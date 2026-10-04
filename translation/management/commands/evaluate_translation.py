"""
Measure translation quality before using it on pages.

Reference set: the site's interface texts, written by people in Italian,
English and French (translation/eval/interface.json, 244 texts). The model
translates the Italian ones; the result is compared with the human version.

    python manage.py evaluate_translation
    python manage.py evaluate_translation --languages fr --samples 10

Prints chrF and BLEU (sacrebleu; chrF is the more telling for short texts,
0-100, higher is better), speed on this server's CPU, how often protected
names and {placeholders} survive, and a few examples to read.
"""
import json
import re
import time
from pathlib import Path

from django.core.management.base import BaseCommand

from translation.engine import Translator

DATA = Path(__file__).resolve().parents[2] / "eval" / "interface.json"


class Command(BaseCommand):
    help = "Score the translation model against the site's own human translations."

    def add_arguments(self, parser):
        parser.add_argument("--languages", default="en,fr")
        parser.add_argument("--samples", type=int, default=6)
        parser.add_argument("--limit", type=int, default=0)

    def handle(self, *args, languages="en,fr", samples=6, limit=0, **options):
        import sacrebleu

        rows = json.loads(DATA.read_text(encoding="utf-8"))
        if limit:
            rows = rows[:limit]
        for language in [l.strip() for l in languages.split(",") if l.strip()]:
            pairs = [(r["it"], r[language]) for r in rows if r.get("it") and r.get(language)]
            sources = [p[0] for p in pairs]
            references = [p[1] for p in pairs]

            started = time.perf_counter()
            translator = Translator(language, memory=False)
            load = time.perf_counter() - started
            started = time.perf_counter()
            outputs = translator.translate(sources)
            elapsed = time.perf_counter() - started

            chrf = sacrebleu.corpus_chrf(outputs, [references]).score
            bleu = sacrebleu.corpus_bleu(outputs, [references]).score
            braces = [(s, o) for s, o in zip(sources, outputs) if re.search(r"\{\w+\}", s)]
            braces_ok = sum(all(b in o for b in re.findall(r"\{\w+\}", s)) for s, o in braces)
            terms = [(s, o, t) for s, o in zip(sources, outputs) for t in translator.terms if t in s]
            terms_ok = sum(t in o for s, o, t in terms)

            self.stdout.write(self.style.MIGRATE_HEADING(f"\nItalian → {language.upper()}  ({translator.backend.name})"))
            self.stdout.write(f"  texts: {len(pairs)}   sentences: {translator.stats['sentences']}")
            self.stdout.write(f"  chrF: {chrf:.1f}   BLEU: {bleu:.1f}")
            self.stdout.write(f"  speed: {elapsed:.1f}s total, {1000 * elapsed / max(1, translator.stats['sentences']):.0f} ms per sentence "
                              f"(model load {load:.1f}s)")
            if braces:
                self.stdout.write(f"  {{placeholders}} kept: {braces_ok}/{len(braces)}")
            if terms:
                self.stdout.write(f"  protected names kept: {terms_ok}/{len(terms)}  (shielded and retried: {translator.stats['protected']})")
            step = max(1, len(pairs) // max(1, samples))
            for i in range(0, len(pairs), step)[:samples]:
                self.stdout.write(f"  · IT  {sources[i][:110]}\n    MT  {outputs[i][:110]}\n    REF {references[i][:110]}")
