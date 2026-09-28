"""The 12 "Come lo realizziamo?" pages as they were written in the frontend
(app/data/contentPages.ts), used once by `manage.py import_solution_pages`.
Edit the pages in the CMS, not here."""

DEFAULT_SOLUTIONS = [
    {
        "slug": "angel-bpm",
        "title": "Gestionale AngelBPM",
        "group": "Piattaforme",
        "eyebrow": "Supervisione e controllo",
        "introduction": "Una piattaforma centrale raccoglie eventi, dati e procedure per trasformare sistemi diversi in un unico ambiente operativo.",
        "image": "Angel.png",
        "feature": {
            "label": "La piattaforma",
            "name": "Angel BPM Platform",
            "description": "Il cuore software per gestire traffico, IoT, meteo, video e manutenzione con dati in tempo reale e processi guidati."
        },
        "feature_product": "angel-bpm",
        "sections": [
            {
                "title": "Una vista unica sull'infrastruttura",
                "paragraphs": [
                    "AngelBPM riunisce dati provenienti da sensori, impianti, telecamere e sistemi di terze parti in dashboard, mappe e video wall configurabili.",
                    "Eventi e allarmi arrivano agli operatori con il contesto necessario per valutare la situazione e intervenire rapidamente."
                ],
                "highlights": [
                    "Eventi real-time",
                    "Dashboard e video wall",
                    "Integrazione sistemi"
                ]
            },
            {
                "title": "Dall'evento alla procedura",
                "paragraphs": [
                    "La piattaforma associa agli eventi procedure operative, attività e responsabilità. Ogni passaggio rimane tracciato e alimenta report e indicatori.",
                    "La gestione della manutenzione completa il quadro con anagrafiche, scadenze e storico degli interventi."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "analitici",
        "title": "Analitici",
        "group": "Piattaforme",
        "eyebrow": "Dati e decisioni",
        "introduction": "I dati raccolti sul campo diventano indicatori leggibili, confrontabili e utili a programmare le decisioni.",
        "image": "",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "Dal dato grezzo all'informazione",
                "paragraphs": [
                    "Serie storiche, soglie, aggregazioni e correlazioni aiutano a riconoscere andamenti e anomalie senza perdere il dettaglio della singola misura.",
                    "Dashboard e report sono costruiti intorno al processo del gestore, non intorno alla tecnologia che produce il dato."
                ],
                "highlights": [
                    "Serie storiche",
                    "KPI operativi",
                    "Report configurabili"
                ]
            },
            {
                "title": "Condividere e integrare",
                "paragraphs": [
                    "Le informazioni possono essere esportate o rese disponibili ad altri sistemi, enti e portali pubblici.",
                    "Permessi e viste dedicate consentono a ogni ruolo di accedere agli indicatori davvero rilevanti."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "sensori",
        "title": "Sensori",
        "group": "Sensori",
        "eyebrow": "Misure dal campo",
        "introduction": "Scegliamo e integriamo sensori adatti al fenomeno da osservare, al luogo di installazione e alla continuita richiesta.",
        "image": "AngelBridge.png",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "La misura giusta, nel punto giusto",
                "paragraphs": [
                    "Parametri ambientali, strutturali, idraulici e di mobilita richiedono tecnologie, frequenze e soglie differenti.",
                    "Il progetto considera precisione, autonomia, robustezza, manutenzione e condizioni reali del sito."
                ],
                "highlights": [
                    "Ambientali",
                    "Strutturali",
                    "Mobilita"
                ]
            },
            {
                "title": "Una filiera completa",
                "paragraphs": [
                    "Dal dispositivo alla piattaforma, seguiamo acquisizione, trasmissione, normalizzazione e rappresentazione del dato.",
                    "Il risultato e un sistema osservabile e manutenibile, pronto a generare allarmi e analisi."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "telecamere-intelligenti",
        "title": "Telecamere intelligenti",
        "group": "Sensori",
        "eyebrow": "Videoanalisi",
        "introduction": "La telecamera diventa un sensore capace di riconoscere eventi e inviare informazioni operative in tempo reale.",
        "image": "TrafficAlert.png",
        "feature": {
            "label": "Applicazione",
            "name": "Traffic Alert",
            "description": "Videoanalisi per rilevare incidenti, code, veicoli fermi e guida contromano, con verifica immediata dell'operatore."
        },
        "feature_product": "traffic-alert",
        "sections": [
            {
                "title": "Riconoscere gli eventi",
                "paragraphs": [
                    "L'elaborazione a bordo riduce i tempi di risposta e limita il traffico dati, inviando al centro solo gli eventi e i flussi necessari.",
                    "Regole e aree di analisi vengono configurate in base allo scenario stradale e agli obiettivi del gestore."
                ],
                "highlights": [
                    "Analisi a bordo",
                    "Allarmi real-time",
                    "Verifica video"
                ]
            },
            {
                "title": "Integrare la risposta",
                "paragraphs": [
                    "Gli allarmi possono raggiungere AngelBPM, SCADA e sistemi di automazione per attivare procedure, segnaletica e soccorsi.",
                    "Archivio e storico permettono di analizzare gli eventi e migliorare progressivamente le configurazioni."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "lorawan",
        "title": "LoRaWAN",
        "group": "Tecnologie",
        "eyebrow": "Internet of Things",
        "introduction": "Connettiamo sensori distribuiti con una rete radio a lungo raggio, bassi consumi e senza una SIM per ogni dispositivo.",
        "image": "AngelRiver.png",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "Connettivita per il territorio",
                "paragraphs": [
                    "LoRaWAN e adatta a misure periodiche provenienti da molti punti, anche lontani dalla rete elettrica o dalla copertura cellulare.",
                    "Pochi gateway possono servire aree estese, riducendo costi ricorrenti e complessita sul campo."
                ],
                "highlights": [
                    "Lungo raggio",
                    "Bassi consumi",
                    "Nessuna SIM"
                ]
            },
            {
                "title": "Dal nodo al cloud",
                "paragraphs": [
                    "Progettiamo dispositivi, copertura radio, gateway, network server e integrazione con le applicazioni finali.",
                    "Sicurezza, qualita del segnale e autonomia vengono verificate rispetto al contesto reale di installazione."
                ]
            }
        ],
        "cta": None,
        "devices": [
            "angel-river",
            "angel-bridge",
            "cerere-pro-aria"
        ]
    },
    {
        "slug": "networking",
        "title": "Networking",
        "group": "Tecnologie",
        "eyebrow": "Reti affidabili",
        "introduction": "Progettiamo reti che mantengono connessi impianti, sensori e centri di controllo anche negli ambienti infrastrutturali piu complessi.",
        "image": "",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "La rete come parte del sistema",
                "paragraphs": [
                    "Fibra, radio, reti industriali e connettivita IP vengono dimensionate in base a distanze, banda, ridondanza e criticita operative.",
                    "Segmentazione e monitoraggio rendono l'infrastruttura piu controllabile e semplice da gestire."
                ],
                "highlights": [
                    "Fibra e radio",
                    "Ridondanza",
                    "Monitoraggio rete"
                ]
            },
            {
                "title": "Continuita operativa",
                "paragraphs": [
                    "Architetture e apparati sono selezionati per lavorare nel contesto reale, dalla sala controllo agli armadi distribuiti lungo la rete.",
                    "Diagnostica e allarmi consentono di individuare rapidamente guasti e degradi della comunicazione."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "firmware",
        "title": "Firmware",
        "group": "Tecnologie",
        "eyebrow": "Sviluppo elettronico",
        "introduction": "Sviluppiamo il software che governa dispositivi e schede elettroniche, dalla lettura dei sensori alla comunicazione con la piattaforma.",
        "image": "",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "Intelligenza sul dispositivo",
                "paragraphs": [
                    "Il firmware gestisce acquisizione, consumi, diagnostica, memoria locale e protocolli di comunicazione.",
                    "La logica viene progettata insieme all'hardware per ottenere stabilita, autonomia e comportamento prevedibile sul campo."
                ],
                "highlights": [
                    "Acquisizione dati",
                    "Energy management",
                    "Diagnostica"
                ]
            },
            {
                "title": "Dal prototipo alla produzione",
                "paragraphs": [
                    "Affianchiamo sviluppo, test e industrializzazione, anche per prodotti elettronici realizzati conto terzi.",
                    "Aggiornabilita e tracciabilita delle versioni rendono il ciclo di vita piu semplice da governare."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "scada",
        "title": "SCADA",
        "group": "Tecnologie",
        "eyebrow": "Supervisione impianti",
        "introduction": "Sistemi SCADA raccolgono stati, misure e allarmi e consentono agli operatori di comandare impianti distribuiti da un'unica interfaccia.",
        "image": "",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "Controllo in tempo reale",
                "paragraphs": [
                    "Sinottici e dashboard mostrano lo stato degli apparati, evidenziano anomalie e supportano comandi controllati da remoto.",
                    "Allarmi, priorita e storico eventi danno all'operatore una lettura immediata di cio che richiede attenzione."
                ],
                "highlights": [
                    "Sinottici",
                    "Allarmi",
                    "Comandi remoti"
                ]
            },
            {
                "title": "Integrare nuovo ed esistente",
                "paragraphs": [
                    "Colleghiamo PLC, sensori, sottosistemi e applicazioni di terze parti attraverso protocolli industriali e interfacce dedicate.",
                    "La soluzione viene adattata alle procedure operative e ai livelli di accesso dell'organizzazione."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "plc",
        "title": "PLC",
        "group": "Tecnologie",
        "eyebrow": "Automazione industriale",
        "introduction": "La logica PLC governa gli impianti sul campo con tempi certi, regole verificabili e continuita anche in assenza del centro di controllo.",
        "image": "",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "Automazioni affidabili",
                "paragraphs": [
                    "Programmiamo sequenze, interblocchi, sicurezze e regolazioni per impianti stradali e infrastrutturali.",
                    "Ogni logica e costruita a partire dagli scenari operativi e dalle condizioni di guasto previste."
                ],
                "highlights": [
                    "Sequenze",
                    "Interblocchi",
                    "Fail-safe"
                ]
            },
            {
                "title": "Collaudo e manutenzione",
                "paragraphs": [
                    "Test funzionali e messa in servizio verificano il comportamento dell'automazione prima e dopo l'installazione.",
                    "Diagnostica chiara e documentazione agevolano gli interventi durante l'intero ciclo di vita."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "progettazione",
        "title": "Progettazione",
        "group": "Servizi",
        "eyebrow": "Ingegneria",
        "introduction": "Traduciamo esigenze operative e vincoli normativi in sistemi integrati, dimensionati per funzionare e durare nel contesto reale.",
        "image": "",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "Dall'esigenza al progetto",
                "paragraphs": [
                    "Analisi del sito, requisiti, architettura, computi e specifiche tecniche costruiscono una base chiara per la realizzazione.",
                    "Automazione, telecomunicazioni, sensoristica e software vengono considerati come parti dello stesso sistema."
                ],
                "highlights": [
                    "Analisi requisiti",
                    "Progetto integrato",
                    "Normative"
                ]
            },
            {
                "title": "Progettare per la gestione",
                "paragraphs": [
                    "Le scelte tengono conto non solo dell'installazione, ma anche di manutenzione, evoluzione e continuita operativa.",
                    "Modelli e strumenti real-time aiutano a verificare scenari e prestazioni prima della messa in esercizio."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "direzione-lavori",
        "title": "Direzione lavori",
        "group": "Servizi",
        "eyebrow": "Dalla carta al campo",
        "introduction": "Seguiamo la realizzazione affinche impianti, software e infrastrutture rispettino progetto, tempi e qualita attesa.",
        "image": "",
        "feature": None,
        "feature_product": "",
        "sections": [
            {
                "title": "Coordinamento tecnico",
                "paragraphs": [
                    "Verifichiamo avanzamento, materiali, lavorazioni e coerenza tra discipline, mantenendo allineati committente, imprese e fornitori.",
                    "Le decisioni di campo vengono tracciate e ricondotte agli obiettivi funzionali dell'opera."
                ],
                "highlights": [
                    "Controllo qualita",
                    "Coordinamento",
                    "Avanzamento lavori"
                ]
            },
            {
                "title": "Collaudo e consegna",
                "paragraphs": [
                    "Prove, verifiche e documentazione accompagnano la messa in servizio del sistema.",
                    "La consegna include gli elementi necessari per gestire e mantenere l'infrastruttura nel tempo."
                ]
            }
        ],
        "cta": None,
        "devices": []
    },
    {
        "slug": "control-room",
        "title": "Control Room",
        "group": "Servizi",
        "eyebrow": "Supporto operativo",
        "introduction": "Una control room remota affianca il personale locale nella supervisione degli impianti e nella gestione degli eventi.",
        "image": "",
        "feature": {
            "label": "Il servizio",
            "name": "Twin Control Room",
            "description": "Affiancamento remoto in tempo reale e disponibilita di una sala radio di backup per aumentare la continuita operativa."
        },
        "feature_product": "",
        "sections": [
            {
                "title": "Un secondo presidio",
                "paragraphs": [
                    "Gli operatori Axatel seguono allarmi e situazioni operative insieme alla sala controllo del gestore, offrendo supporto tecnico e procedurale.",
                    "Il servizio puo diventare un punto di continuita quando la postazione principale non e disponibile."
                ],
                "highlights": [
                    "Affiancamento remoto",
                    "Sala radio di backup",
                    "Supporto real-time"
                ]
            },
            {
                "title": "Conoscenza condivisa",
                "paragraphs": [
                    "L'osservazione quotidiana aiuta a individuare ricorrenze, affinare le procedure e migliorare la configurazione dei sistemi.",
                    "Report e tracciamento degli eventi mantengono trasparente il lavoro svolto."
                ]
            }
        ],
        "cta": None,
        "devices": []
    }
]
