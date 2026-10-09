# Технічний аудит WordPress-сайту з PDF-звітом (демо)

**Демо-проєкт для портфоліо**, не робота для клієнта. Аудит виконано на власному локальному стенді з вигаданим сайтом пекарні, куди навмисно внесено типові проблеми.

**Задача.** Пояснити власнику сайту, чому сайт повільний, чи він у безпеці і що виправити насамперед.

**Що зроблено.**
- Неінвазивна перевірка: швидкість (Lighthouse), заголовки безпеки, HTTPS, виведення помилок, XML-RPC, перелік користувачів, службові файли.
- Інвентаризація ядра, плагінів і тем через WP-CLI; SEO-база й доступність (alt, контраст, тексти посилань).
- PDF-звіт: резюме, докази й виправлення по кожній проблемі, план робіт за пріоритетом з оцінкою часу.

**Результат.** 7-сторінковий звіт: 22 проблеми (6 високого, 8 середнього, 8 низького пріоритету) ([findings.json](https://github.com/robertvitrovin-droid/demo-wordpress-audit/blob/main/data/findings.json)). Lighthouse стенду 73 / 90 / 89 / 75 ([HTML-звіт](https://github.com/robertvitrovin-droid/demo-wordpress-audit/blob/main/data/lighthouse-wp.report.html); Lighthouse 12.8.2, mobile, локальний стенд, 2026-10-09). Скрипти: [audit.py](https://github.com/robertvitrovin-droid/demo-wordpress-audit/blob/main/audit.py), [report.py](https://github.com/robertvitrovin-droid/demo-wordpress-audit/blob/main/report.py).

**Посилання.** [Приклад PDF-звіту](https://github.com/robertvitrovin-droid/demo-wordpress-audit/blob/main/WP_AUDIT_REPORT_DEMO.pdf)

Стек: Python, WP-CLI, Lighthouse, WeasyPrint · **Ціна від 1 500 грн** за аудит, виправлення окремо, від 1 дня
