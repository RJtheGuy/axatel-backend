# Axatel Production Deployment Guide

This is the final backend-only deployment guide for this project.

Scope:
- Django + Wagtail backend only
- MySQL/MariaDB database
- gunicorn + nginx + certbot
- no frontend CSS/JS in this backend repo
- only media and admin-required assets are served by the backend

## 1) Production environment file

Create the production environment file on the VPS:

```bash
nano /var/www/axatel/.env
```

Use this exact content:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret-key
APP_DEBUG=False
SITE_URL=https://axatel.it
FRONTEND_URL=https://axatel.it

DATABASE_URL=mysql://axatel:strong_password_here@localhost:3306/axatel
REDIS_URL=redis://localhost:6379/1

CORS_ALLOWED_ORIGINS=https://axatel.it,https://www.axatel.it
CSRF_TRUSTED_ORIGINS=https://axatel.it,https://www.axatel.it

EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-email-password
```

---

## 2) Install Ubuntu system packages

Run this on the VPS:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev \
  default-libmysqlclient-dev build-essential pkg-config \
  nginx redis-server mariadb-server mariadb-client \
  git certbot python3-certbot-nginx
```

---

## 3) Create the MySQL database

```bash
sudo mysql -u root -e "
CREATE DATABASE axatel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'axatel'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON axatel.* TO 'axatel'@'localhost';
FLUSH PRIVILEGES;
"
```

---

## 4) Clone and set up the app

```bash
cd /var/www
git clone <your_repo_url> axatel
cd /var/www/axatel

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Then run the app bootstrap:

```bash
export DJANGO_SETTINGS_MODULE=axatel.settings.production
python manage.py migrate --noinput
python manage.py seed_chatbot_kb
python manage.py createsuperuser
```

If you want to use the repo helper script instead:

```bash
source venv/bin/activate
DJANGO_SETTINGS_MODULE=axatel.settings.production SKIP_STATIC=1 bash ./deploy_vps.sh
```

---

## 5) Configure gunicorn

Create the service file:

```bash
sudo nano /etc/systemd/system/axatel.service
```

Paste this exact content:

```ini
[Unit]
Description=Axatel Django Gunicorn
After=network.target redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/axatel
EnvironmentFile=/var/www/axatel/.env
Environment="DJANGO_SETTINGS_MODULE=axatel.settings.production"
ExecStart=/var/www/axatel/venv/bin/gunicorn \
    --workers 4 \
    --worker-class sync \
    --bind 127.0.0.1:8000 \
    --timeout 60 \
    --access-logfile /var/log/gunicorn/axatel_access.log \
    --error-logfile /var/log/gunicorn/axatel_error.log \
    axatel.wsgi:application
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable axatel
sudo systemctl start axatel
sudo systemctl status axatel --no-pager
```

---

## 6) Configure nginx and HTTPS

Create the nginx config:

```bash
sudo nano /etc/nginx/sites-available/axatel
```

Paste this exact content:

```nginx
# /etc/nginx/sites-available/axatel
server {
    listen 80;
    server_name axatel.it www.axatel.it;
    return 301 https://axatel.it$request_uri;
}

server {
    listen 443 ssl http2;
    server_name www.axatel.it;

    ssl_certificate     /etc/letsencrypt/live/axatel.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/axatel.it/privkey.pem;

    return 301 https://axatel.it$request_uri;
}

server {
    listen 443 ssl http2;
    server_name axatel.it;

    ssl_certificate     /etc/letsencrypt/live/axatel.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/axatel.it/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_session_cache shared:SSL:10m;

    client_max_body_size 20M;

    location /media/ {
        alias /var/www/axatel/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }
}
```

Enable it and obtain HTTPS:

```bash
sudo ln -sf /etc/nginx/sites-available/axatel /etc/nginx/sites-enabled/axatel
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d axatel.it -d www.axatel.it
```

---

## 7) Final cleanup: no leftovers

Do not keep frontend static artifacts in the backend repo. Remove any generated leftovers:

```bash
rm -rf /var/www/axatel/staticfiles
rm -rf /var/www/axatel/static
rm -rf /var/www/axatel/logs
rm -f /var/www/axatel/db.sqlite3
```

Recommended `.gitignore` entries:

```gitignore
.env
.env.*
venv/
.venv/
db.sqlite3
static/
staticfiles/
logs/
media/
```

---

## 8) Strict order of operations: what comes first and why

This is the exact order you must follow.

### First: server bootstrap

Run these first because the app cannot run without the operating system and database layer being ready:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip python3-dev \
  default-libmysqlclient-dev build-essential pkg-config \
  nginx redis-server mariadb-server mariadb-client \
  git certbot python3-certbot-nginx
```

Then create the database:

```bash
sudo mysql -u root -e "
CREATE DATABASE axatel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'axatel'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON axatel.* TO 'axatel'@'localhost';
FLUSH PRIVILEGES;
"
```

Why first:
- the database must exist before Django can migrate
- Python build dependencies must exist before installing `mysqlclient`
- nginx and certbot are needed for the production reverse proxy and HTTPS layer

### Second: app deployment

After the server is ready, deploy the code and install Python dependencies:

```bash
cd /var/www/axatel
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Then create `.env` and run:

```bash
export DJANGO_SETTINGS_MODULE=axatel.settings.production
python manage.py migrate --noinput
python manage.py seed_chatbot_kb
python manage.py createsuperuser
```

Why second:
- Django needs a valid database connection and environment variables
- the app cannot boot until the database and Python dependencies are available

### Third: run the app service

Only after Django is installed and the database is ready do you start gunicorn:

```bash
sudo cp /etc/systemd/system/axatel.service /etc/systemd/system/axatel.service
sudo systemctl daemon-reload
sudo systemctl enable axatel
sudo systemctl start axatel
```

Why third:
- the web process must be started only after migrations and environment setup succeed
- otherwise gunicorn fails because the app is not ready

### Fourth: nginx + HTTPS

Only after the app is running locally on port 8000 do you configure nginx and certbot:

```bash
sudo cp /etc/nginx/sites-available/axatel /etc/nginx/sites-available/axatel
sudo ln -sf /etc/nginx/sites-available/axatel /etc/nginx/sites-enabled/axatel
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d axatel.it -d www.axatel.it
```

Why fourth:
- nginx is the front door to the app
- HTTPS should be enabled only after the backend is already working and listening on localhost

### What should not happen out of order

Do not do this in the wrong order:
- do not start gunicorn before creating the database
- do not run migrations before installing OS dependencies
- do not set nginx before the app is already running on port 8000
- do not deploy frontend static assets into this backend repo

### Final rule

The repository contains two distinct phases:
- `deploy_server_vps.sh`: server bootstrap / OS + DB + base system setup
- `deploy_vps.sh`: app deployment / Python + Django migrations + app startup

Run the server bootstrap first, then the app deployment second, then gunicorn, then nginx/HTTPS.

That order is the reason the project is reliable and does not fail in production.


This backend must host only:
- admin assets required by Django/Wagtail
- uploaded media files
- API endpoints
- CMS content and management routes

This backend must not host:
- frontend CSS
- frontend JavaScript
- frontend build bundles
- static site rendering assets

This is the final production-ready deployment setup for your project.
