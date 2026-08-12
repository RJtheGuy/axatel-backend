# Axatel Site — Django 5 + Wagtail 6

Full replacement for the WordPress site.
Zero SEO regression. StreamField block editor for the marketing team.

---

## What's inside

```
axatel_site/
├── axatel/             ← Django project config
│   └── settings/
│       ├── base.py     ← shared settings
│       ├── dev.py      ← SQLite, no Redis needed, DEBUG=True
│       └── production.py ← HTTPS, HSTS, Redis, SMTP
├── core/
│   └── blocks.py       ← ALL StreamField blocks (add new ones here)
├── home/
│   ├── models.py       ← HomePage + FlexPage
│   └── management/commands/import_wordpress.py
├── services/
│   └── models.py       ← ServicesIndexPage + ServicePage
├── blog/
│   └── models.py       ← BlogIndexPage + BlogPost
├── seo/
│   └── views.py        ← robots.txt
├── templates/
│   ├── base.html       ← site shell (nav, footer, all SEO tags)
│   └── blocks/         ← one HTML file per block type
├── static/
│   ├── css/main.css    ← complete stylesheet, no framework
│   └── js/main.js      ← mobile nav only, ~20 lines
└── deploy/
    ├── nginx.conf      ← production nginx config
    └── gunicorn.service ← systemd unit
```

---

## 5-minute local start

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment (SQLite is used in dev automatically)
cp .env.example .env
# Only DJANGO_SECRET_KEY needs changing for local dev

# 4. Run database migrations (creates db.sqlite3)
python manage.py migrate

# 5. Create a CMS superuser (for the marketing agent)
python manage.py createsuperuser

# 6. Start the dev server
python manage.py runserver
```

Then open:
- **Site:**      http://0.0.0.0:port/
- **CMS admin:** http://0.0.0.0:port/cms/

---

## Available StreamField blocks

Marketing agents see these in the "+" block picker inside any page editor:

| Block | What it does |
|---|---|
| **Paragrafo** | Full rich text — headings, bold, lists, links |
| **Titolo sezione** | Standalone H2/H3 with optional subtitle |
| **Immagine** | Image from media library with caption + alignment |
| **Due colonne** | Side-by-side layout, 3 ratio options |
| **Griglia icone** | Emoji + title + description grid, 2/3/4 columns |
| **Box evidenziato** | Callout box: info, success, warning, tip |
| **Pulsante CTA** | Standalone CTA button, 3 styles, 3 alignments |
| **Citazione** | Pull-quote with author and role |
| **Video** | YouTube/Vimeo by URL, responsive 16:9 |
| **Spazio verticale** | Vertical whitespace, 4 sizes |

**Adding a new block type:**
1. Add the class to `core/blocks.py`
2. Add it to the `BODY_BLOCKS` list at the bottom of the same file
3. Create `templates/blocks/<name>.html`
4. Add CSS in `static/css/main.css` (search "StreamField blocks")
5. `python manage.py makemigrations && python manage.py migrate`

---

## Import from WordPress

```bash
# Step 1: Export from WordPress
# WP Admin → Tools → Export → All content → Download Export File

# Step 2: Dry run (nothing written to DB)
python manage.py import_wordpress wordpress.xml --dry-run

# Step 3: Real import
python manage.py import_wordpress wordpress.xml
```

What gets imported:
- WordPress **posts** → BlogPost (under BlogIndexPage)
- WordPress **pages** → FlexPage (under HomePage)
- Slugs are preserved exactly → your URLs stay the same

After import, check each page in the CMS and fill in the SEO fields
(Promote tab: SEO title, meta description, OG image).

---

## SEO checklist post-launch

- [ ] Submit `/sitemap.xml` to Google Search Console
- [ ] Verify `/robots.txt` looks correct
- [ ] For any changed URL: Settings → Redirects → add 301
- [ ] Per page: fill in SEO title + meta description in the Promote tab
- [ ] Per page: upload an OG image in the Promote tab
- [ ] For service pages: fill in Schema.org serviceType field

---

## Database options

The default is PostgreSQL. Change four lines in `axatel/settings/base.py`:

**MySQL / MariaDB (in-house server):**
```python
"ENGINE": "django.db.backends.mysql",
"HOST":   "0.0.0.0",  # your server IP
"PORT":   "****",
```
Add `mysqlclient>=2.2` to requirements.txt.

**Microsoft SQL Server:**
```python
"ENGINE": "mssql",
"HOST":   "0.0.0.0\\SQLEXPRESS",
"PORT":   "***",
```
Add `mssql-django>=1.4` to requirements.txt.

After changing the engine, re-run `python manage.py migrate`.

---

## Production deployment

```bash
# On the server (Ubuntu 22/24):

# 1. System packages
sudo apt install python3-venv nginx redis-server postgresql certbot python3-certbot-nginx

# 2. Create database (PostgreSQL example)
sudo -u postgres createdb axatel
sudo -u postgres createuser axatel -P

# 3. Clone repo
sudo mkdir -p /var/www/axatel
sudo git clone <your-repo> /var/www/axatel

# 4. Virtualenv + dependencies
cd /var/www/axatel
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# 5. Fill in .env
cp .env.example .env && nano .env

# 6. Collect static files
DJANGO_SETTINGS_MODULE=axatel.settings.production venv/bin/python manage.py collectstatic --noinput

# 7. Run migrations
DJANGO_SETTINGS_MODULE=axatel.settings.production venv/bin/python manage.py migrate

# 8. Create superuser on server
DJANGO_SETTINGS_MODULE=axatel.settings.production venv/bin/python manage.py createsuperuser

# 9. SSL certificate
sudo certbot --nginx -d axatel.it -d www.axatel.it

# 10. nginx
sudo cp deploy/nginx.conf /etc/nginx/sites-available/axatel
sudo ln -s /etc/nginx/sites-available/axatel /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 11. gunicorn service
sudo mkdir -p /var/log/gunicorn
sudo cp deploy/gunicorn.service /etc/systemd/system/axatel.service
sudo systemctl daemon-reload
sudo systemctl enable axatel
sudo systemctl start axatel

# Check it's running:
sudo systemctl status axatel
sudo journalctl -u axatel -f
```
