import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-before-production")
DEBUG = os.environ.get("APP_DEBUG", "False").lower() in ("true", "1", "t")
ALLOWED_HOSTS = [
    "axatel.it",
    "www.axatel.it",
    "localhost",
    "127.0.0.1",
    "web",
]

INSTALLED_APPS = [
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",     
    "wagtail.contrib.sitemaps",      
    "wagtail.contrib.routable_page",
    "wagtail.embeds",                
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "wagtail.contrib.settings",
    "wagtail.contrib.simple_translation",   # "Traduci" action on pages
    "wagtail.locales",                      # Impostazioni → Lingue
    "wagtail.api.v2",
    "rest_framework",
    "wagtail_headless_preview",
    "corsheaders",
    "modelcluster",
    "taggit",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "wagtailseo",                    # site-wide SEO panel + Twitter Cards
    "core",
    "home",
    "services",
    "blog",
    "seo",
    "chatbot",
    "translation",                   # self-hosted machine translation (Opus-MT)
    "casi",
    "monitoring",
    "solutions",
    "products",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",       
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:8080,http://localhost:8001,http://localhost:3000,http://127.0.0.1:3000,"
    ).split(",")
    if origin.strip()
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001"
    ).split(",")
    if origin.strip()
]

WAGTAILADMIN_BASE_URL = os.environ.get("SITE_URL", "http://localhost:8001")
HEADLESS_PREVIEW_CLIENT_URLS = {
    "default": os.environ.get("FRONTEND_URL", "http://localhost:5173") + "/preview",
}
ROOT_URLCONF = "axatel.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

WSGI_APPLICATION = "axatel.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

if DATABASES["default"].get("ENGINE") == "django.db.backends.mysql":
    DATABASES["default"].setdefault("OPTIONS", {}).update({
        "charset": "utf8mb4",
        "init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_general_ci",
    })

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "it-it"

# ── Translations ─────────────────────────────────────────────────────────
# Italian is the default and the source of every page. English and French
# pages are created in the CMS with the "Traduci" action on a page (copies
# it into the other language for an editor to translate).
# The API returns ONLY Italian unless ?locale=en / ?locale=fr is passed
# (core/api.py), so enabling this changes nothing for existing callers.
WAGTAIL_I18N_ENABLED = True
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
    ("it", "Italiano"),
    ("en", "English"),
    ("fr", "Français"),
]
TIME_ZONE     = "Europe/Rome"
USE_I18N      = True
USE_TZ        = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if os.environ.get("REDIS_URL"):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.environ.get("REDIS_URL"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# Who receives contact-form notifications (mail_admins) and server
# error emails. Comma-separated in .env: ADMIN_EMAILS=info@axatel.it,ops@axatel.it
ADMINS = [
    ("Axatel", email.strip())
    for email in os.environ.get("ADMIN_EMAILS", "").split(",")
    if email.strip()
]
MANAGERS = ADMINS

WAGTAIL_SITE_NAME               = "Axatel"
WAGTAIL_ENABLE_WHATS_NEW_BANNER = False

WAGTAILSEO_TWITTER_SITE  = "@axatel"
WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "svg"]

FILE_UPLOAD_PERMISSIONS = None


# Self-hosted machine translation (translation/engine.py): where the converted
# Opus-MT models live (manage.py setup_translation_models puts them there).
TRANSLATION_MODEL_DIR = os.environ.get("TRANSLATION_MODEL_DIR", str(BASE_DIR / "models" / "mt"))
