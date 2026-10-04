"""
Download the Opus-MT models (Italian → English, Italian → French) from
Hugging Face and convert them to CTranslate2 int8 for fast CPU inference.
Run once on the server (needs internet and the transformers + torch
packages, already installed for the chatbot):

    python manage.py setup_translation_models
    python manage.py setup_translation_models --languages en --force

Models go to TRANSLATION_MODEL_DIR (default: <project>/models/mt), about
80 MB each. Licence: CC-BY 4.0 (Helsinki-NLP / University of Helsinki).
"""
import shutil

from django.core.management.base import BaseCommand, CommandError

from translation.engine import model_dir

MODELS = {"en": "Helsinki-NLP/opus-mt-it-en", "fr": "Helsinki-NLP/opus-mt-it-fr"}


class Command(BaseCommand):
    help = "Download and convert the self-hosted translation models (Opus-MT → CTranslate2 int8)."

    def add_arguments(self, parser):
        parser.add_argument("--languages", default="en,fr")
        parser.add_argument("--force", action="store_true", help="Convert again even if the model is there.")

    def handle(self, *args, languages="en,fr", force=False, **options):
        try:
            import ctranslate2
            from transformers import AutoTokenizer
        except ImportError as error:
            raise CommandError(f"Missing package ({error}). Run: venv/bin/pip install -r requirements.txt")

        base = model_dir()
        base.mkdir(parents=True, exist_ok=True)
        for language in [l.strip() for l in languages.split(",") if l.strip()]:
            name = MODELS.get(language)
            if not name:
                raise CommandError(f"No model configured for '{language}'.")
            target = base / f"opus-mt-it-{language}"
            if (target / "model.bin").exists() and not force:
                self.stdout.write(f"= {target} already there")
                continue
            if target.exists():
                shutil.rmtree(target)
            self.stdout.write(f"+ {name} → {target} (download and int8 conversion, a minute or two)")
            converter = ctranslate2.converters.TransformersConverter(name)
            converter.convert(str(target), quantization="int8", force=True)
            AutoTokenizer.from_pretrained(name).save_pretrained(str(target))
            size = sum(f.stat().st_size for f in target.rglob("*") if f.is_file()) / 1e6
            self.stdout.write(self.style.SUCCESS(f"  ready, {size:.0f} MB"))
        self.stdout.write("Next: python manage.py evaluate_translation")
