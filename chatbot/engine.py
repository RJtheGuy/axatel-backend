"""
The chatbot's matching engine. It never writes text: it finds the answer
whose example questions mean the same as the visitor's question.

Two kinds of answers are indexed together:
  - entries written by hand in Snippets → Voci chatbot (they always win);
  - answers built from the published site (chatbot/site_knowledge.py):
    monitoring topics, products, solutions, success stories, glossary terms,
    FAQ blocks, and the lists "cosa monitorate?" / "quali prodotti avete?".

The index is rebuilt when an entry is saved or, checked at most once a
minute, when a page is published or unpublished. Questions already embedded
are kept, so a rebuild only encodes what is new.
"""
import os
import re
import time
from pathlib import Path

import numpy as np
from django.conf import settings
from django.db.models import Max

from .models import ChatbotEntry
from .understanding import Vocabulary, classify, words

# The model is fetched once at deploy time (manage.py setup_chatbot_model)
# into models/chatbot/; it used to be downloaded on the first question into
# /tmp, which is wiped at reboot and fails when Hugging Face is unreachable.
os.environ.setdefault("HF_HOME", str(Path(settings.BASE_DIR) / "models" / "hf"))


def chatbot_model_path(name: str) -> Path:
    return Path(getattr(settings, "CHATBOT_MODEL_DIR", "") or Path(settings.BASE_DIR) / "models" / "chatbot") / name.replace("/", "__")


class _HashEncoder:
    """Stand-in for tests (CHATBOT_MODEL=hash): character 3-grams hashed into
    a vector. No download; good enough to check the logic, not for visitors."""

    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False):
        out = np.zeros((len(texts), 2048), dtype=np.float32)
        for row, text in enumerate(texts):
            padded = f"  {text}  "
            for i in range(len(padded) - 2):
                out[row, hash(padded[i:i + 3]) % 2048] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.where(norms == 0, 1, norms)


class ManualAnswer:
    """An entry of Voci chatbot, as the engine sees it."""

    def __init__(self, entry):
        self.key = f"entry:{entry.pk}"
        self.entry_id = entry.pk
        self.kind = "entry"
        self.label = str(entry)
        self.link = ""
        self._entry = entry

    def answer_in(self, language):
        return self._entry.answer_in(language)


