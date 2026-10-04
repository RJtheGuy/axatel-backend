"""
E-mails about requests sent from the site's forms (contact, quote, CV,
partnership).

- notify(): tells Axatel. Recipients per request type come from
  Impostazioni → Notifiche moduli (fallback: ADMIN_EMAILS in .env). "Reply"
  in the mail program answers the visitor directly. The CV or document is
  attached when the setting says so. The outcome is stored on the request
  (notified_at / notify_error), so a failed send is visible in Richieste di
  contatto and can be sent again (manage.py resend_notifications).
- confirm(): tells the visitor the request arrived, in the site language
  they used, when the setting is on.

The request itself is always saved first: an e-mail problem never loses it.
"""
import html
import logging
import re

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)

QUOTE_DETAIL_FIELDS = {
    "subject": "Prodotto o soluzione",
    "sector": "Tipo di opera",
    "sites": "Punti o siti",
    "timeline": "Tempistiche",
}
CONFIRM_SUBJECT = {
    "it": "Abbiamo ricevuto la tua richiesta — Axatel",
    "en": "We have received your request — Axatel",
    "fr": "Nous avons bien reçu votre demande — Axatel",
}
EMAIL_RE = re.compile(r"[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+")


def _file_name(field) -> str:
    """The visitor's file name, without the random prefix added on upload."""
    return re.sub(r"^[0-9a-f]{32}_", "", field.name.rsplit("/", 1)[-1])


def email_configured() -> bool:
    return bool(getattr(settings, "EMAIL_HOST", "")) and "dummy" not in settings.EMAIL_BACKEND


def _settings():
    from wagtail.models import Site

    from .site_settings import FormNotificationSettings

    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
    return FormNotificationSettings.for_site(site) if site else None


def recipients_for(kind: str) -> list[str]:
    config = _settings()
    found = []
    if config is not None:
        own = getattr(config, f"emails_{kind}", "") or ""
        found = EMAIL_RE.findall(own) or EMAIL_RE.findall(config.emails_contact or "")
    if not found:
        found = [email for _, email in getattr(settings, "ADMINS", [])]
    return list(dict.fromkeys(found))


def _admin_link(submission) -> str:
    base = (getattr(settings, "WAGTAILADMIN_BASE_URL", "") or "").rstrip("/")
    return f"{base}/django-admin/core/contactsubmission/{submission.pk}/change/" if base else ""


def _rows(submission) -> list[tuple[str, str]]:
    rows = [
        ("Tipo", submission.get_submission_type_display()),
        ("Nome", submission.name),
        ("Azienda", submission.company or "—"),
        ("E-mail", submission.email),
        ("Telefono", submission.phone or "—"),
        ("Lingua del sito", (submission.language or "it").upper()),
    ]
    if submission.interests:
        rows.append(("Interessi", ", ".join(submission.interests)))
    for key, value in (submission.details or {}).items():
        rows.append((QUOTE_DETAIL_FIELDS.get(key, key), value))
    if submission.attachment:
        rows.append(("Allegato", _file_name(submission.attachment)))
    rows.append(("Consenso privacy", "sì" if submission.privacy_consent else "no"))
    rows.append(("Ricevuta il", timezone.localtime(submission.created_at).strftime("%d/%m/%Y %H:%M")))
    return rows


def build_notification(submission, recipients, attach=True) -> EmailMultiAlternatives:
    kind = submission.get_submission_type_display()
    who = submission.name + (f" ({submission.company})" if submission.company else "")
    subject = f"[Sito Axatel] {kind} — {who}"
    rows = _rows(submission)
    link = _admin_link(submission)
    message = submission.message or "—"

    text = "\n".join(f"{label}: {value}" for label, value in rows)
    text += f"\n\nMessaggio:\n{message}\n"
    text += "\nRispondi a questa e-mail per scrivere direttamente a chi ha inviato la richiesta.\n"
    if link:
        text += f"Nel CMS: {link}\n"

    cell = "padding:6px 12px;border-bottom:1px solid #e3e9ef;vertical-align:top;"
    body_rows = "".join(
        f"<tr><th style='{cell}text-align:left;color:#667f97;font-weight:600;white-space:nowrap'>{html.escape(label)}</th>"
        f"<td style='{cell}color:#0b355b'>{html.escape(str(value))}</td></tr>"
        for label, value in rows
    )
    html_body = (
        "<div style='font-family:Arial,Helvetica,sans-serif;max-width:640px'>"
        f"<p style='margin:0 0 4px;color:#c52317;font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase'>{html.escape(kind)}</p>"
        f"<h2 style='margin:0 0 16px;color:#0b355b'>{html.escape(who)}</h2>"
        f"<table style='border-collapse:collapse;width:100%;font-size:14px'>{body_rows}</table>"
        f"<h3 style='margin:20px 0 6px;color:#0b355b;font-size:15px'>Messaggio</h3>"
        f"<p style='white-space:pre-wrap;color:#274e72;font-size:14px;line-height:1.5'>{html.escape(message)}</p>"
        "<p style='color:#667f97;font-size:12px'>Rispondi a questa e-mail per scrivere direttamente a chi ha inviato la richiesta."
        + (f" <a href='{html.escape(link)}'>Apri nel CMS</a>" if link else "")
        + "</p></div>"
    )
    mail = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, recipients, reply_to=[submission.email])
    mail.attach_alternative(html_body, "text/html")
    if attach and submission.attachment:
        try:
            submission.attachment.open("rb")
            mail.attach(_file_name(submission.attachment), submission.attachment.read())
        finally:
            submission.attachment.close()
    return mail


def notify(submission) -> bool:
    """E-mail Axatel about a saved request; records the outcome on it."""
    from .models import ContactSubmission

    recipients = recipients_for(submission.submission_type)
    error = ""
    if not email_configured():
        error = "E-mail non configurata sul server (EMAIL_HOST nel file .env)."
    elif not recipients:
        error = "Nessun destinatario: Impostazioni → Notifiche moduli (o ADMIN_EMAILS nel .env)."
    else:
        config = _settings()
        try:
            build_notification(submission, recipients, attach=config.attach_files if config else True).send()
        except Exception as exc:  # noqa: BLE001 - recorded on the request, never lost
            logger.exception("Contact notification failed")
            error = f"{type(exc).__name__}: {exc}"[:1000]
    ContactSubmission.objects.filter(pk=submission.pk).update(
        notified_at=None if error else timezone.now(), notify_error=error,
    )
    return not error


def confirm(submission) -> bool:
    """Tell the visitor the request arrived (Impostazioni → Notifiche moduli)."""
    config = _settings()
    if config is None or not config.send_confirmation or not email_configured():
        return False
    language = submission.language if submission.language in ("it", "en", "fr") else "it"
    template = (getattr(config, f"confirmation_{language}", "") or config.confirmation_it or "").strip()
    if not template:
        return False
    text = template.replace("{nome}", submission.name.split(" ")[0] if submission.name else "")
    recipients = recipients_for(submission.submission_type)
    try:
        EmailMultiAlternatives(
            CONFIRM_SUBJECT[language], text, settings.DEFAULT_FROM_EMAIL, [submission.email],
            reply_to=recipients[:1] or None,
        ).send()
        return True
    except Exception:  # noqa: BLE001
        logger.exception("Confirmation e-mail failed")
        return False
