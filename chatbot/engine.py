# import os
# import numpy as np

# # Ensure HuggingFace cache directory is writable by non-root users
# os.environ["HF_HOME"] = "/tmp/huggingface"

# from sentence_transformers import SentenceTransformer

# KNOWLEDGE_BASE = [
#     {
#         "questions": [
#             "cos'\u00e8 Axatel", "chi \u00e8 Axatel", "cosa fa Axatel",
#             "di cosa vi occupate", "parlami di Axatel",
#             "what is Axatel", "what does Axatel do", "tell me about Axatel",
#         ],
#         "answer": (
#             "Axatel \u00e8 un'azienda di innovazione tecnologica con sede a Vicenza, "
#             "attiva dal 2012 nell'automazione stradale e nell'Internet of Things. "
#             "Progettiamo sistemi di monitoraggio e supervisione \u2014 dai sensori sul "
#             "campo fino alla control room \u2014 per pubbliche amministrazioni, "
#             "concessionarie stradali e aziende di manutenzione impianti."
#         ),
#     },
#     {
#         "questions": [
#             "dove siete", "dove si trova Axatel", "indirizzo", "sede",
#             "come vi raggiungo", "where are you located", "address",
#         ],
#         "answer": (
#             "La sede di Axatel \u00e8 in Viale del Mercato Nuovo, 75, "
#             "36100 Vicenza (VI), Italia."
#         ),
#     },
#     {
#         "questions": [
#             "come vi contatto", "numero di telefono", "email",
#             "come posso scrivervi", "contatti", "how do I contact you",
#             "phone number", "contact email",
#         ],
#         "answer": (
#             "Puoi contattarci al numero +39 0444 96 38 91 oppure via email "
#             "a info@axatel.it. Siamo anche su LinkedIn."
#         ),
#     },
#     {
#         "questions": [
#             "cos'\u00e8 IoT", "cosa fate con l'IoT", "internet of things",
#             "sensori e connettivit\u00e0", "what is your IoT offering",
#         ],
#         "answer": (
#             "Axatel sviluppa e gestisce l'intera filiera tecnologica per i "
#             "servizi IoT: gateway, network server, middleware e sensori. "
#             "Progettiamo e realizziamo soluzioni per persone, aziende e citt\u00e0, "
#             "dal singolo sensore fino alla piattaforma di gestione dei dati."
#         ),
#     },
#     {
#         "questions": [
#             "cos'\u00e8 smart road", "monitoraggio stradale", "sicurezza strade",
#             "sensori su strade e autostrade", "what is smart road",
#         ],
#         "answer": (
#             "Smart Road \u00e8 la nostra soluzione di monitoraggio su strade e "
#             "autostrade per la sicurezza della viabilit\u00e0 \u2014 rilevamento di "
#             "frane, allagamenti, condizioni del manto stradale e traffico, "
#             "con allerta in tempo reale verso la control room."
#         ),
#     },
#     {
#         "questions": [
#             "cos'\u00e8 smart city", "soluzioni per le citt\u00e0",
#             "monitoraggio urbano", "what is smart city",
#         ],
#         "answer": (
#             "Smart City comprende le nostre soluzioni IoT progettate per le "
#             "esigenze delle citt\u00e0 \u2014 monitoraggio ambientale, gestione degli "
#             "impianti pubblici e sistemi di supervisione integrati per la "
#             "pubblica amministrazione."
#         ),
#     },
#     {
#         "questions": [
#             "supervisione e controllo", "control room", "cosa fate in ingegneria",
#             "impianti di automazione", "what does supervisione e controllo mean",
#         ],
#         "answer": (
#             "Progettiamo impianti di automazione personalizzati in base alle "
#             "esigenze dell'opera da monitorare \u2014 dalla raccolta dati dei "
#             "sensori fino alla control room, dove gli operatori supervisionano "
#             "e gestiscono gli allarmi in tempo reale."
#         ),
#     },
#     {
#         "questions": [
#             "servizi di ingegneria", "ingegneria integrata",
#             "what engineering services do you offer",
#         ],
#         "answer": (
#             "Offriamo ingegneria integrata end-to-end: dalla progettazione alla "
#             "realizzazione, con l'obiettivo di ridurre le problematiche e i "
#             "costi di gestione per il cliente lungo tutto il ciclo di vita "
#             "dell'impianto."
#         ),
#     },
#     {
#         "questions": [
#             "sviluppo elettronico", "progettate hardware",
#             "sviluppate elettronica conto terzi", "electronics development",
#         ],
#         "answer": (
#             "Sviluppiamo internamente \u2014 e anche conto terzi \u2014 le nostre "
#             "soluzioni elettroniche per il controllo e la comunicazione, "
#             "dai sensori ai gateway di trasmissione."
#         ),
#     },
#     {
#         "questions": [
#             "cos'\u00e8 LoRaWAN", "che tecnologia usate", "trasmissione radio",
#             "what is LoRaWAN", "which technology do you use",
#         ],
#         "answer": (
#             "LoRaWAN \u00e8 la tecnologia di trasmissione radio che utilizziamo "
#             "per le applicazioni outdoor \u2014 a lungo raggio e basso consumo, "
#             "ideale per sensori distribuiti su territori estesi come strade "
#             "e corsi d'acqua."
#         ),
#     },
#     {
#         "questions": [
#             "catalogo sensori", "che sensori avete", "che tipo di sensori",
#             "what sensors do you offer",
#         ],
#         "answer": (
#             "Sviluppiamo e realizziamo internamente i sensori per i nostri "
#             "sistemi di supervisione, progettati per applicazioni outdoor in "
#             "condizioni ambientali difficili. Per il catalogo completo, "
#             "scrivici a info@axatel.it."
#         ),
#     },
#     {
#         "questions": [
#             "cos'\u00e8 angel river", "monitoraggio corsi d'acqua",
#             "livelli fiumi", "what is angel river",
#         ],
#         "answer": (
#             "Angel River \u00e8 il nostro sistema per il monitoraggio dei livelli "
#             "dei corsi d'acqua, pensato per pubbliche amministrazioni, "
#             "concessionarie stradali e aziende di manutenzione impianti che "
#             "devono prevenire rischi idrogeologici."
#         ),
#     },
#     {
#         "questions": [
#             "casi di successo", "progetti realizzati", "esempi di progetti",
#             "con chi avete lavorato", "referenze", "case studies",
#         ],
#         "answer": (
#             "Tra i nostri progetti: automazione e monitoraggio sulla SS51 "
#             "Alemagna per la Provincia di Belluno e ANAS, l'apertura della "
#             "Galleria di Caltanissetta sulla SS640 con ANAS, e la partnership "
#             "con TAV (Trans Audio Video) per la distribuzione delle nostre "
#             "soluzioni. L'elenco completo \u00e8 nella sezione Casi di successo "
#             "del sito."
#         ),
#     },
#     {
#         "questions": [
#             "diventa partner", "come diventare partner", "partnership",
#             "collaborazioni", "how do I become a partner",
#         ],
#         "answer": (
#             "Cerchiamo sempre nuovi partner per distribuire ed estendere le "
#             "nostre soluzioni. Scrivici a info@axatel.it indicando la tua "
#             "azienda e l'area di interesse \u2014 trovi anche una pagina dedicata "
#             "\"Diventa partner\" sul sito."
#         ),
#     },
#     {
#         "questions": [
#             "certificazioni", "siete certificati", "ESG", "sostenibilit\u00e0",
#             "are you certified", "sustainability",
#         ],
#         "answer": (
#             "Axatel ha ottenuto lo score \"C \u2014 Satisfactory Level of "
#             "Sustainability\" nell'ambito della certificazione ESG. Lavoriamo "
#             "anche con enti certificatori come IQ Cert, SQS ed ESNA-SOA."
#         ),
#     },
#     {
#         "questions": [
#             "voglio un preventivo", "richiedi informazioni",
#             "come inizio un progetto con voi", "sviluppa il tuo business",
#             "I want a quote", "how do I start a project with you",
#         ],
#         "answer": (
#             "Scrivici a commerciale@axatel.it descrivendo brevemente la tua "
#             "esigenza \u2014 un nostro tecnico ti ricontatter\u00e0 per capire come "
#             "possiamo aiutarti."
#         ),
#     },
#     # \u2500\u2500 FALLBACK \u2014 must be last \u2500\u2500
#     {
#         "questions": ["altro", "qualcos'altro", "non c'entra", "other", "something else"],
#         "answer": (
#             "Posso rispondere solo a domande su Axatel e le nostre soluzioni "
#             "di monitoraggio e IoT. Per qualsiasi altra richiesta, scrivici a "
#             "info@axatel.it."
#         ),
#         "_fallback": True,
#     },
# ]
# class ChatbotEngine:
#     THRESHOLD = 0.42

