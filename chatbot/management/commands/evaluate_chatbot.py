"""
Measure how well the chatbot recognises questions, and pick its thresholds
from data instead of guesses.

Leave-one-out on the knowledge base (Snippets → Voci chatbot): every
question of an entry that has at least two is hidden in turn and asked to
the bot, which must find the right entry from the others. With the
translation models installed, the same questions are also asked in English
and French, as visitors from those pages do.

    python manage.py evaluate_chatbot
    python manage.py evaluate_chatbot --models all-MiniLM-L6-v2,paraphrase-multilingual-MiniLM-L12-v2

Then the answers built from the site (topics, products, solutions, cases,
glossary, FAQ) are checked with the live engine: each is asked in words
that are NOT in its index ("mi parli di …", "… informazioni", the English
and French title) and must come back as itself, not as another answer or
the fallback.

For each model: top-1 accuracy, then for a grid of thresholds the share of
questions answered (coverage) and the share answered correctly (precision),
and the threshold with the most coverage at ≥ 90% precision. Put the chosen
values in .env (CHATBOT_THRESHOLD, CHATBOT_MARGIN) and restart.
"""
import numpy as np
from django.core.management.base import BaseCommand

from chatbot.engine import ChatbotEngine, chatbot_model_path
from chatbot.models import ChatbotEntry


def _cases(entries, normalize):
    questions, owners = [], []
    for entry in entries:
        for q in entry.questions_list:
            n = normalize(q)
            if n:
                questions.append(n)
                owners.append(entry.pk)
    counts = {o: owners.count(o) for o in set(owners)}
    tests = [i for i, o in enumerate(owners) if counts[o] >= 2]
    return questions, owners, tests


def _evaluate(model, index_texts, owners, queries, query_owner, exclude, margin_floor):
    index = model.encode(index_texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    asked = model.encode(queries, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    owners = np.array(owners)
    rows = []
    for qi, vector in enumerate(asked):
        scores = index @ vector
        if exclude[qi] is not None:
            scores[exclude[qi]] = -1.0  # the hidden question itself
        order = np.argsort(scores)[::-1]
        best = order[0]
        second = next((j for j in order[1:] if owners[j] != owners[best]), None)
        margin = scores[best] - (scores[second] if second is not None else 0.0)
        rows.append((float(scores[best]), float(margin), owners[best] == query_owner[qi]))
    return rows


class Command(BaseCommand):
    help = "Leave-one-out evaluation of the chatbot and threshold recommendation."

    def add_arguments(self, parser):
        parser.add_argument("--models", default=ChatbotEngine.MODEL_NAME)
        parser.add_argument("--margin", type=float, default=ChatbotEngine.MARGIN)

    def handle(self, *args, models, margin, **options):
        from sentence_transformers import SentenceTransformer

        entries = list(ChatbotEntry.objects.filter(is_fallback=False))
        normalize = ChatbotEngine._normalize_text
        questions, owners, tests = _cases(entries, normalize)
        if not tests:
            self.stdout.write("Not enough data: give each Voce chatbot at least two ways of asking.")
            return
        self.stdout.write(f"{len(entries)} entries, {len(questions)} questions, {len(tests)} held-out tests")

        # The same held-out questions in English and French, if the
        # translation models are installed (update 18).
        variants = {"it": [questions[i] for i in tests]}
        for language in ("en", "fr"):
            try:
                from translation.engine import Translator
                translated = Translator(language, memory=False, terms=[]).translate([questions[i] for i in tests])
                variants[language] = [normalize(t) for t in translated]
            except Exception as error:  # noqa: BLE001
                self.stdout.write(f"  ({language}: skipped, {str(error)[:80]})")

        for name in [m.strip() for m in models.split(",") if m.strip()]:
            local = chatbot_model_path(name)
            model = SentenceTransformer(str(local) if (local / "modules.json").exists() else name, device="cpu")
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{name}"))
            for language, queries in variants.items():
                # The original (Italian) question is hidden in every language:
                # the bot has to find its entry from the other questions.
                rows = _evaluate(model, questions, owners, queries, [owners[i] for i in tests], list(tests), margin)
                accuracy = np.mean([ok for _, _, ok in rows])
                self.stdout.write(f"  [{language}] top-1 accuracy: {accuracy:.0%}")
                best = None
                line = []
                for threshold in np.arange(0.40, 0.91, 0.05):
                    answered = [(s, m, ok) for s, m, ok in rows if s >= threshold and m >= margin]
                    coverage = len(answered) / len(rows)
                    precision = np.mean([ok for _, _, ok in answered]) if answered else 1.0
                    line.append(f"{threshold:.2f}: {coverage:.0%}/{precision:.0%}")
                    if precision >= 0.9 and (best is None or coverage > best[1]):
                        best = (threshold, coverage, precision)
                self.stdout.write("       threshold: answered/correct  " + "  ".join(line))
                if best:
                    self.stdout.write(self.style.SUCCESS(
                        f"       → CHATBOT_THRESHOLD={best[0]:.2f}: answers {best[1]:.0%} with {best[2]:.0%} correct"))

        self._site_check()

    def _site_check(self):
        """Ask each site answer in new words; it must come back as itself."""
        from chatbot.engine import engine

        answers = engine.site_answers()
        if not answers:
            self.stdout.write("\nSite answers: none (no published pages, or CHATBOT_SITE_KNOWLEDGE=false).")
            return
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\nSite answers ({len(answers)}) with the live engine, threshold {engine.THRESHOLD:.2f}"))
        totals = {}
        misses = []
        for answer in answers:
            name = answer.label.split(": ", 1)[-1]
            if answer.kind == "list":
                probes = [("it", "potete dirmi cosa monitorate" if answer.key == "list:topics" else "che prodotti offrite")]
            elif answer.kind == "faq":
                probes = [("it", answer.questions[0])]
            else:
                probes = [("it", f"mi parli di {name}"), ("it", f"{name} informazioni")]
                probes += [(lang, title) for lang, title in answer.titles.items()
                           if lang != "it" and title and title != answer.titles.get("it")]
            for language, probe in probes:
                _, meta = engine.answer_with_scores(probe)
                own = meta.get("answer_key") == answer.key
                # A hand-written entry answering instead is by design (they win).
                by_entry = not meta["used_fallback"] and meta.get("entry_id") and not meta.get("source")
                kind = totals.setdefault(answer.kind, [0, 0, 0])
                kind[0] += own
                kind[1] += bool(by_entry)
                kind[2] += 1
                if not own and not by_entry:
                    got = meta.get("source") or "fallback"
                    misses.append(f"  · [{language}] \"{probe}\" → {got} (expected {answer.label}, score {meta['best_score']})")
        for kind, (good, by_entry, total) in sorted(totals.items()):
            extra = f", {by_entry} by a hand-written entry" if by_entry else ""
            self.stdout.write(f"  {kind:<9} {good}/{total} found itself ({good / total:.0%}){extra}")
        if misses:
            self.stdout.write("  Not found (add these phrasings to a Voce chatbot, or improve the page's title/description):")
            for line in misses[:15]:
                self.stdout.write(line)
