"""
Compute every vector the chatbot needs (questions and page passages) and
keep them in the database, so the first visitor after a restart does not
wait. Run after deploying: python manage.py chatbot_warmup
"""
import time

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Prepare the chatbot index (questions and page passages) ahead of the first visitor."

    def handle(self, *args, **options):
        from chatbot.engine import engine

        start = time.monotonic()
        questions, passages = engine.warm_up()
        self.stdout.write(self.style.SUCCESS(
            f"Chatbot ready: {questions} questions, {passages} page passages ({time.monotonic() - start:.0f}s)."))
