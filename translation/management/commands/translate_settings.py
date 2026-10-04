"""
Fill the empty English/French labels of the menu, the header button and the
team (roles, descriptions, departments) with the self-hosted model. Fields
already filled in are never touched.

    python manage.py translate_settings --dry-run
    python manage.py translate_settings
"""
from django.core.management.base import BaseCommand

from translation.engine import Translator
from translation.settings_fill import fill_settings


class _Preview:
    def one(self, text):
        return "…"


class Command(BaseCommand):
    help = "Translate empty English/French fields of the menu and the team."

    def add_arguments(self, parser):
        parser.add_argument("--languages", default="en,fr")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, languages="en,fr", dry_run=False, **options):
        for language in [l.strip() for l in languages.split(",") if l.strip()]:
            translator = _Preview() if dry_run else Translator(language)
            notes = fill_settings(language, translator, dry_run=dry_run)
            for note in notes:
                self.stdout.write(f"[{language}] {note}")
            self.stdout.write(self.style.SUCCESS(f"[{language}] {len(notes)} field(s) {'would be ' if dry_run else ''}filled."))
