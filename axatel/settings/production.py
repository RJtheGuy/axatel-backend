
from .base import *

DEBUG         = False
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "axatel.it,www.axatel.it").split(",")
    if host.strip()
]

SECURE_SSL_REDIRECT            = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() in ("true", "1", "t")
SECURE_HSTS_SECONDS            = 31536000 if SECURE_SSL_REDIRECT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_SSL_REDIRECT
SECURE_HSTS_PRELOAD             = SECURE_SSL_REDIRECT
SESSION_COOKIE_SECURE           = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE              = SECURE_SSL_REDIRECT
SECURE_CONTENT_TYPE_NOSNIFF    = True
X_FRAME_OPTIONS                = "DENY"

EMAIL_BACKEND       = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST          = os.environ.get("EMAIL_HOST",     "smtp.sendgrid.net")
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.environ.get("EMAIL_HOST_USER",     "apikey")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL  = "noreply@axatel.it"
SERVER_EMAIL        = "errors@axatel.it"

log_dir = BASE_DIR / "logs"
log_dir.mkdir(exist_ok=True, parents=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "logs/django.log"),
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["file"], "level": "ERROR"},
}
