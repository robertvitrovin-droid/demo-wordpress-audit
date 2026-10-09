"""findings.json -> professional PDF report (WeasyPrint)."""
import html, json, sys
from pathlib import Path
from weasyprint import HTML

R = Path(__file__).parent
d = json.loads((R / "data/findings.json").read_text(encoding="utf-8"))
F = d["findings"]
SEV = {"high": ("Високий", "#c0392b"), "medium": ("Середній", "#d68910"), "low": ("Низький", "#2e86c1")}
EFFORT = {"high": "1–2 дні", "medium": "2–4 год", "low": "до 1 год"}
e = html.escape
cnt = {k: sum(1 for f in F if f["severity"] == k) for k in SEV}
areas = ["Продуктивність", "Безпека", "Плагіни й оновлення", "SEO", "Доступність"]

def badge(s): n, c = SEV[s]; return f'<span class="b" style="background:{c}">{n}</span>'
def gauge(name, v):
    c = "#1e8449" if v >= 90 else "#d68910" if v >= 50 else "#c0392b"
    return f'<div class="g"><div class="gv" style="border-color:{c};color:{c}">{v}</div><div>{name}</div></div>'

sections = ""
for a in areas:
    items = [f for f in F if f["area"] == a]
    if not items: continue
    sections += f"<h2>{a}</h2>"
    for f in items:
        sections += (f'<div class="f"><div class="ft">{badge(f["severity"])} {e(f["title"])}</div>'
                     f'<div class="ev"><b>Що виявлено:</b> {e(f["evidence"]) or "—"}</div>'
                     f'<div><b>Як виправити:</b> {e(f["fix"])}</div></div>')
    if a == "Продуктивність" and d["metrics"]:
        sections += "<table><tr><th>Метрика (mobile)</th><th>Значення</th></tr>" + "".join(
            f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in d["metrics"].items()) + "</table>"
    if a == "Плагіни й оновлення":
        sections += f"<p>WordPress core: <b>{d.get('core')}</b></p><table><tr><th>Плагін</th><th>Статус</th><th>Версія</th><th>Доступна</th></tr>" + "".join(
            f"<tr><td>{p['name']}</td><td>{p['status']}</td><td>{p['version']}</td><td>{p.get('update_version') or '✓ актуальна'}</td></tr>" for p in d["plugins"]) + "</table>"

plan = "".join(f'<tr><td>{i}</td><td>{badge(f["severity"])}</td><td>{e(f["title"])}</td><td>{f["area"]}</td><td>{EFFORT[f["severity"]]}</td></tr>'
               for i, f in enumerate(F, 1))
