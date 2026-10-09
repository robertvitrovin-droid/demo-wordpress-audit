# Технічний аудит WordPress-сайту (демо)

> **Демо-проєкт для портфоліо.** Аудит проведено на **власному локальному стенді**: WordPress з вигаданим сайтом «Пекарня «Колосок»», куди навмисно внесено типові проблеми. Чужі сайти не скануються.

## Що всередині
- `WP_AUDIT_REPORT_DEMO.pdf` — готовий звіт (7 стор.): резюме, Lighthouse, продуктивність, безпека, плагіни й оновлення, SEO, доступність, план виправлень за пріоритетом.
- `audit.py` — неінвазивний аудит: лише GET/HEAD-запити з паузою, + WP-CLI для інвентаризації ядра/плагінів/тем, + Lighthouse JSON.
- `report.py` — генерує PDF з `data/findings.json` (WeasyPrint).
- `data/` — `findings.json`, звіт Lighthouse (`lighthouse-wp.report.html/json`), скриншот головної.
- `setup_lab.sh` — як піднято стенд (PHP built-in server + SQLite, без Docker).

## Навмисні проблеми стенду
Застарілі Contact Form 7 5.3.1 і Classic Editor 1.5 та тема Twenty Twenty-One 1.0, `WP_DEBUG_DISPLAY` увімкнено, адміністратор `admin`,
зображення 4000×3000 по ~6.8 МБ без alt, три H1, немає meta description, світло-сірий текст з низьким контрастом, посилання «тут», без HTTPS і заголовків безпеки.

## Запуск
```bash
bash setup_lab.sh                       # потрібні php-cli, php-sqlite3, wp-cli
lighthouse http://127.0.0.1:8088/ --output=json --output-path=data/lighthouse-wp.report.json
python audit.py --url http://127.0.0.1:8088 --wp-path lab/wordpress --lighthouse data/lighthouse-wp.report.json
python report.py
```
Запускайте `audit.py` лише для сайтів, якими володієте або маєте письмовий дозвіл на аудит.
