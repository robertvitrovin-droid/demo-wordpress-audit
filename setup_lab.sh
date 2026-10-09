#!/usr/bin/env bash
# Local WordPress lab with deliberate issues (PHP built-in server + SQLite). For demo only.
set -euo pipefail
mkdir -p lab && cd lab
curl -sSLo wp.tgz https://wordpress.org/latest.tar.gz && tar xzf wp.tgz
curl -sSLo sq.zip https://downloads.wordpress.org/plugin/sqlite-database-integration.zip
(cd wordpress/wp-content/plugins && unzip -oq ../../../sq.zip)
cd wordpress
cp wp-content/plugins/sqlite-database-integration/db.copy wp-content/db.php
sed -i "s#{SQLITE_IMPLEMENTATION_FOLDER_PATH}#$PWD/wp-content/plugins/sqlite-database-integration#; s#{SQLITE_PLUGIN}#sqlite-database-integration/load.php#" wp-content/db.php
cp wp-config-sample.php wp-config.php
sed -i "s/define( 'WP_DEBUG', false );/define( 'WP_DEBUG', true );\ndefine( 'WP_DEBUG_DISPLAY', true );/" wp-config.php
nohup php -S 127.0.0.1:8088 >/tmp/wp-server.log 2>&1 &
sleep 1
wp core install --url=http://127.0.0.1:8088 --title="Пекарня «Колосок» (лабораторний стенд)" --admin_user=admin --admin_password=admin123 --admin_email=admin@example.test --skip-email
for p in contact-form-7.5.3.1 classic-editor.1.5; do curl -sSfLo /tmp/$p.zip https://downloads.wordpress.org/plugin/$p.zip; wp plugin install /tmp/$p.zip --activate; done
curl -sSfLo /tmp/tt1.zip https://downloads.wordpress.org/theme/twentytwentyone.1.0.zip && wp theme install /tmp/tt1.zip --activate
python3 - <<'PY'
from PIL import Image
for i in range(3):
    im = Image.blend(Image.effect_noise((2000,1500), 90).convert("RGB").resize((4000,3000)), Image.new("RGB",(4000,3000),(200,150,90)), .5)
    im.save(f"/tmp/hero{i}.jpg", quality=95)
PY
for i in 0 1 2; do wp media import /tmp/hero$i.jpg >/dev/null; done
U="/wp-content/uploads/$(date +%Y/%m)"
P=$(wp post create --post_type=page --post_status=publish --post_title="Головна" --porcelain --post_content="<h1>Ласкаво просимо</h1><h1>Свіжий хліб щодня</h1><img src=\"$U/hero0.jpg\"><img src=\"$U/hero1.jpg\"><p style=\"color:#bbb\">Замовлення за телефоном.</p><a href=\"#\">тут</a>")
wp post create --post_status=publish --post_title="Новини" --post_content="<h4>Новинка</h4><img src=\"$U/hero2.jpg\"> Текст."
wp option update show_on_front page && wp option update page_on_front "$P"
