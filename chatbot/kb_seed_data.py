"""
chatbot/kb_seed_data.py

The original hardcoded chatbot knowledge base - previously the
KNOWLEDGE_BASE constant inside engine.py. Moved here unchanged, now
used only by `manage.py seed_chatbot_kb` to populate the real,
CMS-editable ChatbotEntry table on first setup.

engine.py no longer reads this directly - it queries ChatbotEntry from
the database instead. This file exists purely as seed data / a starting
point, and as a reference for the shape editors are recreating when
they add entries through Snippets → Voci chatbot in the Wagtail admin.
"""

KNOWLEDGE_BASE = [
    {
        "questions": [
            "cos'è Axatel", "chi è Axatel", "cosa fa Axatel",
            "di cosa vi occupate", "parlami di Axatel",
            "what is Axatel", "what does Axatel do", "tell me about Axatel",
        ],
        "answer": (
            "Axatel è un'azienda di innovazione tecnologica con sede a Vicenza, "
            "attiva dal 2012 nell'automazione stradale e nell'Internet of Things. "
            "Progettiamo sistemi di monitoraggio e supervisione — dai sensori sul "
            "campo fino alla control room — per pubbliche amministrazioni, "
            "concessionarie stradali e aziende di manutenzione impianti."
        ),
    },
    {
        "questions": [
            "dove siete", "dove si trova Axatel", "indirizzo", "sede",
            "come vi raggiungo", "where are you located", "address",
        ],
        "answer": (
            "La sede di Axatel è in Viale del Mercato Nuovo, 75, "
            "36100 Vicenza (VI), Italia."
        ),
    },
    {
        "questions": [
            "come vi contatto", "numero di telefono", "email",
            "come posso scrivervi", "contatti", "how do I contact you",
            "phone number", "contact email",
        ],
        "answer": (
            "Puoi contattarci al numero +39 0444 96 38 91 oppure via email "
            "a info@axatel.it. Siamo anche su LinkedIn."
        ),
    },
    {
        "questions": [
            "cos'è IoT", "cosa fate con l'IoT", "internet of things",
            "sensori e connettività", "what is your IoT offering",
        ],
        "answer": (
            "Axatel sviluppa e gestisce l'intera filiera tecnologica per i "
            "servizi IoT: gateway, network server, middleware e sensori. "
            "Progettiamo e realizziamo soluzioni per persone, aziende e città, "
            "dal singolo sensore fino alla piattaforma di gestione dei dati."
        ),
    },
    {
        "questions": [
            "cos'è smart road", "monitoraggio stradale", "sicurezza strade",
            "sensori su strade e autostrade", "what is smart road",
        ],
        "answer": (
            "Smart Road è la nostra soluzione di monitoraggio su strade e "
            "autostrade per la sicurezza della viabilità — rilevamento di "
            "frane, allagamenti, condizioni del manto stradale e traffico, "
            "con allerta in tempo reale verso la control room."
        ),
    },
    {
        "questions": [
            "cos'è smart city", "soluzioni per le città",
            "monitoraggio urbano", "what is smart city",
        ],
        "answer": (
            "Smart City comprende le nostre soluzioni IoT progettate per le "
            "esigenze delle città — monitoraggio ambientale, gestione degli "
            "impianti pubblici e sistemi di supervisione integrati per la "
            "pubblica amministrazione."
        ),
    },
    {
        "questions": [
            "supervisione e controllo", "control room", "cosa fate in ingegneria",
            "impianti di automazione", "what does supervisione e controllo mean",
        ],
        "answer": (
            "Progettiamo impianti di automazione personalizzati in base alle "
            "esigenze dell'opera da monitorare — dalla raccolta dati dei "
            "sensori fino alla control room, dove gli operatori supervisionano "
            "e gestiscono gli allarmi in tempo reale."
        ),
    },
    {
        "questions": [
            "servizi di ingegneria", "ingegneria integrata",
            "what engineering services do you offer",
        ],
        "answer": (
            "Offriamo ingegneria integrata end-to-end: dalla progettazione alla "
            "realizzazione, con l'obiettivo di ridurre le problematiche e i "
            "costi di gestione per il cliente lungo tutto il ciclo di vita "
            "dell'impianto."
        ),
    },
    {
        "questions": [
            "sviluppo elettronico", "progettate hardware",
            "sviluppate elettronica conto terzi", "electronics development",
        ],
        "answer": (
            "Sviluppiamo internamente — e anche conto terzi — le nostre "
            "soluzioni elettroniche per il controllo e la comunicazione, "
            "dai sensori ai gateway di trasmissione."
        ),
    },
    {
        "questions": [
            "cos'è LoRaWAN", "che tecnologia usate", "trasmissione radio",
            "what is LoRaWAN", "which technology do you use",
        ],
        "answer": (
            "LoRaWAN è la tecnologia di trasmissione radio che utilizziamo "
            "per le applicazioni outdoor — a lungo raggio e basso consumo, "
            "ideale per sensori distribuiti su territori estesi come strade "
            "e corsi d'acqua."
        ),
    },
    {
        "questions": [
            "catalogo sensori", "che sensori avete", "che tipo di sensori",
            "what sensors do you offer",
        ],
        "answer": (
            "Sviluppiamo e realizziamo internamente i sensori per i nostri "
            "sistemi di supervisione, progettati per applicazioni outdoor in "
            "condizioni ambientali difficili. Per il catalogo completo, "
            "scrivici a info@axatel.it."
        ),
    },
    {
        "questions": [
            "cos'è angel river", "monitoraggio corsi d'acqua",
            "livelli fiumi", "what is angel river",
        ],
        "answer": (
            "Angel River è il nostro sistema per il monitoraggio dei livelli "
            "dei corsi d'acqua, pensato per pubbliche amministrazioni, "
            "concessionarie stradali e aziende di manutenzione impianti che "
            "devono prevenire rischi idrogeologici."
        ),
    },
    {
        "questions": [
            "casi di successo", "progetti realizzati", "esempi di progetti",
            "con chi avete lavorato", "referenze", "case studies",
        ],
        "answer": (
            "Tra i nostri progetti: automazione e monitoraggio sulla SS51 "
            "Alemagna per la Provincia di Belluno e ANAS, l'apertura della "
            "Galleria di Caltanissetta sulla SS640 con ANAS, e la partnership "
            "con TAV (Trans Audio Video) per la distribuzione delle nostre "
            "soluzioni. L'elenco completo è nella sezione Casi di successo "
            "del sito."
        ),
    },
    {
        "questions": [
            "diventa partner", "come diventare partner", "partnership",
            "collaborazioni", "how do I become a partner",
        ],
        "answer": (
            "Cerchiamo sempre nuovi partner per distribuire ed estendere le "
            "nostre soluzioni. Scrivici a info@axatel.it indicando la tua "
            "azienda e l'area di interesse — trovi anche una pagina dedicata "
            "\"Diventa partner\" sul sito."
        ),
    },
    {
        "questions": [
            "certificazioni", "siete certificati", "ESG", "sostenibilità",
            "are you certified", "sustainability",
        ],
        "answer": (
            "Axatel ha ottenuto lo score \"C — Satisfactory Level of "
            "Sustainability\" nell'ambito della certificazione ESG. Lavoriamo "
            "anche con enti certificatori come IQ Cert, SQS ed ESNA-SOA."
        ),
    },
    {
        "questions": [
            "voglio un preventivo", "richiedi informazioni",
            "come inizio un progetto con voi", "sviluppa il tuo business",
            "I want a quote", "how do I start a project with you",
        ],
        "answer": (
            "Scrivici a commerciale@axatel.it descrivendo brevemente la tua "
            "esigenza — un nostro tecnico ti ricontatterà per capire come "
            "possiamo aiutarti."
        ),
    },
    {
        "questions": [
            "avete un commerciale", "posso parlare con un commerciale",
            "contatto commerciale", "ufficio commerciale",
            "chi mi segue commercialmente", "voglio parlare con un venditore",
            "can I speak to sales", "sales contact",
        ],
        "answer": (
            "Per richieste commerciali scrivi a commerciale@axatel.it "
            "oppure chiama il +39 0444 96 38 91: ti mettiamo in contatto "
            "con la persona giusta."
        ),
    },
    {
        "questions": [
            "posso parlare con un tecnico", "assistenza tecnica",
            "supporto tecnico", "ho un problema tecnico",
            "chi mi da supporto", "voglio parlare con un ingegnere",
            "technical support", "can I speak to an engineer",
        ],
        "answer": (
            "Per l'assistenza tecnica scrivi a info@axatel.it descrivendo "
            "il problema e l'impianto coinvolto: un nostro tecnico ti "
            "ricontatterà."
        ),
    },
    {
        "questions": [
            "quanti siete", "quante persone lavorano in Axatel",
            "quanti dipendenti avete", "quanto e grande l'azienda",
            "dimensione azienda", "how many people work at Axatel",
            "how big is the company",
        ],
        "answer": (
            "Per informazioni sull'organizzazione e sul team scrivi a "
            "info@axatel.it: non ho questo dato a disposizione."
        ),
    },
    # ── FALLBACK — must be last ──
    {
        "questions": ["altro", "qualcos'altro", "non c'entra", "other", "something else"],
        "answer": (
            "Posso rispondere solo a domande su Axatel e le nostre soluzioni "
            "di monitoraggio e IoT. Per qualsiasi altra richiesta, scrivici a "
            "info@axatel.it."
        ),
        "_fallback": True,
    },
]