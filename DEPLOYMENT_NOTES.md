# Deployment Notes

This project is a Django + Wagtail backend intended for a VPS deployment without Docker.

## Recommended production stack
- Ubuntu 22.04 or 24.04
- MariaDB or MySQL
- Python venv
- gunicorn
- nginx
- certbot
- Redis optional for caching

## Important rule
Do not keep SQLite in production. For a live VPS, use MySQL/MariaDB via `DATABASE_URL`.

## Required production setup
1. Install OS packages:
   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-pip nginx redis-server mariadb-server mariadb-client python3-dev default-libmysqlclient-dev build-essential pkg-config git certbot python3-certbot-nginx
   ```
2. Create the database:
   ```sql
   CREATE DATABASE axatel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'axatel'@'localhost' IDENTIFIED BY 'strong_password_here';
   GRANT ALL PRIVILEGES ON axatel.* TO 'axatel'@'localhost';
   FLUSH PRIVILEGES;
   ```
3. Set production `.env`:
   ```dotenv
   DJANGO_SECRET_KEY=replace-with-a-long-random-secret
   APP_DEBUG=False
   SITE_URL=https://axatel.it
   FRONTEND_URL=https://axatel.it
   DATABASE_URL=mysql://axatel:strong_password_here@localhost:3306/axatel
   REDIS_URL=redis://localhost:6379/1
   CORS_ALLOWED_ORIGINS=https://axatel.it,https://www.axatel.it
   CSRF_TRUSTED_ORIGINS=https://axatel.it,https://www.axatel.it
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-key
   ```
4. Install app dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
5. Run Django setup:
   ```bash
   export DJANGO_SETTINGS_MODULE=axatel.settings.production
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py createsuperuser
   ```
6. Start gunicorn:
   ```bash
   sudo cp deploy/gunicorn.service /etc/systemd/system/axatel.service
   sudo systemctl daemon-reload
   sudo systemctl enable axatel
   sudo systemctl start axatel
   ```
7. Configure nginx and HTTPS:
   ```bash
   sudo cp deploy/nginx.conf /etc/nginx/sites-available/axatel
   sudo ln -sf /etc/nginx/sites-available/axatel /etc/nginx/sites-enabled/axatel
   sudo nginx -t
   sudo systemctl reload nginx
   sudo certbot --nginx -d axatel.it -d www.axatel.it
   ```

## What not to keep in the backend project
These are not needed in this backend repo and should be removed or kept out of the repo if they are not part of the server-side app:

- frontend CSS/JS source and generated static assets
  - they belong to a separate frontend app
  - keeping them here makes the backend project harder to maintain and deploy
- SQLite as the production default
  - it is suitable only for local development
  - production should use MariaDB/MySQL
- Docker as the required runtime for a VPS
  - this repo is designed for a plain Linux VPS deployment
  - Docker is optional, not required
- generated runtime folders tracked in Git
  - `staticfiles/`, `logs/`, `db.sqlite3`, `.env`, `.venv` or `venv/`

## Safe refactor guidance
Keep the following modules as core backend logic:
- `axatel/`
- `core/`
- `home/`
- `blog/`
- `services/`
- `casi/`
- `chatbot/`
- `monitoring/`
- `seo/`
- `solutions/`

Only remove or isolate things that are clearly frontend-only, runtime-generated, or deployment-specific. Do not remove the Wagtail settings, migrations, or the app model structure unless you intentionally rewrite the feature architecture.

## Verified status
The Django application itself was validated with:
```bash
source venv/bin/activate
python manage.py check
python manage.py migrate --noinput
```
These completed successfully after the startup fixes.


cd /home/rashid/axatel-backend
DOMAIN_NAME=staging.example.com ./deploy_production.sh