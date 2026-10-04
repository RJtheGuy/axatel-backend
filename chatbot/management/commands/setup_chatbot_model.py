"""
Download the chatbot's embedding model once, into models/chatbot/, so the
site never fetches it while a visitor waits (and keeps working when
Hugging Face is unreachable).

    python manage.py setup_chatbot_model
    python manage.py setup_chatbot_model --model all-MiniLM-L6-v2   # e.g. to compare in evaluate_chatbot
"""
from django.core.management.base import BaseCommand

from chatbot.engine import ChatbotEngine, chatbot_model_path


class Command(BaseCommand):
    help = "Download the chatbot embedding model to models/chatbot/."

    def add_arguments(self, parser):
        parser.add_argument("--model", default=ChatbotEngine.MODEL_NAME)

    def handle(self, *args, model, **options):
        from sentence_transformers import SentenceTransformer

        target = chatbot_model_path(model)
        if (target / "modules.json").exists():
            self.stdout.write(f"= {target} already there")
            return
        self.stdout.write(f"+ {model} → {target}")
        SentenceTransformer(model, device="cpu").save(str(target))
        size = sum(f.stat().st_size for f in target.rglob("*") if f.is_file()) / 1e6
        self.stdout.write(self.style.SUCCESS(f"  ready, {size:.0f} MB. Restart the site (systemctl restart axatel) to use it."))
