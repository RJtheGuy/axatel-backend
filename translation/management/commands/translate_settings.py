"""
Fill the English/French labels of the menu, the header button, the team
(roles, descriptions, departments) and the chatbot answers with the
self-hosted model: empty fields, and fields that still hold an earlier
machine translation. Fields typed or corrected by hand are never touched.

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
    help = "Translate empty (or machine-made) English/French fields: menu, team, chatbot answers."

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
