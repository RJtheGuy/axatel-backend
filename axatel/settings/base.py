# import os
# from pathlib import Path
# from dotenv import load_dotenv

# load_dotenv()

# BASE_DIR = Path(__file__).resolve().parent.parent.parent
# SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-before-production")
# DEBUG = False
# ALLOWED_HOSTS = []

# INSTALLED_APPS = [
#     # ── Wagtail ───────────────────────────────────────────────
#     "wagtail.contrib.forms",
#     "wagtail.contrib.redirects",     # 301/302 from admin, no plugin needed
#     "wagtail.contrib.sitemaps",      # auto sitemap.xml
#     "wagtail.contrib.routable_page",
#     "wagtail.embeds",                # YouTube/Vimeo in VideoBlock
#     "wagtail.sites",
#     "wagtail.users",
#     "wagtail.snippets",
#     "wagtail.documents",
#     "wagtail.images",
#     "wagtail.search",
#     "wagtail.admin",
#     "wagtail",
#     "wagtail.contrib.settings",
#     "wagtail.api.v2",
#     "rest_framework",
#     "wagtail_headless_preview",
#     "corsheaders",
#     "modelcluster",
#     "taggit",
#     # ── Django ────────────────────────────────────────────────
#     "django.contrib.admin",
#     "django.contrib.auth",
#     "django.contrib.contenttypes",
#     "django.contrib.sessions",
#     "django.contrib.messages",
#     "django.contrib.staticfiles",
#     "django.contrib.sitemaps",
#     # ── Third-party ───────────────────────────────────────────
#     "wagtailseo",                    # site-wide SEO panel + Twitter Cards
#     # ── Local apps ────────────────────────────────────────────
#     "core",
#     "home",
#     "services",
#     "blog",
#     "seo",
#     "chatbot",
# ]

# MIDDLEWARE = [
#     "django.middleware.security.SecurityMiddleware",
#     "corsheaders.middleware.CorsMiddleware",
#     "whitenoise.middleware.WhiteNoiseMiddleware",       # fast static file serving
#     "django.contrib.sessions.middleware.SessionMiddleware",
#     "django.middleware.common.CommonMiddleware",
#     "django.middleware.csrf.CsrfViewMiddleware",
#     "django.contrib.auth.middleware.AuthenticationMiddleware",
#     "django.contrib.messages.middleware.MessageMiddleware",
#     "django.middleware.clickjacking.XFrameOptionsMiddleware",
#     "wagtail.contrib.redirects.middleware.RedirectMiddleware",

# ]

# # CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
# # Replace line 64 with this:
# CORS_ALLOWED_ORIGINS = [
#     origin.strip()
#     for origin in os.environ.get(
#         "CORS_ALLOWED_ORIGINS",
#         "http://localhost:5173,http://localhost:8080,http://localhost:8001"
#     ).split(",")
#     if origin.strip()  # <--- Filters out empty strings!
# ]

# WAGTAILADMIN_BASE_URL = os.environ.get("SITE_URL", "https://axatel.it")
# HEADLESS_PREVIEW_CLIENT_URLS = {
#     "default": os.environ.get("FRONTEND_URL", "http://localhost:5173") + "/preview",
#  }
# ROOT_URLCONF = "axatel.urls"

# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [BASE_DIR / "templates"],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.debug",
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#                 "wagtail.contrib.settings.context_processors.settings",
#             ],
#         },
#     },
# ]

# WSGI_APPLICATION = "axatel.wsgi.application"

# # ─── Database ─────────────────────────────────────────────────────────────────
# # Default: PostgreSQL. See dev.py for SQLite override during development.
# # To use MySQL: change ENGINE to django.db.backends.mysql, add mysqlclient to requirements.
# # To use MSSQL:  change ENGINE to mssql, add mssql-django to requirements.
# DATABASES = {
#     "default": {
#         "ENGINE":   "django.db.backends.postgresql",
#         "NAME":     os.environ.get("DB_NAME",     "axatel"),
#         "USER":     os.environ.get("DB_USER",     "axatel"),
#         "PASSWORD": os.environ.get("DB_PASSWORD", ""),
#         "HOST":     os.environ.get("DB_HOST",     "localhost"),
#         "PORT":     os.environ.get("DB_PORT",     "5432"),
#     }
# }

