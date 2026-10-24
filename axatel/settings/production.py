
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
# Microsoft 365: use the Graph settings below (SMTP passwords stop working there
# at the end of 2026). Google Workspace: smtp.gmail.com, 587, TLS (app password).
# Without EMAIL_HOST nothing is sent (requests are still saved in the CMS).
EMAIL_HOST          = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT          = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_SSL       = os.environ.get("EMAIL_USE_SSL", "false").lower() in ("true", "1", "t", "yes")
EMAIL_USE_TLS       = (not EMAIL_USE_SSL) and os.environ.get("EMAIL_USE_TLS", "true").lower() in ("true", "1", "t", "yes")
EMAIL_HOST_USER     = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT       = int(os.environ.get("EMAIL_TIMEOUT", "15"))
# Microsoft 365 (recommended there): the Graph API with an app registered in
# Microsoft Entra, see core/mail_graph.py. When these are set they win over SMTP:
#   GRAPH_TENANT_ID=…  GRAPH_CLIENT_ID=…  GRAPH_CLIENT_SECRET=…  GRAPH_SENDER=sito@axatel.it
GRAPH_TENANT_ID     = os.environ.get("GRAPH_TENANT_ID", "").strip()
GRAPH_CLIENT_ID     = os.environ.get("GRAPH_CLIENT_ID", "").strip()
GRAPH_CLIENT_SECRET = os.environ.get("GRAPH_CLIENT_SECRET", "").strip()
GRAPH_SENDER        = os.environ.get("GRAPH_SENDER", "").strip()
USE_GRAPH           = all((GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET, GRAPH_SENDER))
MAIL_ACCOUNT        = GRAPH_SENDER if USE_GRAPH else EMAIL_HOST_USER
EMAIL_BACKEND       = ("core.mail_graph.GraphEmailBackend" if USE_GRAPH
                       else "django.core.mail.backends.smtp.EmailBackend" if EMAIL_HOST
                       else "django.core.mail.backends.dummy.EmailBackend")
# Most providers only accept mail "from" the account that logs in.
DEFAULT_FROM_EMAIL  = os.environ.get("DEFAULT_FROM_EMAIL", "") or (f"Sito Axatel <{MAIL_ACCOUNT}>" if MAIL_ACCOUNT else "noreply@axatel.it")
SERVER_EMAIL        = os.environ.get("SERVER_EMAIL", "") or MAIL_ACCOUNT or "errors@axatel.it"

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
