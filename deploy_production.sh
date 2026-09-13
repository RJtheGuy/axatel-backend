#!/usr/bin/env bash
set -euo pipefail

# Full Axatel deployment for a fresh Ubuntu VPS.
# Required inputs are prompted at runtime; secrets are never stored in Git.

APP_ROOT="/var/www/axatel"
FRONTEND_ROOT="/var/www/axatel-frontend"
DOMAIN_NAME="${DOMAIN_NAME:-}"
BACKEND_REPO_URL="${BACKEND_REPO_URL:-}"
FRONTEND_REPO_URL="${FRONTEND_REPO_URL:-}"
DB_NAME="${DB_NAME:-axatel_cms}"
DB_USER="${DB_USER:-axatel_app}"

required() {
    local variable="$1"
    local value="${!variable:-}"
    if [[ -z "$value" ]]; then
        read -r -p "$variable: " value
        [[ -n "$value" ]] || { echo "$variable is required" >&2; exit 1; }
        printf -v "$variable" '%s' "$value"
    fi
}

required DOMAIN_NAME
required BACKEND_REPO_URL
required FRONTEND_REPO_URL

if [[ "$DOMAIN_NAME" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
    PUBLIC_SCHEME="http"
    SECURE_SSL_REDIRECT="False"
else
    PUBLIC_SCHEME="https"
    SECURE_SSL_REDIRECT="True"
fi

read -r -s -p "MariaDB password for ${DB_USER}: " DB_PASSWORD
printf '\n'
[[ -n "$DB_PASSWORD" ]] || { echo "Database password is required" >&2; exit 1; }
read -r -s -p "SMTP password (press Enter if not configured yet): " SMTP_PASSWORD
printf '\n'
read -r -p "SMTP host [smtp.sendgrid.net]: " SMTP_HOST
SMTP_HOST="${SMTP_HOST:-smtp.sendgrid.net}"
read -r -p "SMTP username [apikey]: " SMTP_USER
SMTP_USER="${SMTP_USER:-apikey}"

sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt install -y \
    python3-venv python3-pip python3-dev default-libmysqlclient-dev \
    build-essential pkg-config nginx redis-server mariadb-server mariadb-client \
    git certbot python3-certbot-nginx curl ca-certificates openssl
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo DEBIAN_FRONTEND=noninteractive apt install -y nodejs
sudo systemctl enable --now mariadb redis-server

sudo mysql -u root <<SQL
CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL

# Keep Django's connection collation consistent with the database defaults.
sudo mysql -u root -e "ALTER DATABASE \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"

# A rerun may have tables from a migration that stopped part-way through.
# ALTER DATABASE changes defaults only; convert existing tables as well.
sudo mysql -u root -N -B -e "
SELECT CONCAT(
    'ALTER TABLE ', TABLE_NAME,
    ' CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;'
)
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = '${DB_NAME}'
    AND TABLE_TYPE = 'BASE TABLE';
" | sudo mysql -u root "$DB_NAME"

sudo mkdir -p /var/www
if [[ ! -d "$APP_ROOT/.git" ]]; then sudo git clone "$BACKEND_REPO_URL" "$APP_ROOT"; fi
if [[ ! -d "$FRONTEND_ROOT/.git" ]]; then sudo git clone "$FRONTEND_REPO_URL" "$FRONTEND_ROOT"; fi

sudo python3 -m venv "$APP_ROOT/venv"
sudo "$APP_ROOT/venv/bin/pip" install --upgrade pip
sudo "$APP_ROOT/venv/bin/pip" install -r "$APP_ROOT/requirements.txt"

if [[ ! -f "$APP_ROOT/.env" ]]; then
    DJANGO_SECRET_KEY="$(openssl rand -hex 48)"
    sudo tee "$APP_ROOT/.env" >/dev/null <<EOF
DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
APP_DEBUG=False
SITE_URL=$PUBLIC_SCHEME://$DOMAIN_NAME
FRONTEND_URL=$PUBLIC_SCHEME://$DOMAIN_NAME
ALLOWED_HOSTS=$DOMAIN_NAME,www.$DOMAIN_NAME
SECURE_SSL_REDIRECT=$SECURE_SSL_REDIRECT
DATABASE_URL=mysql://$DB_USER:$DB_PASSWORD@127.0.0.1:3306/$DB_NAME
REDIS_URL=redis://127.0.0.1:6379/1
CORS_ALLOWED_ORIGINS=$PUBLIC_SCHEME://$DOMAIN_NAME,$PUBLIC_SCHEME://www.$DOMAIN_NAME
CSRF_TRUSTED_ORIGINS=$PUBLIC_SCHEME://$DOMAIN_NAME,$PUBLIC_SCHEME://www.$DOMAIN_NAME
EMAIL_HOST=$SMTP_HOST
EMAIL_HOST_USER=$SMTP_USER
EMAIL_HOST_PASSWORD=$SMTP_PASSWORD
EOF
    sudo chown www-data:www-data "$APP_ROOT/.env"
    sudo chmod 600 "$APP_ROOT/.env"
else
    echo "Preserving existing $APP_ROOT/.env"
fi
sudo mkdir -p "$APP_ROOT/media" "$APP_ROOT/logs" "$APP_ROOT/staticfiles"
sudo chown -R www-data:www-data "$APP_ROOT/media" "$APP_ROOT/logs" "$APP_ROOT/staticfiles"
sudo -u www-data env DJANGO_SETTINGS_MODULE=axatel.settings.production "$APP_ROOT/venv/bin/python" "$APP_ROOT/manage.py" migrate --noinput
sudo -u www-data env DJANGO_SETTINGS_MODULE=axatel.settings.production "$APP_ROOT/venv/bin/python" "$APP_ROOT/manage.py" collectstatic --noinput
sudo -u www-data env DJANGO_SETTINGS_MODULE=axatel.settings.production "$APP_ROOT/venv/bin/python" "$APP_ROOT/manage.py" check

sudo tee /etc/systemd/system/axatel.service >/dev/null <<EOF
[Unit]
Description=Axatel Django Gunicorn
After=network.target mariadb.service redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_ROOT
EnvironmentFile=$APP_ROOT/.env
Environment=DJANGO_SETTINGS_MODULE=axatel.settings.production
ExecStart=$APP_ROOT/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 --timeout 60 axatel.wsgi:application
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo chown -R www-data:www-data "$FRONTEND_ROOT"
sudo -u www-data bash -c "cd '$FRONTEND_ROOT' && npm ci && NUXT_PUBLIC_API_BASE=$PUBLIC_SCHEME://$DOMAIN_NAME/api/v2 NUXT_API_INTERNAL_BASE=http://127.0.0.1:8000/api/v2 npm run build"

sudo tee /etc/systemd/system/axatel-frontend.service >/dev/null <<EOF
[Unit]
Description=Axatel Nuxt frontend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$FRONTEND_ROOT
Environment=NODE_ENV=production
Environment=HOST=127.0.0.1
Environment=PORT=3000
Environment=NUXT_PUBLIC_API_BASE=$PUBLIC_SCHEME://$DOMAIN_NAME/api/v2
Environment=NUXT_API_INTERNAL_BASE=http://127.0.0.1:8000/api/v2
ExecStart=/usr/bin/node $FRONTEND_ROOT/.output/server/index.mjs
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now axatel axatel-frontend

sudo tee /etc/nginx/sites-available/axatel >/dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location /api/ { proxy_pass http://127.0.0.1:8000; include proxy_params; }
    location /cms/ { proxy_pass http://127.0.0.1:8000; include proxy_params; }
    location /media/ { alias $APP_ROOT/media/; expires 30d; add_header Cache-Control "public"; }
    location /static/ { alias $APP_ROOT/staticfiles/; expires 1y; add_header Cache-Control "public, immutable"; }
    location / { proxy_pass http://127.0.0.1:3000; include proxy_params; }
}
EOF
sudo ln -sfn /etc/nginx/sites-available/axatel /etc/nginx/sites-enabled/axatel
sudo nginx -t
sudo systemctl reload nginx

read -r -p "Email address for the Let's Encrypt certificate: " CERTBOT_EMAIL
[[ -n "$CERTBOT_EMAIL" ]] || { echo "Certificate email is required" >&2; exit 1; }
if [[ "$PUBLIC_SCHEME" == "https" ]]; then
    read -r -p "Email address for the Let's Encrypt certificate: " CERTBOT_EMAIL
    [[ -n "$CERTBOT_EMAIL" ]] || { echo "Certificate email is required" >&2; exit 1; }
    sudo certbot --nginx --non-interactive --agree-tos --redirect \
        -m "$CERTBOT_EMAIL" -d "$DOMAIN_NAME" -d "www.$DOMAIN_NAME"
else
    echo "No domain detected: skipping Certbot. The site is available over HTTP at http://$DOMAIN_NAME"
fi
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl --no-pager --full status axatel axatel-frontend
printf 'Deployment complete: https://%s\n' "$DOMAIN_NAME"