lh = d["lighthouse"]
shot = (R / "data/site-home.png").resolve().as_uri()
doc = f"""<html><head><meta charset="utf-8"><style>
@page {{ size:A4; margin:18mm 16mm 20mm; @bottom-right {{ content:"стор. " counter(page); font-size:9pt; color:#889 }}
 @bottom-left {{ content:"ДЕМО-аудит · лабораторний стенд"; font-size:9pt; color:#889 }} }}
@page:first {{ margin:0; @bottom-right{{content:none}} @bottom-left{{content:none}} }}
body {{ font-family: Inter, 'DejaVu Sans', sans-serif; font-size:10.5pt; color:#1b2333; line-height:1.45 }}
.cover {{ height:297mm; background:#0f1626; color:#fff; padding:30mm 22mm; box-sizing:border-box; page-break-after:always; position:relative }}
.demo {{ display:inline-block; background:#e8a33d; color:#111; font-weight:900; letter-spacing:3px; padding:6px 14px; border-radius:6px }}
.cover h1 {{ font-size:34pt; line-height:1.1; margin:18mm 0 6mm }} .cover .sub {{ color:#8fb3d6; font-size:13pt }}
.cover .meta {{ position:absolute; bottom:28mm; left:22mm; color:#9fb0c0; font-size:10.5pt }}
h2 {{ color:#1F2A44; border-bottom:2px solid #e8a33d; padding-bottom:3px; margin-top:9mm }}
.b {{ color:#fff; font-size:8.5pt; padding:2px 7px; border-radius:4px; font-weight:700 }}
.f {{ border:1px solid #dde3ec; border-left:4px solid #1F2A44; border-radius:6px; padding:8px 11px; margin:7px 0; page-break-inside:avoid }}
.ft {{ font-weight:700; margin-bottom:4px }} .ev {{ color:#4a5568; margin-bottom:3px; word-break:break-word }}
table {{ width:100%; border-collapse:collapse; margin:8px 0; font-size:9.5pt }} th {{ background:#1F2A44; color:#fff; text-align:left; padding:5px 7px }}
td {{ border-bottom:1px solid #e5e9f0; padding:5px 7px }}
.gs {{ display:flex; gap:14px; margin:8px 0 }} .g {{ text-align:center; font-size:9pt; flex:1 }}
.gv {{ width:58px; height:58px; line-height:52px; border:4px solid; border-radius:50%; margin:0 auto 4px; font-size:17pt; font-weight:800 }}
.sum {{ display:flex; gap:10px }} .sum div {{ flex:1; border-radius:8px; padding:10px; color:#fff; text-align:center; font-size:10pt }}
.sum b {{ display:block; font-size:22pt }} .note {{ background:#fff7e6; border:1px solid #f0d49a; padding:8px 11px; border-radius:6px; font-size:9.5pt }}
img.shot {{ width:100%; border:1px solid #dde3ec; border-radius:6px }}
</style></head><body>
<div class="cover"><span class="demo">DEMO</span><h1>Технічний аудит<br>WordPress-сайту</h1>
<div class="sub">Продуктивність · Безпека · Плагіни · SEO · Доступність · План виправлень</div>
<div class="meta">Об'єкт: лабораторний стенд «Пекарня «Колосок»» ({e(d['url'])})<br>Дата: {d['date']}<br>
Демо-проєкт для портфоліо. Сайт і бізнес вигадані; проблеми внесено навмисно.</div></div>

<h2>Коротко</h2>
<p>Перевірено головну сторінку й типові службові адреси WordPress лише GET/HEAD-запитами, плюс інвентаризацію ядра, плагінів і тем через WP-CLI та Lighthouse 12 (мобільний профіль). Знайдено <b>{len(F)}</b> проблем.</p>
<div class="sum"><div style="background:#c0392b"><b>{cnt['high']}</b>високий пріоритет</div><div style="background:#d68910"><b>{cnt['medium']}</b>середній</div><div style="background:#2e86c1"><b>{cnt['low']}</b>низький</div></div>
<div class="gs">{gauge('Performance', lh.get('performance', 0))}{gauge('Accessibility', lh.get('accessibility', 0))}{gauge('Best Practices', lh.get('best-practices', 0))}{gauge('SEO', lh.get('seo', 0))}</div>
<p class="note"><b>Головне:</b> PHP-помилки показуються відвідувачам, сайт працює без HTTPS і без заголовків безпеки, плагіни застарілі, а зображення по ~6.8 МБ сповільнюють сторінку. Ці пункти закриваються за 1–2 робочі дні і дають найбільший ефект.</p>
<img class="shot" src="{shot}">
{sections}
<h2>План виправлень за пріоритетом</h2>
<table><tr><th>#</th><th>Пріоритет</th><th>Проблема</th><th>Розділ</th><th>Оцінка часу</th></tr>{plan}</table>
<h2>Методика й обмеження</h2>
<p>Аудит неінвазивний: без сканування вразливостей, підбору паролів і навантажувального тестування. Lighthouse виміряно на локальному стенді; на реальному хостингу значення будуть іншими. Оцінки часу орієнтовні й залежать від хостингу та теми.</p>
</body></html>"""
out = R / "WP_AUDIT_REPORT_DEMO.pdf"
HTML(string=doc, base_url=str(R)).write_pdf(out)
print(out)
