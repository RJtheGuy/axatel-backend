"""
Self-hosted machine translation, Italian → English / French.

Models: Helsinki-NLP Opus-MT (opus-mt-it-en, opus-mt-it-fr; CC-BY 4.0),
converted once to CTranslate2 int8 by `manage.py setup_translation_models`
into TRANSLATION_MODEL_DIR. They run on the server's CPU; nothing is sent
to an outside service.

Translator adds what the raw model lacks:
  - sentence splitting (the model works sentence by sentence);
  - protected terms (product names) kept exactly as written;
  - translation memory: each text is translated once; corrections win.
"""
import hashlib
import os
import time
from pathlib import Path

from django.conf import settings

from . import text as T

DEFAULT_TERMS = [
    "Axatel", "Angel BPM", "Angel River", "Angel Road Site", "Angel Bridge", "Geo Angel", "GeoAngel",
    "Traffic Alert", "Cerere Pro Aria", "LoRaWAN", "LoRa", "SCADA", "PLC", "IoT", "Smart Road", "Smart City",
]


def model_dir() -> Path:
    return Path(getattr(settings, "TRANSLATION_MODEL_DIR", "") or Path(settings.BASE_DIR) / "models" / "mt")


class CTranslate2Backend:
    """Opus-MT through CTranslate2 (fast int8 inference on CPU)."""

    def __init__(self, language: str):
        # Everything is on disk: never reach out to Hugging Face at run time.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        import ctranslate2
        from transformers import AutoTokenizer

        path = model_dir() / f"opus-mt-it-{language}"
        if not (path / "model.bin").exists():
            raise RuntimeError(f"Translation model missing: {path}. Run manage.py setup_translation_models.")
        threads = int(os.environ.get("TRANSLATION_THREADS", "2"))
        self.name = path.name
        self.tokenizer = AutoTokenizer.from_pretrained(str(path))
        self.model = ctranslate2.Translator(str(path), device="cpu", compute_type="int8",
                                            inter_threads=1, intra_threads=threads)

    def translate(self, sentences: list[str]) -> list[str]:
        if not sentences:
            return []
        tokens = [self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(s)) for s in sentences]
        results = self.model.translate_batch(tokens, beam_size=4, max_batch_size=16, max_decoding_length=400)
        return [
            self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(r.hypotheses[0]), skip_special_tokens=True)
            for r in results
        ]


class EchoBackend:
    """Stand-in for tests: marks the text instead of translating it."""

    def __init__(self, language: str):
        self.name = f"echo-{language}"
        self.language = language

    def translate(self, sentences: list[str]) -> list[str]:
        return [f"[{self.language}] {s}" for s in sentences]


def protected_terms() -> list[str]:
    terms = list(DEFAULT_TERMS)
    try:
        from .models import ProtectedTerm
        terms += list(ProtectedTerm.objects.values_list("term", flat=True))
        from products.models import ProductPage
        terms += list(ProductPage.objects.filter(locale__language_code="it").values_list("title", flat=True))
    except Exception:
        pass
    return sorted({t.strip() for t in terms if t and t.strip()}, key=len, reverse=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Translator:
    def __init__(self, language: str, backend=None, memory: bool = True, terms: list[str] | None = None):
        self.language = language
        self.backend = backend or (EchoBackend(language) if os.environ.get("TRANSLATION_BACKEND") == "echo"
                                   else CTranslate2Backend(language))
        self.memory = memory
        self.terms = protected_terms() if terms is None else terms
        self.cache: dict[str, str] = {}
        self.stats = {"texts": 0, "from_memory": 0, "sentences": 0, "characters": 0, "seconds": 0.0, "protected": 0}

    # -- public ------------------------------------------------------------
    def translate(self, texts: list[str]) -> list[str]:
        """Translate many texts at once (batched); same order as given."""
        wanted = [t for t in dict.fromkeys(texts) if t not in self.cache]
        if wanted:
            self._fill(wanted)
        return [self.cache.get(t, t) for t in texts]

    def one(self, text: str) -> str:
        if text not in self.cache:
            self._fill([text])
        return self.cache.get(text, text)

    # -- internals ---------------------------------------------------------
    def _fill(self, texts: list[str]):
        from .models import TranslationMemory

        todo = []
        for text in texts:
            if not T.needs_translation(text) or text.strip() in self.terms:
                self.cache[text] = text
            else:
                todo.append(text)
        if not todo:
            return
        self.stats["texts"] += len(todo)

        if self.memory:
            hashes = {_hash(t): t for t in todo}
            for row in TranslationMemory.objects.filter(language=self.language, source_hash__in=list(hashes)):
                source = hashes.get(row.source_hash)
                if source is not None and (row.edited or row.engine == self.backend.name):
                    self.cache[source] = row.target
                    self.stats["from_memory"] += 1
            todo = [t for t in todo if t not in self.cache]
        if not todo:
            return

        # Split into sentences, translate all of them in one batch.
        pieces = [T.split_sentences(t) or [t] for t in todo]
        flat = [s for group in pieces for s in group]
        started = time.perf_counter()
        plain = self.backend.translate(flat)

        # Product names changed by the model? Translate those sentences again
        # with the names shielded by placeholders.
        retry = [i for i, (src, out) in enumerate(zip(flat, plain))
                 if any(term not in out for term in T.terms_in(src, self.terms))]
        if retry:
            shielded = [T.protect(flat[i], self.terms) for i in retry]
            again = self.backend.translate([s for s, _ in shielded])
            for i, (_, mapping), out in zip(retry, shielded, again):
                restored = T.restore(out, mapping)
                if restored is not None:
                    plain[i] = restored
                    self.stats["protected"] += 1
        self.stats["seconds"] += time.perf_counter() - started
        self.stats["sentences"] += len(flat)
        self.stats["characters"] += sum(len(s) for s in flat)

        position = 0
        rows = []
        for text, group in zip(todo, pieces):
            translated = " ".join(plain[position: position + len(group)]).strip()
            position += len(group)
            self.cache[text] = translated
            if self.memory:
                rows.append((text, translated))
        for source, target in rows:
            key = _hash(source)
            # A row corrected by hand is never overwritten.
            if TranslationMemory.objects.filter(source_hash=key, language=self.language, edited=True).exists():
                continue
            TranslationMemory.objects.update_or_create(
                source_hash=key, language=self.language,
                defaults={"source": source, "target": target, "engine": self.backend.name},
            )
