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

# IMPORTANT: SentenceTransformer is deliberately NOT imported at module
# level.
#
# This module is reachable from the URLconf:
#     axatel/urls.py \u2192 chatbot.urls \u2192 chatbot.views \u2192 chatbot.engine
# so Django imports it while building the URL resolver \u2014 before handling
# any request, on every request path, including the Wagtail admin.
#
# A top-level `from sentence_transformers import SentenceTransformer`
# pulls in torch (~800MB-1GB RSS) at that moment, in every gunicorn
# worker. With the default 3 workers that is ~3GB before Django has done
# anything, which on a memory-constrained host shows up as:
#     [CRITICAL] WORKER TIMEOUT
#     [ERROR] Worker was sent SIGKILL! Perhaps out of memory?
# and the admin never loads.
#
# The real import lives in ChatbotEngine._ensure_loaded(), so the cost is
# paid once, on the first actual chat request, in one worker only.
#
# KNOWLEDGE_BASE used to be a ~250-line hardcoded list here. It now
# lives in chatbot/models.py (ChatbotEntry, a Wagtail snippet) so an
# editor can change what the chatbot knows from Snippets -> Voci
# chatbot in the CMS, instead of a developer editing this file and
# redeploying. The original list survives as one-time seed data in
# chatbot/kb_seed_data.py (see the seed_chatbot_kb management command).
from django.db.models import Max

from .models import ChatbotEntry



class ChatbotEngine:
    # Minimum cosine similarity for an answer to be used at all.
    #
    # WAS 0.42, which let clearly unrelated questions through: "quanti
    # siete in totale?" returned the ESG certification answer because it
    # scraped past 0.42 against it. Raised so a near miss becomes an
    # honest fallback rather than a confidently wrong answer.
    #
    # Recalibrate with:  manage.py chatbot_test
    THRESHOLD = float(os.environ.get("CHATBOT_THRESHOLD", "0.70"))

    # Minimum gap between the best and second best match.
    #
    # A question matching nothing tends to score mediocre-and-equal
    # against several entries, making the winner close to arbitrary.
    # Requiring the top match to beat the runner up by this margin
    # catches that case, which the threshold alone does not.
    MARGIN = float(os.environ.get("CHATBOT_MARGIN", "0.06"))

    # English only by default. The knowledge base is Italian, which is
    # why similarity scores are compressed and mismatches frequent.
    # paraphrase-multilingual-MiniLM-L12-v2 handles Italian properly;
    # it is ~470MB and needs the thresholds recalibrated, so it is an
    # env var rather than the default.
    MODEL_NAME = os.environ.get("CHATBOT_MODEL", "all-MiniLM-L6-v2")

    def __init__(self):
        self._model = None
        self._embeddings = None
        self._questions = []
        self._answers = []
        self._fallback = ""
        # Timestamp of the ChatbotEntry row that was most recently
        # updated, as of the last time this worker built its index -
        # see _ensure_loaded() below for what this is actually for.
        self._loaded_kb_version = None

    def _ensure_loaded(self):
        """
        Loads the model and (re)builds the index lazily, on the first
        request only - and again, cheaply, whenever the knowledge base
        has changed since this worker last built its index.

        WHY "again, whenever changed": Gunicorn runs several worker
        processes (3 by default - see the note above about why the
        heavy import is deferred). Each has its OWN copy of this
        singleton in its own memory. A naive "load once, keep forever"
        cache would mean an editor's change in Snippets -> Voci chatbot
        only reaches whichever worker happens to serve their NEXT test
        message, while the other two workers keep answering from the
        stale knowledge base until they're restarted - invisible,
        confusing, and exactly the kind of thing that makes a
        self-service CMS feel broken.

        Instead: every call checks the newest `updated_at` across all
        ChatbotEntry rows (one cheap indexed MAX() query - trivial at
        the scale of a few dozen KB entries) and only pays the real
        cost - re-embedding every question - if that timestamp has
        moved since this worker's last build. The heavy SentenceTransformer
        import/model load also only happens once per worker regardless
        (the model itself doesn't change, only the questions being
        embedded), unless the worker has never loaded it before.
        """
        latest = ChatbotEntry.objects.aggregate(latest=Max("updated_at"))["latest"]

        if self._model is not None and latest == self._loaded_kb_version:
            return  # already loaded, and nothing has changed since

        if self._model is None:
            print("[Chatbot] Initializing model...")
            # Local import: this is the ~1GB torch pull, deferred to first use.
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
            # Fresh install, not seeded yet - nothing to embed. Leave
            # embeddings empty rather than calling model.encode([]),
            # which some sentence-transformers versions handle badly.
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
            # No ChatbotEntry rows exist yet (unseeded install). Fail
            # soft with whatever fallback text is configured, rather
            # than crashing the chat widget for every visitor.
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

        # The margin check exists to catch genuine ambiguity - two
        # DIFFERENT answers that both scored about the same, so the
        # winner is close to arbitrary. It does NOT mean anything when
        # the runner-up is just another phrasing of the SAME answer
        # ("what is Axatel" / "what does Axatel do" both live under the
        # same KB entry) - that's not ambiguous, it's the same answer
        # either way, and comparing against it caused real questions to
        # incorrectly fall back on the very first live test run. Skip
        # runner-ups that share the top match's answer when computing
        # the margin.
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
            # Ambiguous: several entries scored about the same, so the
            # winner is close to arbitrary. Better to say nothing.
            meta["used_fallback"] = True
            meta["reason"] = "margin too small"
            return self._fallback, meta

        return self._answers[best_idx], meta


# Singleton instance \u2014 constructing this is cheap: __init__ only sets
# attributes to None. The model is not touched until answer() is called.
engine = ChatbotEngine()