class ChatbotEngine:
    THRESHOLD = float(os.environ.get("CHATBOT_THRESHOLD", "0.70"))
    MARGIN = float(os.environ.get("CHATBOT_MARGIN", "0.06"))
    # A site answer must beat a clear hand-written one by this much to be used.
    MANUAL_PRIORITY = float(os.environ.get("CHATBOT_MANUAL_PRIORITY", "0.05"))
    SITE_KNOWLEDGE = os.environ.get("CHATBOT_SITE_KNOWLEDGE", "true").lower() not in ("0", "false", "no")
    SITE_CHECK_SECONDS = 60
    # Multilingual: the answers are written in Italian and visitors ask in
    # Italian, English or French. (The old all-MiniLM-L6-v2 is English-only.)
    MODEL_NAME = os.environ.get("CHATBOT_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

    def __init__(self):
        self._model = None
        self._embeddings = None
        self._questions = []      # normalised text, one per indexed question
        self._owners = []         # answer key for each question
        self._manual_mask = None  # True where the question belongs to a hand-written entry
        self._answers = {}        # key → ManualAnswer / SiteAnswer
        self._fallback = ""
        self._fallback_id = None
        self._loaded_version = None
        self._site_version = None
        self._site_checked = 0.0
        self._vectors = {}        # normalised question → embedding (kept across rebuilds)
        self._vocabulary = None   # every word of the questions and answers (understanding.py)
        self._known = set()       # the example questions, as plain words

    @staticmethod
    def _normalize_text(value: str) -> str:
        if value is None:
            return ""
        text = value.lower()
        # Letters of any language (French ê, ï, œ... included), digits, spaces.
        text = re.sub(r"[^\w\s]+|_", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # -- loading -----------------------------------------------------------
    def _load_model(self):
        if self._model is not None:
            return
        if self.MODEL_NAME == "hash":
            self._model = _HashEncoder()
            return
        print("[Chatbot] Initializing model...")
        from sentence_transformers import SentenceTransformer

        local = chatbot_model_path(self.MODEL_NAME)
        source = str(local) if (local / "modules.json").exists() else self.MODEL_NAME
        self._model = SentenceTransformer(source, device="cpu")

    def _site_signature(self):
        if not self.SITE_KNOWLEDGE:
            return None
        now = time.monotonic()
        if self._site_version is not None and now - self._site_checked < self.SITE_CHECK_SECONDS:
            return self._site_version
        self._site_checked = now
        try:
            from .site_knowledge import signature
            self._site_version = signature()
        except Exception as error:  # noqa: BLE001 - the hand-written entries still work
            print(f"[Chatbot] Site knowledge unavailable: {error}")
            self._site_version = None
        return self._site_version

    def _ensure_loaded(self):
        latest = ChatbotEntry.objects.aggregate(latest=Max("updated_at"))["latest"]
        version = (latest, self._site_signature())
        if self._model is not None and version == self._loaded_version:
            return
        self._load_model()
        self._rebuild()
        self._loaded_version = version

    def _rebuild(self):
        existing_fallback = self._fallback
        questions, owners, manual, answers = [], [], [], {}
        self._fallback, self._fallback_id = "", None

        def add(answer, texts, is_manual):
            seen = set()
            for text in texts:
                normalized = self._normalize_text(text)
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                questions.append(normalized)
                owners.append(answer.key)
                manual.append(is_manual)
            answers[answer.key] = answer

        for entry in ChatbotEntry.objects.all():
            if entry.is_fallback:
                self._fallback = entry.answer.strip()
                self._fallback_id = entry.pk
                continue
            add(ManualAnswer(entry), entry.questions_list, True)

        site_count = 0
        if self.SITE_KNOWLEDGE:
            try:
                from .site_knowledge import build
                for answer in build():
                    add(answer, answer.questions, False)
                    site_count += 1
            except Exception as error:  # noqa: BLE001
                print(f"[Chatbot] Site knowledge skipped: {error}")

        self._questions, self._owners, self._answers = questions, owners, answers
        # What the chatbot can talk about, in all three languages: used to
        # recognise "uff", "boh" or "asdfgh" before any matching.
        texts = list(questions)
        for answer in answers.values():
            texts.append(answer.label)
            for language in ("it", "en", "fr"):
                texts.append(answer.answer_in(language))
            texts += list(getattr(answer, "titles", {}).values()) + list(getattr(answer, "labels", {}).values())
        self._vocabulary = Vocabulary(texts)
        self._known = {" ".join(words(q)) for q in questions}
        self._manual_mask = np.array(manual, dtype=bool)
        if not questions:
            self._embeddings = None
            self._fallback = self._fallback or existing_fallback
            print("[Chatbot] No ChatbotEntry rows found - run `manage.py seed_chatbot_kb`.")
            return

        missing = [q for q in dict.fromkeys(questions) if q not in self._vectors]
        if missing:
            vectors = self._model.encode(missing, convert_to_numpy=True, normalize_embeddings=True,
                                         show_progress_bar=False)
            self._vectors.update(zip(missing, vectors))
        self._embeddings = np.array([self._vectors[q] for q in questions])
        print(f"[Chatbot] Ready. Indexed {len(questions)} questions "
              f"({int(self._manual_mask.sum())} written by hand, {site_count} answers from the site).")

    # -- answering -----------------------------------------------------------
    def answer(self, query: str) -> str:
        """Best matching answer text (Italian), or the fallback."""
        text, meta = self.answer_with_scores(query)
        if meta.get("special"):
            from .understanding import REPLIES
            return REPLIES[meta["special"]]["it"]
        return text

    def get_answer(self, key):
        """The ManualAnswer / SiteAnswer behind meta['answer_key']."""
        return self._answers.get(key)

    def _best(self, scores, mask):
        """(best index, its score, margin to the best other answer) within mask."""
        candidates = np.where(mask)[0]
        if not len(candidates):
            return None, 0.0, 0.0
        order = candidates[np.argsort(scores[candidates])[::-1]]
        best = int(order[0])
        second = next((int(i) for i in order[1:] if self._owners[i] != self._owners[best]), None)
        best_score = float(scores[best])
        return best, best_score, best_score - (float(scores[second]) if second is not None else 0.0)

    def answer_with_scores(self, query: str) -> tuple:
        """Same as answer(), plus the numbers behind the decision.

        Used by chatbot_test / evaluate_chatbot so THRESHOLD and MARGIN can
        be set from real measurements rather than guesses.
        """
        self._ensure_loaded()

        def fallback(reason, best=0.0, margin=0.0, matched=None):
            return self._fallback or "Il chatbot non e ancora configurato.", {
                "best_score": round(best, 4), "second_score": round(best - margin, 4), "margin": round(margin, 4),
                "matched_question": matched, "used_fallback": True, "reason": reason,
                "entry_id": self._fallback_id, "answer_key": None, "source": "", "link": "",
            }

        if not (query or "").strip():
            return fallback("empty query")
        if self._embeddings is None:
            return fallback("knowledge base empty")

        # "uff", "ok", "asdfgh", "?!?", "ciao", "grazie": no matching (understanding.py).
        kind = classify(query, self._vocabulary, self._known)
        if kind:
            return "", {
                "best_score": 0.0, "second_score": 0.0, "margin": 0.0, "matched_question": None,
                "used_fallback": kind == "unclear", "reason": kind, "special": kind,
                "entry_id": None, "answer_key": None, "source": "", "link": "",
            }

        vector = self._model.encode([self._normalize_text(query)], convert_to_numpy=True,
                                    normalize_embeddings=True, show_progress_bar=False)[0]
        scores = self._embeddings @ vector

        m_idx, m_score, m_margin = self._best(scores, self._manual_mask)
        s_idx, s_score, s_margin = self._best(scores, ~self._manual_mask)
        manual_clear = m_idx is not None and m_score >= self.THRESHOLD and m_margin >= self.MARGIN
        site_clear = s_idx is not None and s_score >= self.THRESHOLD and s_margin >= self.MARGIN

        # Hand-written entries win unless a site answer is clearly closer.
        if manual_clear and not (site_clear and s_score > m_score + self.MANUAL_PRIORITY):
            chosen, score, margin = m_idx, m_score, m_margin
        elif site_clear:
            chosen, score, margin = s_idx, s_score, s_margin
        else:
            top, top_score, top_margin = max(
                [(m_idx, m_score, m_margin), (s_idx, s_score, s_margin)], key=lambda t: t[1])
            matched = self._questions[top] if top is not None else None
            reason = "below THRESHOLD" if top_score < self.THRESHOLD else "margin too small"
            return fallback(reason, top_score, top_margin, matched)

        answer = self._answers[self._owners[chosen]]
        return answer.answer_in("it"), {
            "best_score": round(score, 4), "second_score": round(score - margin, 4), "margin": round(margin, 4),
            "matched_question": self._questions[chosen], "used_fallback": False, "reason": "",
            "entry_id": getattr(answer, "entry_id", None), "answer_key": answer.key,
            "source": "" if answer.kind == "entry" else answer.label, "link": answer.link,
        }

    def site_answers(self):
        """The answers built from the site (for evaluate_chatbot)."""
        self._ensure_loaded()
        return [a for a in self._answers.values() if a.kind != "entry"]


engine = ChatbotEngine()
