"""
Translate Italian pages into English / French drafts with the self-hosted
model (see translation/engine.py). Same as the "Traduci" button in the CMS,
for many pages at once.

    python manage.py translate_pages --dry-run --all          # what and how much, no model needed
    python manage.py translate_pages --page chi-siamo
    python manage.py translate_pages --type monitoring.MonitoringPage --languages en
    python manage.py translate_pages --all

Each translation is saved as a DRAFT of the English/French page: review it
in the CMS and press Pubblica. Pages whose translation has a draft waiting
are skipped, so nobody's edits are overwritten.
"""
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from wagtail.models import Page

from translation.engine import Translator
from translation.pages import translate_page


class Command(BaseCommand):
    help = "Translate Italian pages into English/French drafts (self-hosted model)."

    def add_arguments(self, parser):
        parser.add_argument("--page", action="append", default=[], help="Page id or slug (repeatable).")
        parser.add_argument("--type", default="", help="Page type, e.g. monitoring.MonitoringPage")
        parser.add_argument("--all", action="store_true", help="Every published Italian page.")
        parser.add_argument("--languages", default="en,fr")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, page=(), type="", all=False, languages="en,fr", dry_run=False, **options):
        italian = Page.objects.filter(locale__language_code="it", depth__gt=1).live()
        if page:
            chosen = Page.objects.none()
            for ref in page:
                chosen = chosen | (italian.filter(id=int(ref)) if str(ref).isdigit() else italian.filter(slug=ref))
            pages = chosen
        elif type:
            try:
                model = apps.get_model(type)
            except (LookupError, ValueError):
                raise CommandError(f"Unknown page type '{type}'.")
            pages = italian.type(model)
        elif all:
            pages = italian
        else:
            raise CommandError("Say which pages: --page, --type or --all.")

        pages = list(pages.order_by("path"))
        if not pages:
            self.stdout.write("No matching published Italian page.")
            return
        for language in [l.strip() for l in languages.split(",") if l.strip()]:
            translator = None if dry_run else Translator(language)
            for p in pages:
                report = translate_page(p, language, translator, dry_run=dry_run)
                self.stdout.write(f"{p.url_path.replace('/home', '', 1) or '/'}  {report}")
            if translator:
                s = translator.stats
                self.stdout.write(self.style.SUCCESS(
                    f"{language}: {s['texts']} texts ({s['from_memory']} from memory), {s['sentences']} sentences "
                    f"in {s['seconds']:.0f}s"))