# AUTH_PASSWORD_VALIDATORS = [
#     {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
#     {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
#     {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
#     {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
# ]

# LANGUAGE_CODE = "it-it"
# TIME_ZONE     = "Europe/Rome"
# USE_I18N      = True
# USE_TZ        = True

# STATIC_URL          = "/static/"
# STATIC_ROOT         = BASE_DIR / "staticfiles"
# STATICFILES_DIRS    = [BASE_DIR / "static"]
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# MEDIA_URL  = "/media/"
# MEDIA_ROOT = BASE_DIR / "media"

# DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# # ─── Cache (Redis) ─────────────────────────────────────────────────────────────
# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
#         "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
#     }
# }

# # ─── Wagtail ──────────────────────────────────────────────────────────────────
# WAGTAIL_SITE_NAME            = "Axatel"
# # WAGTAILADMIN_BASE_URL        = os.environ.get("SITE_URL", "https://axatel.it")
# WAGTAIL_ENABLE_WHATS_NEW_BANNER = False
# WAGTAILADMIN_BASE_URL = "http://localhost:8001"

# # ─── wagtail-seo ──────────────────────────────────────────────────────────────
# # These are the fallback values used when a page has no OG image set.
# # Marketing agent can override per-page in the Promote tab.
# WAGTAILSEO_TWITTER_SITE = "@axatel"
# WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "svg"]



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
    "localhost",      # browser → host-exposed port 8001
    "127.0.0.1",
    "web",            # ← REQUIRED: Nuxt SSR calls http://web:8000 container-to-container
]

INSTALLED_APPS = [
    # ── Wagtail ───────────────────────────────────────────────
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",     # 301/302 from admin, no plugin needed
    "wagtail.contrib.sitemaps",      # auto sitemap.xml
    "wagtail.contrib.routable_page",
    "wagtail.embeds",                # YouTube/Vimeo in VideoBlock
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "wagtail.contrib.settings",
    "wagtail.api.v2",
    "rest_framework",
    "wagtail_headless_preview",
    "corsheaders",
    "modelcluster",
    "taggit",
    # ── Django ────────────────────────────────────────────────
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # ── Third-party ───────────────────────────────────────────
    "wagtailseo",                    # site-wide SEO panel + Twitter Cards
    # ── Local apps ────────────────────────────────────────────
    "core",
    "home",
    "services",
    "blog",
    "seo",
    "chatbot",
    "casi",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",       # fast static file serving
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
        "http://localhost:5173,http://localhost:8080,http://localhost:8001,http://localhost:3000"
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

# ─── Database ─────────────────────────────────────────────────────────────────
# Dynamically parses DATABASE_URL from .env (supports SQLite, Postgres, MySQL, etc.)
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "it-it"
TIME_ZONE     = "Europe/Rome"
USE_I18N      = True
USE_TZ        = True

STATIC_URL          = "/static/"
STATIC_ROOT         = BASE_DIR / "staticfiles"

# Prevents staticfiles.W004 warning if the 'static/' folder doesn't exist yet
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Cache (Redis) ─────────────────────────────────────────────────────────────
# Uses in-memory cache if REDIS_URL isn't set or fails in local dev
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

# ─── Wagtail ──────────────────────────────────────────────────────────────────
WAGTAIL_SITE_NAME               = "Axatel"
WAGTAIL_ENABLE_WHATS_NEW_BANNER = False

# ─── wagtail-seo ──────────────────────────────────────────────────────────────
WAGTAILSEO_TWITTER_SITE  = "@axatel"
WAGTAILIMAGES_EXTENSIONS = ["gif", "jpg", "jpeg", "png", "webp", "svg"]


FILE_UPLOAD_PERMISSIONS = None