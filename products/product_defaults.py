"""Products already presented on the site (monitoring pages and datasheet
links), used once by `manage.py seed_products`. Specs contain only facts
stated in the site's own text; complete them in the CMS.
Edit products in the CMS, not here."""

GEO_CASES = [
    "geo-angel-il-sistema-di-axatel-di-nuovo-in-azione",
    "3-anni-dallinstallazione-di-geo-angel",
    "nuove-frane-sul-fadalto-nuovo-record-per-geo-angel",
]

DEFAULT_PRODUCTS = [
    {
        "slug": "angel-bpm",
        "title": "Angel BPM",
        "category": "piattaforme",
        "tagline": "Il cuore software per gestire traffico, IoT, meteo, video e manutenzione con dati in tempo reale e processi guidati.",
        "image": "Angel.png",
        "datasheet_url": "",
        "specs": [
            ("Funzioni", "Eventi e allarmi in tempo reale, dashboard, mappe e video wall configurabili"),
            ("Procedure", "Procedure operative, attività e responsabilità associate agli eventi, con tracciamento"),
            ("Manutenzione", "Anagrafiche, scadenze e storico degli interventi"),
            ("Integrazioni", "Sensori, impianti, telecamere, SCADA e sistemi di terze parti"),
        ],
        "cases": ["automazione-e-monitoraggio-in-ss51-alemagna-bl"],
    },
    {
        "slug": "angel-river",
        "title": "Angel River",
        "category": "sistemi",
        "tagline": "Sistema per monitorare corsi d'acqua e bacini, con rilevamento dei livelli e allerta di emergenza.",
        "image": "AngelRiver.png",
        "datasheet_url": "https://www.axatel.it/wp-content/uploads/2026/03/2025_ANGEL-RIVER.pdf",
        "specs": [
            ("Misura", "Livello di corsi d'acqua e bacini"),
            ("Allerta", "Segnalazioni al superamento delle soglie, allarme acustico in broadcast"),
            ("Architettura", "Sensori, network server LoRaWAN, middleware e software Axatel"),
            ("Console", "Presso il cliente o come servizio web"),
            ("Per", "Protezione Civile, consorzi di bonifica, gestori di sottopassi e bacini"),
        ],
        "cases": ["angel-river-il-sistema-di-monitoraggio-dei-livelli-dei-corsi-dacqua"],
    },
    {
        "slug": "geo-angel",
        "title": "Geo Angel",
        "category": "sistemi",
        "tagline": "Sistema real-time per il monitoraggio dei dissesti geologici e l'automazione delle procedure di emergenza.",
        "image": "GeoAngel.png",
        "datasheet_url": "https://www.axatel.it/wp-content/uploads/2026/03/2026_GEO-ANGEL.pdf",
        "specs": [
            ("Misura", "Movimenti del terreno con sensori georeferenziati; accelerometri su reti paramassi e barriere"),
            ("Automazioni", "Semafori, pannelli a messaggio variabile e sirene"),
            ("Meteo", "Stazione locale: vento, pioggia, temperatura, umidità"),
            ("Software", "Portale web con mappe, storico, soglie e frequenze di aggiornamento"),
        ],
        "cases": GEO_CASES,
    },
    {
        "slug": "traffic-alert",
        "title": "Traffic Alert",
        "category": "sistemi",
        "tagline": "Sistema di videoanalisi real-time per generare e gestire allarmi relativi al traffico stradale.",
        "image": "TrafficAlert.png",
        "datasheet_url": "https://www.axatel.it/wp-content/uploads/2026/03/traffic-alert.pdf",
        "specs": [
            ("Rileva", "Incidenti, code, veicoli fermi, guida contromano"),
            ("Tecnologia", "Videoanalisi con software di bordo, snapshot e video in tempo reale"),
            ("Integrazioni", "Applicazione web, Angel BPM e SCADA"),
            ("Automazioni", "Pannelli a messaggio variabile, semafori e sistemi di allarme"),
        ],
        "cases": [
            "galleria-caltanissetta-ss640-opera-completata",
            "galleria-caltanissetta-ss640-apertura-canna-sinistra",
        ],
    },
    {
        "slug": "angel-road-site",
        "title": "Angel Road Site",
        "category": "sistemi",
        "tagline": "Sistema real-time per il tracciamento e il controllo dello stato di sicurezza nei cantieri stradali.",
        "image": "AngelRoadsite.png",
        "datasheet_url": "https://www.axatel.it/wp-content/uploads/2026/03/2026_ANGEL-ROAD-SITE.pdf",
        "specs": [
            ("Tracciamento", "GPS di cartelli e mezzi d'opera"),
            ("Sicurezza operatori", "Rilevamento di condizioni di uomo a terra"),
            ("Segnaletica", "Notifica in tempo reale di urti, ribaltamenti e spostamenti"),
            ("Analisi del traffico", "Telecamere e radar: conteggio, velocità e traiettorie"),
            ("Mappe", "Georeferenziate, con import del progetto da DWG"),
        ],
        "cases": [],
    },
    {
        "slug": "angel-bridge",
        "title": "Angel Bridge",
        "category": "sistemi",
        "tagline": "Sistema hardware e software per il monitoraggio strutturale di ponti, cavalcavia, edifici e monumenti mediante tecnologia radio LoRaWAN.",
        "image": "AngelBridge.png",
        "datasheet_url": "https://www.axatel.it/wp-content/uploads/2026/03/2026_ANGEL-BRIDGE.pdf",
        "specs": [
            ("Sensori", "Fessurimetri, inclinometri, accelerometri"),
            ("Connettività", "LoRaWAN; opera anche con scarsa copertura cellulare"),
            ("Allarmi", "Soglie configurabili di guardia e di allarme"),
            ("Software", "Console web e app mobile, storico ed esportazione; integrabile con SCADA"),
            ("Applicazioni", "Ponti, cavalcavia, edifici, monumenti, aree sismiche"),
        ],
        "cases": [],
    },
    {
        "slug": "cerere-pro-aria",
        "title": "Cerere Pro Aria",
        "category": "sensori",
        "tagline": "Sistema radio LoRaWAN per rilevare in tempo reale gli inquinanti atmosferici e rendere disponibili i dati alla piattaforma di supervisione.",
        "image": "",
        "datasheet_url": "https://www.axatel.it/wp-content/uploads/2026/03/2025_CERERE-PRO-ARIA-PALO.pdf",
        "specs": [
            ("Qualità dell'aria", "CO, CO₂, NOx, NO₂, SO₂, O₃, particolato, TVOC"),
            ("Parametri meteo", "Temperatura, pressione, umidità, velocità e direzione del vento"),
            ("Connettività", "LoRaWAN, senza SIM dati"),
            ("Alimentazione", "Autonoma, adatta a siti senza rete elettrica"),
            ("Software", "Portale web con mappe e grafici, soglie, allarmi ed esportazione dati"),
        ],
        "cases": [],
    },
]
