import os
import re
from pathlib import Path

import numpy as np
from django.conf import settings
from django.db.models import Max

from .models import ChatbotEntry

# The model is fetched once at deploy time (manage.py setup_chatbot_model)
# into models/chatbot/; it used to be downloaded on the first question into
# /tmp, which is wiped at reboot and fails when Hugging Face is unreachable.
os.environ.setdefault("HF_HOME", str(Path(settings.BASE_DIR) / "models" / "hf"))


def chatbot_model_path(name: str) -> Path:
    return Path(getattr(settings, "CHATBOT_MODEL_DIR", "") or Path(settings.BASE_DIR) / "models" / "chatbot") / name.replace("/", "__")


class ChatbotEngine:
    THRESHOLD = float(os.environ.get("CHATBOT_THRESHOLD", "0.70"))
    MARGIN = float(os.environ.get("CHATBOT_MARGIN", "0.06"))
    # Multilingual: the answers are written in Italian and visitors ask in
    # Italian, English or French. (The old all-MiniLM-L6-v2 is English-only.)
    MODEL_NAME = os.environ.get("CHATBOT_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

    def __init__(self):
        self._model = None
        self._embeddings = None
        self._questions = []
        self._answers = []
        self._entry_ids = []
        self._fallback = ""
        self._fallback_id = None
        self._loaded_kb_version = None

    @staticmethod
    def _normalize_text(value: str) -> str:
        if value is None:
            return ""
        text = value.lower()
        # Letters of any language (French ê, ï, œ... included), digits, spaces.
        text = re.sub(r"[^\w\s]+|_", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _ensure_loaded(self):
        latest = ChatbotEntry.objects.aggregate(latest=Max("updated_at"))["latest"]

        if self._model is not None and latest == self._loaded_kb_version:
            return
        if self._model is None:
            print("[Chatbot] Initializing model...")
            from sentence_transformers import SentenceTransformer

            local = chatbot_model_path(self.MODEL_NAME)
            source = str(local) if (local / "modules.json").exists() else self.MODEL_NAME
            self._model = SentenceTransformer(source, device="cpu")

        print("[Chatbot] (Re)building embedding index from ChatbotEntry...")
        existing_fallback = self._fallback
        self._questions = []
        self._answers = []
        self._entry_ids = []
        self._fallback = ""
        self._fallback_id = None

        for entry in ChatbotEntry.objects.all():
            if entry.is_fallback:
                self._fallback = entry.answer.strip()
                self._fallback_id = entry.pk
                continue
            for q in entry.questions_list:
                normalized = self._normalize_text(q)
                if not normalized:
                    continue
                self._questions.append(normalized)
                self._answers.append(entry.answer)
                self._entry_ids.append(entry.pk)

        if not self._questions:
            self._embeddings = None
            self._loaded_kb_version = latest
            self._fallback = self._fallback or existing_fallback
            print("[Chatbot] No ChatbotEntry rows found - run `manage.py seed_chatbot_kb`.")
            return

        self._embeddings = self._model.encode(
            self._questions,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self._loaded_kb_version = latest
        print(f"[Chatbot] Ready. Indexed {len(self._questions)} questions.")

    def answer(self, query: str) -> str:
        """Best matching pre-written answer, or the fallback.

        Falls back when either guard fails:
          - top score below THRESHOLD (nothing close enough), or
          - top score too near the runner up (nothing stands out).
        """
        text, _ = self.answer_with_scores(query)
        return text

    def answer_with_scores(self, query: str) -> tuple:
        """Same as answer(), plus the numbers behind the decision.

        Used by the chatbot_test management command so THRESHOLD and
        MARGIN can be set from real measurements rather than guesses.
        """
        self._ensure_loaded()

        if not query or not self._normalize_text(query):
            fallback = self._fallback or "Il chatbot non e ancora configurato."
            return fallback, {
                "best_score": 0.0,
                "second_score": 0.0,
                "margin": 0.0,
                "matched_question": None,
                "used_fallback": True,
                "reason": "empty query",
            }

        if self._embeddings is None:
            fallback = self._fallback or "Il chatbot non e ancora configurato."
            return fallback, {
                "best_score": 0.0,
                "second_score": 0.0,
                "margin": 0.0,
                "matched_question": None,
                "used_fallback": True,
                "reason": "knowledge base empty",
            }

        query_vec = self._model.encode(
            [self._normalize_text(query)],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

        scores = self._embeddings @ query_vec
        order = np.argsort(scores)[::-1]

        best_idx = int(order[0])
        best_score = float(scores[best_idx])

        second_idx = None
        for idx in order[1:]:
            if self._answers[int(idx)] != self._answers[best_idx]:
                second_idx = int(idx)
                break

        second_score = float(scores[second_idx]) if second_idx is not None else 0.0
        margin = best_score - second_score

        meta = {
            "best_score": round(best_score, 4),
            "second_score": round(second_score, 4),
            "margin": round(margin, 4),
            "matched_question": self._questions[best_idx],
            "entry_id": self._entry_ids[best_idx],
            "used_fallback": False,
            "reason": "",
        }

        if best_score < self.THRESHOLD:
            meta["used_fallback"] = True
            meta["reason"] = "below THRESHOLD"
            meta["entry_id"] = self._fallback_id
            return self._fallback, meta

        if margin < self.MARGIN:
            meta["used_fallback"] = True
            meta["reason"] = "margin too small"
            meta["entry_id"] = self._fallback_id
            return self._fallback, meta

        return self._answers[best_idx], meta


engine = ChatbotEngine()