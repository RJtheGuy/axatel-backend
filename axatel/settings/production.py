
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

# E-mail for form notifications (core/notifications.py) and error reports.
# All from .env, e.g. for Aruba:
#   EMAIL_HOST=smtps.aruba.it  EMAIL_PORT=465  EMAIL_USE_SSL=true
#   EMAIL_HOST_USER=sito@axatel.it  EMAIL_HOST_PASSWORD=...
# Microsoft 365: smtp.office365.com, 587, TLS. Google Workspace: smtp.gmail.com, 587, TLS (app password).
# Without EMAIL_HOST nothing is sent (requests are still saved in the CMS).
EMAIL_HOST          = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT          = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_SSL       = os.environ.get("EMAIL_USE_SSL", "false").lower() in ("true", "1", "t", "yes")
EMAIL_USE_TLS       = (not EMAIL_USE_SSL) and os.environ.get("EMAIL_USE_TLS", "true").lower() in ("true", "1", "t", "yes")
EMAIL_HOST_USER     = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT       = int(os.environ.get("EMAIL_TIMEOUT", "15"))
EMAIL_BACKEND       = ("django.core.mail.backends.smtp.EmailBackend" if EMAIL_HOST
                       else "django.core.mail.backends.dummy.EmailBackend")
# Most providers only accept mail "from" the account that logs in.
DEFAULT_FROM_EMAIL  = os.environ.get("DEFAULT_FROM_EMAIL", "") or (f"Sito Axatel <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else "noreply@axatel.it")
SERVER_EMAIL        = os.environ.get("SERVER_EMAIL", "") or EMAIL_HOST_USER or "errors@axatel.it"

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
