"""
Send again the notification e-mails that failed (e.g. while the mail server
was not configured or not reachable).

    python manage.py resend_notifications --dry-run
    python manage.py resend_notifications            # requests of the last 30 days
    python manage.py resend_notifications --days 90

Only requests whose send failed are picked (they have an "Errore di invio").
Requests received before this feature existed have no record and are left
alone; add --include-older to send those too.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ContactSubmission
from core.notifications import notify


class Command(BaseCommand):
    help = "Re-send form notifications that were never delivered."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--include-older", action="store_true",
                            help="also requests with no send record (received before update 26)")

    def handle(self, *args, days=30, dry_run=False, include_older=False, **options):
        since = timezone.now() - timedelta(days=days)
        waiting = ContactSubmission.objects.filter(created_at__gte=since, notified_at__isnull=True)
        if not include_older:
            waiting = waiting.exclude(notify_error="")
        waiting = list(waiting.order_by("created_at"))
        if not waiting:
            self.stdout.write("Nothing to send: every request of the period was notified.")
            return
        sent = 0
        for submission in waiting:
            if dry_run:
                self.stdout.write(f"  would send: {submission}")
                continue
            ok = notify(submission)
            sent += ok
            self.stdout.write(f"  {'sent' if ok else 'FAILED'}: {submission}")
        if not dry_run:
            style = self.style.SUCCESS if sent == len(waiting) else self.style.WARNING
            self.stdout.write(style(f"{sent}/{len(waiting)} sent."))
