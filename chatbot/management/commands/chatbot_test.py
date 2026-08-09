"""
chatbot/management/commands/chatbot_test.py

Runs every question currently in the database (ChatbotEntry, editable
from Snippets -> Voci chatbot) back through the engine, or a single
custom --query, and prints the similarity numbers behind each decision,
so ChatbotEngine.THRESHOLD and .MARGIN in chatbot/engine.py can be
tuned from real measurements instead of guesses.

This now tests whatever is LIVE in the CMS, not a fixed code-level list
- which is the point: an editor can add a new Voce chatbot, then run
this to see immediately whether the phrasing they chose actually gets
recognized, before trusting it in front of a real visitor.

Usage:
    python manage.py chatbot_test                 # run every known entry
    python manage.py chatbot_test --verbose        # show scores for hits too
    python manage.py chatbot_test --query "dove siete?"
"""

from django.core.management.base import BaseCommand

from chatbot.engine import engine
from chatbot.models import ChatbotEntry


class Command(BaseCommand):
    help = (
        "Test the chatbot engine against every ChatbotEntry currently in "
        "the database, or a single custom question, and show the match "
        "scores behind each answer."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--query", type=str,
            help="Test a single custom question instead of every known entry.",
        )
        parser.add_argument(
            "--verbose", action="store_true",
            help="Show scores for every question, not just the ones that fell back.",
        )

    def handle(self, *args, **options):
        if options["query"]:
            self._run_one(options["query"], verbose=True)
            return

        entries = ChatbotEntry.objects.filter(is_fallback=False)
        if not entries.exists():
            self.stdout.write(self.style.WARNING(
                "No ChatbotEntry rows found. Run `manage.py seed_chatbot_kb` "
                "first, or add some in Snippets -> Voci chatbot."
            ))
            return

        misses, total = 0, 0
        for entry in entries:
            for q in entry.questions_list:
                total += 1
                if self._run_one(q, verbose=options["verbose"]):
                    misses += 1

        self.stdout.write("")
        if misses:
            self.stdout.write(self.style.WARNING(
                f"{misses}/{total} known questions fell back - consider "
                f"lowering CHATBOT_THRESHOLD/CHATBOT_MARGIN, or rewording "
                f"those entries' questions to be more distinct from each other."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f"All {total} known questions matched correctly."))

    def _run_one(self, query: str, verbose: bool = False) -> bool:
        _, meta = engine.answer_with_scores(query)
        used_fallback = meta["used_fallback"]
        if used_fallback or verbose:
            tag = self.style.WARNING("FALLBACK") if used_fallback else self.style.SUCCESS("OK")
            reason = f" ({meta['reason']})" if used_fallback else ""
            self.stdout.write(
                f'[{tag}] "{query}" -> best={meta["best_score"]} '
                f'margin={meta["margin"]} match="{meta["matched_question"]}"{reason}'
            )
        return used_fallback