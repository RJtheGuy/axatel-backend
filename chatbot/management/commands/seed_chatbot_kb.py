"""
One-time seeder: turns the ~20 hardcoded entries in chatbot/kb_seed_data.py
into real ChatbotEntry rows, so the chatbot has something to say on a
fresh install, and so an editor has real examples to copy the pattern
of in Snippets → Voci chatbot before adding their own.

Usage:
    python manage.py seed_chatbot_kb --dry-run
    python manage.py seed_chatbot_kb

Safe to re-run: unlike seed_casi, there's no natural unique key (no
slug) for a Q&A pair, so an entry is skipped if a ChatbotEntry with the
exact same `answer` text already exists - the simplest dedup that holds
up at this scale (~20 entries, not thousands).
"""

from django.core.management.base import BaseCommand

from chatbot.kb_seed_data import KNOWLEDGE_BASE
from chatbot.models import ChatbotEntry


class Command(BaseCommand):
    help = "Seed ChatbotEntry rows from the legacy hardcoded KNOWLEDGE_BASE list."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show what would be created without writing to the DB.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created, skipped = 0, 0

        # Tracked locally rather than re-queried each loop: the unique
        # constraint on ChatbotEntry only stops a SECOND fallback being
        # SAVED - it won't stop this loop from trying to create two in
        # the same run and erroring on the second .create() call.
        have_fallback = ChatbotEntry.objects.filter(is_fallback=True).exists()

        for entry in KNOWLEDGE_BASE:
            answer = entry["answer"].strip()
            is_fallback = entry.get("_fallback", False)
            label = entry["questions"][0]

            if ChatbotEntry.objects.filter(answer=answer).exists():
                self.stdout.write(f"  skip (exists): {label}")
                skipped += 1
                continue

            if is_fallback and have_fallback:
                self.stdout.write(self.style.WARNING(
                    f"  skip (fallback already set elsewhere): {label}"
                ))
                skipped += 1
                continue

            self.stdout.write(f"  create: {label}")
            if not dry_run:
                ChatbotEntry.objects.create(
                    questions="\n".join(entry["questions"]),
                    answer=answer,
                    is_fallback=is_fallback,
                )
                if is_fallback:
                    have_fallback = True
            created += 1

        verb = "Would create" if dry_run else "Created"
        self.stdout.write(self.style.SUCCESS(
            f"{verb} {created} entr{'y' if created == 1 else 'ies'}, skipped {skipped} existing."
        ))