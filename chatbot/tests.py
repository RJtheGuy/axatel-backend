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


class ConversationTests(TestCase):
    """chatbot/engine.py respond(): page text, "dimmi di più", follow-ups,
    "Intendi A o B?", buttons. Uses the hash stand-in for the language model."""

    @classmethod
    def setUpTestData(cls):
        import json

        from wagtail.models import Page

        from monitoring.models import MonitoringPage

        root = Page.get_first_root_node()
        body = json.dumps([
            {"type": "rich_text", "value": {"text": (
                "<h2>Rilevazione e risposta</h2><p>Sensori georeferenziati rilevano i movimenti del terreno; "
                "accelerometri installati su reti paramassi estendono il controllo ai punti critici.</p>"
                "<h2>Supervisione centralizzata</h2><p>Il portale web visualizza dati, grafici e andamenti su "
                "mappe cartografiche e permette di impostare soglie di allarme.</p>"
                "<h2>Stazione meteo</h2><p>La stazione meteo locale correla vento, pioggia, temperatura e "
                "umidità con le misure del dissesto del versante.</p>")}},
            {"type": "cta", "value": {"title": "Parla con un esperto", "text": "Contattaci per un sopralluogo gratuito."}},
        ])
        cls.page = root.add_child(instance=MonitoringPage(
            title="Monitoraggio frane", slug="frane",
            short_description="Il monitoraggio dei versanti instabili rende osservabili i fenomeni di dissesto.",
            body=body,
        ))
        ChatbotEntry.objects.create(questions="Che orari avete?", answer="Dal lunedì al venerdì, 8-18.")
        ChatbotEntry.objects.create(questions="Non lo so", answer="Risposta di riserva.", is_fallback=True)

    def setUp(self):
        from chatbot.engine import ChatbotEngine

        self.engine = ChatbotEngine()
        self.engine.MODEL_NAME = "hash"
        self.engine.ENCODE_BUDGET = 1000

    def ask(self, question, context=None, **kwargs):
        return self.engine.respond(question, "it", context=context, **kwargs)

    def test_passages_follow_headings_and_skip_buttons(self):
        from chatbot.passages import build

        passages = [p for p in build() if p.page_id == self.page.pk]
        headings = [p.heading for p in passages]
        self.assertIn("Rilevazione e risposta", headings)
        self.assertIn("Stazione meteo", headings)
        self.assertFalse(any("sopralluogo" in p.text for p in passages))  # call to action left out

    def test_page_answer_then_more_until_the_end(self):
        reply = self.ask("monitorate le frane?")
        self.assertEqual(reply["kind"], "page")
        self.assertEqual(reply["answer_key"], f"topic:{self.page.pk}")
        self.assertTrue(reply["link"])
        self.assertIn("more", [c["type"] for c in reply["chips"]])

        seen_texts, context = {reply["text"]}, reply["context"]
        for _ in range(5):
            reply = self.ask("dimmi di più", context)
            self.assertEqual(reply["kind"], "more")
            if not any(c["type"] == "more" for c in reply["chips"]):
                break
            self.assertNotIn(reply["text"], seen_texts)
            seen_texts.add(reply["text"])
            context = reply["context"]
        last = self.ask("dimmi di più", reply["context"])
        self.assertIn("ti ho detto", last["text"])
        self.assertIn("contact", [c["type"] for c in last["chips"]])

    def test_price_in_context_offers_contact(self):
        first = self.ask("monitorate le frane?")
        reply = self.ask("quanto costa?", first["context"])
        self.assertEqual(reply["answer_key"] or reply["context"]["key"], f"topic:{self.page.pk}")
        self.assertIn("contact", [c["type"] for c in reply["chips"]])

    def test_follow_up_uses_the_page_being_discussed(self):
        self.engine.CONTEXT_MIN = 0.0
        first = self.ask("monitorate le frane?")
        reply = self.ask("e la stazione meteo?", first["context"])
        self.assertIn(reply["kind"], ("context", "page"))
        self.assertIn("stazione meteo", reply["text"].lower())

    def test_key_gives_exactly_that_answer(self):
        reply = self.ask("qualsiasi cosa", key=f"topic:{self.page.pk}")
        self.assertEqual(reply["answer_key"], f"topic:{self.page.pk}")

    def test_two_equal_answers_ask_which_one(self):
        ChatbotEntry.objects.create(questions="servizio di assistenza tecnica", answer="Risposta A")
        ChatbotEntry.objects.create(questions="servizio di assistenza tecnica.", answer="Risposta B")
        engine = self.engine
        engine.CLARIFY_MIN = 0.0
        engine.PASSAGE_MIN = 2.0
        reply = engine.respond("servizio di assistenza tecnica", "it")
        self.assertEqual(reply["kind"], "clarify")
        self.assertGreaterEqual(len([c for c in reply["chips"] if c.get("key")]), 2)

    def test_inactive_entry_is_not_used(self):
        entry = ChatbotEntry.objects.get(questions="Che orari avete?")
        self.assertEqual(self.ask("Che orari avete?")["answer_key"], f"entry:{entry.pk}")
        entry.active = False
        entry.save()
        self.assertNotEqual(self.ask("Che orari avete?")["answer_key"], f"entry:{entry.pk}")

    def test_answers_about_the_same_page_are_not_rivals(self):
        entry = ChatbotEntry.objects.create(questions="Monitorate le frane?", answer="Sì, con Geo Angel.")
        reply = self.ask("monitorate le frane?")
        self.assertEqual(reply["answer_key"], f"entry:{entry.pk}")
        self.assertTrue(reply["link"])
        self.assertIn("more", [c["type"] for c in reply["chips"]])

    def test_topic_list_uses_the_written_category(self):
        MonitoringPage = type(self.page)
        page = MonitoringPage.objects.get(pk=self.page.pk)
        page.category = "Dissesti geologici e frane"
        page.save_revision().publish()
        self.engine.warm_up()
        text = self.engine.get_answer("list:topics").answer_in("it")
        self.assertIn("Frane (dissesti geologici e frane)", text)

    def test_more_words(self):
        from chatbot.conversation import is_more

        for text in ["Dimmi di più", "dimmi di piu!", "altro?", "più dettagli", "tell me more", "Dites-m'en plus"]:
            self.assertTrue(is_more(text), text)
        for text in ["dimmi dove siete", "più sensori costano di più?"]:
            self.assertFalse(is_more(text), text)


