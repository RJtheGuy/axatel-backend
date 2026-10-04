"""
Check that the site can send e-mail, before relying on it.

    python manage.py send_test_email                 # to every address in Impostazioni → Notifiche moduli
    python manage.py send_test_email --to me@axatel.it

Sends a sample "Richiesta di contatto" notification (nothing is saved) and
prints the settings used and, on failure, the server's exact error.
"""
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ContactSubmission
from core.notifications import build_notification, email_configured, recipients_for


class Command(BaseCommand):
    help = "Send a test notification e-mail and show what went wrong if it fails."

    def add_arguments(self, parser):
        parser.add_argument("--to", action="append", default=[], help="Address to send to (repeatable).")

    def handle(self, *args, to=(), **options):
        self.stdout.write(f"Server: {settings.EMAIL_HOST or '(none)'}:{getattr(settings, 'EMAIL_PORT', '')} "
                          f"SSL={getattr(settings, 'EMAIL_USE_SSL', False)} TLS={getattr(settings, 'EMAIL_USE_TLS', False)} "
                          f"user={getattr(settings, 'EMAIL_HOST_USER', '') or '(none)'} from={settings.DEFAULT_FROM_EMAIL}")
        if not email_configured():
            self.stderr.write(self.style.ERROR(
                "E-mail is not configured: add EMAIL_HOST, EMAIL_PORT, EMAIL_USE_SSL or EMAIL_USE_TLS, "
                "EMAIL_HOST_USER and EMAIL_HOST_PASSWORD to /var/www/axatel/.env, then systemctl restart axatel."))
            return
        for kind, label in ContactSubmission.CONTACT_TYPES:
            self.stdout.write(f"  {label}: {', '.join(recipients_for(kind)) or '(nobody)'}")
        recipients = list(to) or recipients_for("contact")
        if not recipients:
            self.stderr.write(self.style.ERROR("Nobody to send to: fill Impostazioni → Notifiche moduli, or use --to."))
            return
        sample = ContactSubmission(
            pk=0, name="Prova Sito", company="Axatel (test)", email=recipients[0], phone="+39 0444 000000",
            submission_type="contact", message="Questa è un'e-mail di prova inviata con manage.py send_test_email.",
            language="it", privacy_consent=True,
        )
        sample.created_at = timezone.now()
        try:
            build_notification(sample, recipients, attach=False).send()
        except Exception as error:  # noqa: BLE001
            self.stderr.write(self.style.ERROR(f"Not sent: {type(error).__name__}: {error}"))
            self.stderr.write("Check the server name, port, SSL/TLS choice, user and password in .env "
                              "(many providers need the full address as user and an app password).")
            return
        self.stdout.write(self.style.SUCCESS(f"Sent to {', '.join(recipients)}. Check the inbox (and the spam folder)."))
