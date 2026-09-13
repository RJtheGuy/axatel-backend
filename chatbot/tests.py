from django.core.exceptions import ValidationError
from django.test import TestCase

from chatbot.engine import ChatbotEngine
from chatbot.models import ChatbotEntry


class ChatbotValidationTests(TestCase):
    def test_chatbot_entry_requires_questions(self):
        entry = ChatbotEntry(questions="   ", answer="Risposta di prova")

        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_chatbot_entry_requires_answer(self):
        entry = ChatbotEntry(questions="Come posso contattarvi?", answer="   ")

        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_engine_normalizes_input_before_matching(self):
        normalized = ChatbotEngine._normalize_text("  Ciao!!! Come stai?  ")
        self.assertEqual(normalized, "ciao come stai")

    def test_engine_uses_fallback_when_kb_is_empty(self):
        engine = ChatbotEngine()
        engine._embeddings = None
        engine._fallback = "Risposta di riserva"

        result = engine.answer("domanda generica")

        self.assertEqual(result, "Risposta di riserva")