class ChatViewTests(TestCase):
    def setUp(self):
        ChatbotEntry.objects.create(questions="Dove siete?\nDove si trova la sede?", answer="A Vicenza.")
        ChatbotEntry.objects.create(questions="Non lo so", answer="Riserva.", answer_en="Fallback.", is_fallback=True)

    def post(self, body):
        import json

        return self.client.post("/api/v2/chatbot/ask/", json.dumps(body), content_type="application/json")

    def test_answer_carries_context_and_is_logged(self):
        from chatbot.models import ChatbotQuestion

        data = self.post({"message": "Dove siete?", "locale": "it"}).json()
        self.assertEqual(data["response"], "A Vicenza.")
        self.assertTrue(data["context"]["key"].startswith("entry:"))
        logged = ChatbotQuestion.objects.get()
        self.assertEqual(logged.kind, "entry")
        self.assertTrue(logged.answered)

    def test_fallback_in_english_with_contact_button(self):
        data = self.post({"message": "quanto pesa la luna in grammi esattamente", "locale": "en"}).json()
        self.assertEqual(data["response"], "Fallback.")
        contact = [c for c in data["chips"] if c["type"] == "contact"]
        self.assertEqual(contact[0]["link"], "/contatti")


class ChatbotAdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_superuser("admin", "a@example.com", "pw")
        self.client.force_login(user)
        ChatbotEntry.objects.create(questions="Dove siete?", answer="A Vicenza.")

    def test_test_page_answers(self):
        response = self.client.post("/cms/chatbot/prova/", {"question": "Dove siete?", "language": "it"})
        self.assertContains(response, "A Vicenza.")
        self.assertContains(response, "Voce chatbot")

    def test_create_answer_is_prefilled(self):
        from django.urls import reverse

        url = reverse("wagtailsnippets_chatbot_chatbotentry:add") + "?domanda=Avete%20un%20listino%3F"
        self.assertContains(self.client.get(url), "Avete un listino?")
