from .base import *
from django.core.exceptions import ImproperlyConfigured

DEBUG        = True
ALLOWED_HOSTS = ["*"]


WAGTAILADMIN_BASE_URL = "http://127.0.0.1:8000"

if not os.environ.get("DATABASE_URL", "").startswith(("mysql://", "mysql+", "mariadb://")):
    raise ImproperlyConfigured(
        "Local development requires DATABASE_URL to point to a MySQL/MariaDB database."
    )

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += ["django_extensions"]
