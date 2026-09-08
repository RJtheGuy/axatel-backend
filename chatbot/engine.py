import os

import numpy as np

# Ensure HuggingFace cache directory is writable by non-root users
os.environ["HF_HOME"] = "/tmp/huggingface"


from django.db.models import Max

from .models import ChatbotEntry



class ChatbotEngine:
    
    THRESHOLD = float(os.environ.get("CHATBOT_THRESHOLD", "0.70"))
    MARGIN = float(os.environ.get("CHATBOT_MARGIN", "0.06"))
    MODEL_NAME = os.environ.get("CHATBOT_MODEL", "all-MiniLM-L6-v2")

    def __init__(self):
        self._model = None
        self._embeddings = None
        self._questions = []
        self._answers = []
        self._fallback = ""
        self._loaded_kb_version = None

    def _ensure_loaded(self):
        
        latest = ChatbotEntry.objects.aggregate(latest=Max("updated_at"))["latest"]

        if self._model is not None and latest == self._loaded_kb_version:
            return  
        if self._model is None:
            print("[Chatbot] Initializing model...")
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.MODEL_NAME, device="cpu")

        print("[Chatbot] (Re)building embedding index from ChatbotEntry...")
        self._questions = []
        self._answers = []
        self._fallback = ""

        for entry in ChatbotEntry.objects.all():
            if entry.is_fallback:
                self._fallback = entry.answer
                continue
            for q in entry.questions_list:
                self._questions.append(q)
                self._answers.append(entry.answer)

        if not self._questions:
            self._embeddings = None
            self._loaded_kb_version = latest
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

        if self._embeddings is None:
            return self._fallback or "Il chatbot non e ancora configurato.", {
                "best_score": 0.0, "second_score": 0.0, "margin": 0.0,
                "matched_question": None, "used_fallback": True,
                "reason": "knowledge base empty",
            }

        query_vec = self._model.encode(
            [query],
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
            "used_fallback": False,
            "reason": "",
        }

        if best_score < self.THRESHOLD:
            meta["used_fallback"] = True
            meta["reason"] = "below THRESHOLD"
            return self._fallback, meta

        if margin < self.MARGIN:
            meta["used_fallback"] = True
            meta["reason"] = "margin too small"
            return self._fallback, meta

        return self._answers[best_idx], meta

engine = ChatbotEngine()