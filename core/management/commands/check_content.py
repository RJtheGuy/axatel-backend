"""
What an editor still has to do before go-live (and any time after):
test values, links to the old site, empty pages, missing translations…

    python manage.py check_content             # full list with CMS links
    python manage.py check_content --summary   # counts per group
    python manage.py check_content --only placeholders,translations

Read-only. The same list is in the CMS: Rapporti → Controllo contenuti.
See core/content_audit.py for what each group checks.
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from core.content_audit import GROUP_LABELS, run_audit, summary


class Command(BaseCommand):
    help = "List content still to complete, translate or fix before go-live."

    def add_arguments(self, parser):
        parser.add_argument("--summary", action="store_true", help="counts only")
        parser.add_argument("--only", default="", help="comma-separated groups, e.g. placeholders,old_links")

    def handle(self, *args, summary_only=False, only="", **options):
        summary_only = options.get("summary") or summary_only
        wanted = {g.strip() for g in only.split(",") if g.strip()}
        findings = [f for f in run_audit() if not wanted or f.group in wanted]
        base = (getattr(settings, "WAGTAILADMIN_BASE_URL", "") or "").rstrip("/")

        for key, label, help_text, count in summary(findings):
            if wanted and key not in wanted:
                continue
            mark = self.style.SUCCESS("✓") if count == 0 else self.style.WARNING(str(count))
            self.stdout.write(f"{mark:>4}  {label}  [{key}]")
            if summary_only or count == 0:
                continue
            for f in (f for f in findings if f.group == key):
                language = f" [{f.language.upper()}]" if f.language and f.language != "it" else ""
                self.stdout.write(f"        - {f.title}{language}: {f.detail}")
                if f.url:
                    self.stdout.write(f"          {base}{f.url}")
        total = len(findings)
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Nothing left to do.") if total == 0 else f"{total} item(s) to look at.")
