"""Read-only technical audit of a WordPress site (HTTP checks + optional WP-CLI + Lighthouse JSON).
Usage: python audit.py --url http://127.0.0.1:8088 [--wp-path lab/wordpress] [--lighthouse data/lighthouse-wp.report.json]
Only GET/HEAD requests, 0.3s apart. Run it only against sites you own or are authorised to audit."""
import argparse, json, re, subprocess, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

def jload(text):
    """Parse JSON even if PHP notices were printed before it."""
    dec = json.JSONDecoder()
    for m in re.finditer(r"[\[{]", text):
        try:
            obj, end = dec.raw_decode(text, m.start())
            if isinstance(obj, list): return obj
        except ValueError:
            continue
    return []


SEC_HEADERS = ["Strict-Transport-Security", "Content-Security-Policy", "X-Content-Type-Options",
               "X-Frame-Options", "Referrer-Policy", "Permissions-Policy"]


class Audit:
    def __init__(self, url):
        self.url = url.rstrip("/"); self.s = requests.Session(); self.s.headers["User-Agent"] = "wp-audit-demo/1.0"
        self.f = []  # findings

    def get(self, path, **kw):
        time.sleep(0.3)
        return self.s.get(self.url + path, timeout=15, allow_redirects=kw.pop("redirects", True), **kw)

    def add(self, area, sev, title, evidence, fix):
        self.f.append(dict(area=area, severity=sev, title=title, evidence=evidence, fix=fix))

    def run(self, wp_path=None, lh=None):
        home = self.get("/"); soup = BeautifulSoup(home.text, "lxml"); h = home.headers
        missing = [x for x in SEC_HEADERS if x not in h]
        if missing:
            self.add("Безпека", "high" if "Content-Security-Policy" in missing else "medium",
                     "Відсутні заголовки безпеки", ", ".join(missing),
                     "Додати заголовки на рівні веб-сервера (nginx/Apache) або плагіном; почати з X-Content-Type-Options, Referrer-Policy, X-Frame-Options, HSTS після переходу на HTTPS.")
        if "X-Powered-By" in h:
            self.add("Безпека", "low", "Розкривається версія PHP", f"X-Powered-By: {h['X-Powered-By']}", "expose_php = Off у php.ini.")
        if not self.url.startswith("https"):
            self.add("Безпека", "high", "Сайт працює без HTTPS", self.url, "Встановити TLS-сертифікат (Let's Encrypt), 301-редірект на https, увімкнути HSTS.")
        gen = soup.find("meta", attrs={"name": "generator"})
        if gen:
            self.add("Безпека", "low", "Версія WordPress у коді сторінки", gen.get("content"), "Прибрати meta generator (remove_action('wp_head','wp_generator')) та ?ver= у статиці.")
        if "PHP Deprecated" in home.text or re.search(r"<b>(Deprecated|Notice|Warning)</b>", home.text) or "Deprecated:" in home.text:
            self.add("Безпека", "high", "PHP-помилки виводяться відвідувачам", "На головній видно Deprecated/Notice з повними шляхами до файлів", "WP_DEBUG_DISPLAY=false, логувати у файл поза webroot; оновити плагіни, що генерують помилки.")
        r = self.get("/readme.html")
        if r.status_code == 200:
            self.add("Безпека", "low", "Доступний readme.html", "/readme.html → 200", "Видалити або заборонити доступ до readme.html, license.txt.")
        r = self.get("/xmlrpc.php")
        if r.status_code in (200, 405) and "XML-RPC" in r.text:
            self.add("Безпека", "medium", "Увімкнено XML-RPC", f"/xmlrpc.php → {r.status_code}", "Вимкнути XML-RPC, якщо не використовуються Jetpack/мобільний застосунок (brute-force через system.multicall).")
        r = self.get("/wp-json/wp/v2/users")
        if r.ok and r.headers.get("content-type", "").startswith("application/json"):
            names = [u.get("slug") for u in jload(r.text)]
            self.add("Безпека", "medium", "Перелік користувачів через REST API", f"/wp-json/wp/v2/users → {names}", "Обмежити endpoint users для неавторизованих; не використовувати логін 'admin'.")
        r = self.get("/?author=1", redirects=False)
        if r.status_code in (301, 302) and "/author/" in r.headers.get("Location", ""):
            self.add("Безпека", "low", "Енумерація авторів через ?author=", r.headers["Location"], "Блокувати ?author=N редіректом/правилом сервера.")
        r = self.get("/wp-login.php")
        if r.ok:
            self.add("Безпека", "medium", "Сторінка входу без захисту від перебору", "/wp-login.php доступна без обмежень/2FA", "Ліміт спроб входу, 2FA для адміністраторів, за можливості — обмеження за IP.")
        # SEO
        desc = soup.find("meta", attrs={"name": "description"})
        if not desc:
            self.add("SEO", "medium", "Немає meta description", "головна сторінка", "Задати унікальні description для ключових сторінок (Yoast/Rank Math або вручну).")
        h1 = soup.find_all("h1")
        if len(h1) != 1:
            self.add("SEO", "low", f"Кількість H1 на головній: {len(h1)}", "; ".join(x.get_text(strip=True)[:40] for x in h1), "Один H1 на сторінку, далі логічна ієрархія H2–H3.")
        if not soup.find("link", rel="canonical"):
            self.add("SEO", "low", "Немає canonical на головній", "", "Додати rel=canonical.")
        for p in ("/sitemap.xml", "/wp-sitemap.xml"):
            if self.get(p).ok: break
        else:
            self.add("SEO", "medium", "Не знайдено sitemap", "", "Увімкнути XML sitemap і додати в Search Console.")
        if not soup.find("meta", property="og:title"):
            self.add("SEO", "low", "Немає Open Graph-розмітки", "", "Додати og:title/og:description/og:image для коректних прев'ю в соцмережах.")
        # images / a11y
        imgs = soup.select("main img, .entry-content img, img")
        noalt = [i.get("src", "")[-30:] for i in imgs if not i.get("alt")]
        if noalt:
            self.add("Доступність", "medium", f"Зображення без alt: {len(noalt)}", ", ".join(noalt[:4]), "Заповнити alt для змістовних зображень, alt='' для декоративних.")
        big = []
        for i in imgs[:10]:
            src = i.get("src", "")
            if not src: continue
            src = src if src.startswith("http") else self.url + src
            try:
                hr = self.s.head(src, timeout=10); size = int(hr.headers.get("Content-Length", 0))
                if size > 300_000: big.append(f"{src.rsplit('/',1)[-1]} ({size//1024} КБ)")
            except Exception: pass
        if big:
            self.add("Продуктивність", "high", "Важкі неоптимізовані зображення", ", ".join(big), "Стиснути та перевести у WebP/AVIF, задати розміри, srcset і loading='lazy'; ціль < 200 КБ на зображення.")
        vague = [a.get_text(strip=True) for a in soup.find_all("a") if a.get_text(strip=True).lower() in ("тут", "here", "детальніше", "click")]
        if vague:
            self.add("Доступність", "low", "Неінформативні тексти посилань", ", ".join(vague), "Писати зміст посилання: «Замовити торт», а не «тут».")
        if lh:
            d = json.loads(Path(lh).read_text())
            self.lh = {k: round(v["score"] * 100) for k, v in d["categories"].items()}
            a = d["audits"]
            self.lh_metrics = {k: a[k]["displayValue"] for k in ("first-contentful-paint", "largest-contentful-paint", "total-blocking-time", "cumulative-layout-shift", "speed-index") if k in a}
            if a.get("color-contrast", {}).get("score") == 0:
                self.add("Доступність", "medium", "Недостатній контраст тексту", "Lighthouse: color-contrast", "Контраст тексту не менше 4.5:1 (WCAG AA).")
            if self.lh.get("performance", 100) < 90:
                self.add("Продуктивність", "high", f"Lighthouse Performance {self.lh['performance']}/100 (mobile)",
                         ", ".join(f"{k}: {v}" for k, v in self.lh_metrics.items()), "Оптимізація зображень, кешування сторінок, відкладене завантаження JS/CSS, CDN.")
        else:
            self.lh, self.lh_metrics = {}, {}
        self.plugins = []
        if wp_path:
            def wp(*args):
                return subprocess.run(["wp", f"--path={wp_path}", *args, "--skip-plugins=" if False else "--quiet"], capture_output=True, text=True).stdout
            core = subprocess.run(["wp", f"--path={wp_path}", "core", "version"], capture_output=True, text=True).stdout.strip()
            self.core = core
            pl = jload(subprocess.run(["wp", f"--path={wp_path}", "plugin", "list", "--fields=name,status,version,update_version", "--format=json"], capture_output=True, text=True).stdout)
            self.plugins = [p for p in pl if p["name"] != "db.php"]
            old = [p for p in self.plugins if p.get("update_version")]
            if old:
                self.add("Плагіни й оновлення", "high", f"Застарілі плагіни: {len(old)}",
                         ", ".join(f"{p['name']} {p['version']} → {p['update_version']}" for p in old),
                         "Зробити резервну копію, оновити на staging, перевірити форми й редактор, потім на production. Увімкнути автооновлення безпеки.")
            inactive = [p["name"] for p in self.plugins if p["status"] == "inactive" and p["name"] != "sqlite-database-integration"]
            if inactive:
                self.add("Плагіни й оновлення", "low", f"Неактивні плагіни: {len(inactive)}", ", ".join(inactive), "Видалити непотрібні плагіни — вони все одно можуть містити вразливості.")
            th = jload(subprocess.run(["wp", f"--path={wp_path}", "theme", "list", "--fields=name,status,version,update_version", "--format=json"], capture_output=True, text=True).stdout)
            self.themes = th
            oldt = [t for t in th if t.get("update_version")]
            if oldt:
                self.add("Плагіни й оновлення", "medium", "Застарілі теми", ", ".join(f"{t['name']} {t['version']} → {t['update_version']}" for t in oldt), "Оновити активну тему (через дочірню тему, щоб не втратити правки), видалити зайві.")
            users = subprocess.run(["wp", f"--path={wp_path}", "user", "list", "--role=administrator", "--field=user_login"], capture_output=True, text=True).stdout.split()
            if "admin" in users:
                self.add("Безпека", "medium", "Адміністратор з логіном «admin»", "user_login=admin", "Створити нового адміністратора з унікальним логіном, перенести контент, видалити «admin».")
        order = {"high": 0, "medium": 1, "low": 2}
        self.f.sort(key=lambda x: order[x["severity"]])
        return self


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True); ap.add_argument("--wp-path"); ap.add_argument("--lighthouse")
    ap.add_argument("--out", default="data/findings.json")
    a = ap.parse_args()
    au = Audit(a.url).run(a.wp_path, a.lighthouse)
    res = dict(url=a.url, date=time.strftime("%Y-%m-%d"), lighthouse=au.lh, metrics=au.lh_metrics,
               core=getattr(au, "core", None), plugins=au.plugins, themes=getattr(au, "themes", []), findings=au.f)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in au.f: print(f"[{x['severity']:6}] {x['area']}: {x['title']}")
