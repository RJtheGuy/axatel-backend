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


class UnderstandingTests(TestCase):
    """chatbot/understanding.py: nonsense never gets a real-looking answer."""

    def setUp(self):
        from chatbot.understanding import Vocabulary

        self.vocabulary = Vocabulary([
            "dove siete", "La sede di Axatel è a Vicenza", "Monitoraggio frane",
            "Scegliamo e integriamo sensori adatti", "Landslide monitoring", "cos'è LoRaWAN",
        ])
        self.known = {"dove siete", "ai"}

    def kind(self, text):
        from chatbot.understanding import classify

        return classify(text, self.vocabulary, self.known)

    def test_nonsense_is_unclear(self):
        for text in ["uff", "boh", "ok", "mah...", "asdfgh", "qwerty zxcvb", "uff uff uff", "?!?", "123", "xyzzy"]:
            self.assertEqual(self.kind(text), "unclear", text)

    def test_greetings_and_thanks(self):
        self.assertEqual(self.kind("Ciao!"), "greeting")
        self.assertEqual(self.kind("buongiorno"), "greeting")
        self.assertEqual(self.kind("Bonjour"), "greeting")
        self.assertEqual(self.kind("grazie mille"), "thanks")
        self.assertEqual(self.kind("thanks"), "thanks")

    def test_real_questions_are_matched(self):
        for text in ["dove siete", "sede", "sensore", "sensori?", "monitorate le frane?", "LoRaWAN",
                     "landslides", "ciao, avete sensori?", "AI",
                     "quanto costa un impianto di monitoraggio per un ponte?"]:
            self.assertIsNone(self.kind(text), text)

    def test_short_word_is_not_a_prefix_match(self):
        # "uff" must not count as the start of "ufficio".
        from chatbot.understanding import Vocabulary

        self.assertFalse(Vocabulary(["i nostri uffici"]).knows("uff"))
        self.assertTrue(Vocabulary(["i nostri uffici"]).knows("ufficio"))