#     def __init__(self):
#         self._model = None
#         self._embeddings = None
#         self._questions = []
#         self._answers = []
#         self._fallback = ""

#     def _ensure_loaded(self):
#         """
#         Loads the model and builds index lazily on the first request only.
#         Does NOTHING during module import or Django startup.
#         """
#         if self._model is not None:
#             return

#         print("[Chatbot] Initializing model and embedding index...")
#         from sentence_transformers import SentenceTransformer

#         self._model = SentenceTransformer(self.MODEL_NAME, device="cpu")

#         for entry in KNOWLEDGE_BASE:
#             if entry.get("_fallback"):
#                 self._fallback = entry["answer"]
#                 continue
#             for q in entry["questions"]:
#                 self._questions.append(q)
#                 self._answers.append(entry["answer"])

#         self._embeddings = self._model.encode(
#             self._questions,
#             convert_to_numpy=True,
#             normalize_embeddings=True,
#             show_progress_bar=False,
#         )
#         print(f"[Chatbot] Model ready. Indexed {len(self._questions)} questions.")

#     def answer(self, query: str) -> str:
#         # Lazy initialization check
#         self._ensure_loaded()

#         query_vec = self._model.encode(
#             [query],
#             convert_to_numpy=True,
#             normalize_embeddings=True,
#         )[0]

#         scores = self._embeddings @ query_vec
#         best_idx = int(np.argmax(scores))
#         best_score = float(scores[best_idx])

#         if best_score < self.THRESHOLD:
#             return self._fallback

#         return self._answers[best_idx]


# # Singleton instance \u2014 lightweight and harmless at import time
# engine = ChatbotEngine()





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