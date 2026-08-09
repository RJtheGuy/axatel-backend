"""
Development settings.
Uses SQLite so you can run locally with zero infrastructure.
python manage.py runserver  ← uses this file by default (see manage.py)
"""
from .base import *

DEBUG        = True
ALLOWED_HOSTS = ["*"]

# SQLite for local dev — no Postgres install needed
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME":   BASE_DIR / "db.sqlite3",
    }
}

# In-memory cache — no Redis needed locally
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

# Print emails to the terminal instead of sending them
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Extra dev tools (shell_plus, graph_models, etc.)
INSTALLED_APPS += ["django_extensions"]
