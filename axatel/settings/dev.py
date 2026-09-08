from .base import *

DEBUG        = True
ALLOWED_HOSTS = ["*"]


WAGTAILADMIN_BASE_URL = "http://127.0.0.1:8000"


CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += ["django_extensions"]