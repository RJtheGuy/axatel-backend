"""The Azienda and Approfondimenti pages as they were written in the
frontend (app/data/contentPages.ts and app/data/glossary.ts), used once by
`manage.py import_info_pages`. Edit the pages in the CMS, not here.

"Coming soon" pages (Academy, News, FAQ) are not created: the site keeps
showing its placeholder until someone writes the page in the CMS."""

SECTIONS = [
    {"slug": "azienda", "title": "Azienda"},
    {"slug": "approfondimenti", "title": "Approfondimenti"},
]

PAGES = {'azienda': [{'slug': 'chi-siamo',
              'title': 'Chi siamo',
              'eyebrow': 'Tecnologia e infrastrutture',
              'introduction': 'Dal 2012 progettiamo a Vicenza sistemi di automazione, monitoraggio e IoT per '
                              'rendere infrastrutture e territori piu osservabili e sicuri.',
              'status': 'published',
              'image': 'angelo.png',
              'image_alt': 'Identita visiva Axatel',
              'feature': None,
              'sections': [{'title': 'Un unico interlocutore',
                            'paragraphs': ["Seguiamo l'intera filiera: sensori ed elettronica, "
                                           'comunicazione, automazione, software di supervisione e servizi '
                                           'operativi.',
                                           'Questa visione riduce i passaggi tra fornitori e mantiene '
                                           'coerenti dati, impianti e procedure.'],
                            'highlights': ['Automazione', 'IoT', 'Software']},
                           {'title': 'Esperienza sul campo',
                            'paragraphs': ['Lavoriamo in particolare su strade, gallerie, dissesto '
                                           'idrogeologico e monitoraggio ambientale e strutturale.',
                                           'Partiamo dal problema operativo, scegliamo la tecnologia '
                                           'necessaria e accompagniamo il sistema durante il suo '
                                           'utilizzo.']}],
              'cta': None},
             {'slug': 'bilancio-sostenibilita',
              'title': 'Bilancio di sostenibilita',
              'eyebrow': 'Responsabilita e trasparenza',
              'introduction': 'Misuriamo il nostro impatto e rendiamo visibili impegni, risultati e '
                              'obiettivi ambientali, sociali e di governance.',
              'status': 'published',
              'image': 'casi-di-successo/esg.webp',
              'image_alt': 'Percorso ESG e sostenibilita Axatel',
              'feature': None,
              'sections': [{'title': 'Un percorso misurabile',
                            'paragraphs': ['Il bilancio organizza dati e iniziative per leggere con '
                                           "chiarezza l'evoluzione dell'azienda oltre ai soli risultati "
                                           'economici.',
                                           'Indicatori e obiettivi aiutano a trasformare gli impegni in '
                                           'azioni verificabili nel tempo.'],
                            'highlights': ['Ambiente', 'Persone', 'Governance']},
                           {'title': 'Tecnologia con uno scopo',
                            'paragraphs': ['Le soluzioni Axatel contribuiscono a conoscere meglio '
                                           'infrastrutture e territorio, riducendo interventi inutili e '
                                           'anticipando le criticita.',
                                           'Lo stesso approccio basato sui dati guida le scelte interne e il '
                                           'dialogo con clienti, partner e comunita.']}],
              'cta': None},
             {'slug': 'invia-il-cv',
              'title': 'Lavora con noi',
              'eyebrow': 'Invia il tuo CV',
              'introduction': 'Cerchiamo persone curiose di unire elettronica, software e ingegneria per '
                              'risolvere problemi concreti sul territorio.',
              'status': 'published',
              'image': '',
              'image_alt': '',
              'feature': None,
              'sections': [{'title': 'Competenze che dialogano',
                            'paragraphs': ['I nostri progetti richiedono collaborazione tra sviluppo '
                                           'software, automazione, elettronica, reti e progettazione.',
                                           'Valutiamo esperienza e specializzazione, ma anche capacita di '
                                           'comprendere il sistema nel suo insieme.'],
                            'highlights': ['Software', 'Automazione', 'Ingegneria']},
                           {'title': 'Presentati',
                            'paragraphs': ['Raccontaci cosa sai fare, quali problemi ti piace affrontare e '
                                           'in quale direzione vorresti crescere.',
                                           'Puoi inviare la candidatura attraverso la pagina contatti: il '
                                           'messaggio arrivera direttamente ad Axatel.']}],
              'cta': {'text': 'Vuoi costruire con noi sistemi che lavorano nel mondo reale?',
                      'label': 'Invia il tuo CV',
                      'href': '/contatti'}},
             {'slug': 'diventa-partner',
              'title': 'Diventa Partner',
              'eyebrow': 'Collaborazioni',
              'introduction': 'Costruiamo partnership con chi porta competenze, tecnologie o presenza sul '
                              'territorio e condivide un approccio concreto ai problemi.',
              'status': 'published',
              'image': '',
              'image_alt': '',
              'feature': None,
              'sections': [{'title': 'Soluzioni che si completano',
                            'paragraphs': ['Integratori, produttori, progettisti e operatori possono unire '
                                           'la propria specializzazione alla filiera tecnologica Axatel.',
                                           'La collaborazione parte da obiettivi chiari, ruoli definiti e '
                                           'valore riconoscibile per il cliente finale.'],
                            'highlights': ['Tecnologie', 'Competenze', 'Territorio']},
                           {'title': 'Crescere sui progetti',
                            'paragraphs': ['Condividiamo conoscenza tecnica, opportunita e responsabilita '
                                           'per affrontare scenari che richiedono capacita complementari.',
                                           'Il successo della partnership si misura sulla qualita del '
                                           'risultato e sulla continuita della relazione.']}],
              'cta': {'text': 'Hai una tecnologia o un progetto che potrebbe incontrare le competenze '
                              'Axatel?',
                      'label': 'Parliamone',
                      'href': '/contatti'}}],
 'approfondimenti': [{'slug': 'academy',
                      'title': 'Academy',
                      'eyebrow': 'Formazione',
                      'introduction': 'Stiamo preparando percorsi e contenuti formativi dedicati a '
                                      'monitoraggio, automazione e gestione delle infrastrutture.',
                      'status': 'coming-soon',
                      'image': '',
                      'image_alt': '',
                      'feature': None,
                      'sections': [],
                      'cta': None},
                     {'slug': 'news',
                      'title': 'News',
                      'eyebrow': 'Aggiornamenti',
                      'introduction': 'Stiamo costruendo uno spazio per raccontare novita, progetti e '
                                      'appuntamenti dal mondo Axatel.',
                      'status': 'coming-soon',
                      'image': '',
                      'image_alt': '',
                      'feature': None,
                      'sections': [],
                      'cta': None},
                     {'slug': 'faq',
                      'title': 'FAQ',
                      'eyebrow': 'Risposte utili',
                      'introduction': 'Stiamo raccogliendo le domande piu frequenti su soluzioni, '
                                      'tecnologie, installazione e assistenza.',
                      'status': 'coming-soon',
                      'image': '',
                      'image_alt': '',
                      'feature': None,
                      'sections': [],
                      'cta': None}]}

GLOSSARY = {'slug': 'glossario',
 'title': 'Glossario',
 'eyebrow': 'Parole e tecnologie',
 'introduction': 'Definizioni semplici dei termini tecnici usati nelle pagine Axatel, dalla sensoristica '
                 'alle piattaforme di supervisione.',
 'terms': [{'term': 'Accelerometro',
            'definition': 'Sensore che misura accelerazioni e vibrazioni. Nel monitoraggio strutturale aiuta '
                          'a osservare come ponti, edifici e altre opere reagiscono a traffico, vento o '
                          'eventi sismici.'},
           {'term': 'Allarme',
            'definition': 'Segnalazione generata quando una misura o un evento richiede attenzione. Puo '
                          'avvisare un operatore oppure attivare automaticamente una procedura.'},
           {'term': 'API',
            'definition': 'Insieme di regole che permette a software diversi di scambiarsi dati e comandi in '
                          'modo strutturato.',
            'aliases': ['Application Programming Interface']},
           {'term': 'Attuatore',
            'definition': 'Dispositivo che esegue un comando fisico, per esempio accendere una sirena, '
                          'cambiare un semaforo o mostrare un messaggio su un pannello.'},
           {'term': 'Automazione',
            'definition': 'Uso di logiche e dispositivi per eseguire operazioni senza intervento manuale '
                          'continuo, seguendo regole e condizioni definite.'},
           {'term': 'Cloud',
            'definition': 'Insieme di risorse informatiche accessibili tramite rete, usate per conservare '
                          'dati ed eseguire applicazioni senza ospitarle necessariamente nella sede del '
                          'cliente.'},
           {'term': 'Control Room',
            'definition': 'Sala di controllo dalla quale gli operatori osservano impianti ed eventi, '
                          'ricevono allarmi e coordinano gli interventi.'},
           {'term': 'Dashboard',
            'definition': 'Schermata che riassume dati, indicatori e allarmi per offrire una lettura '
                          'immediata dello stato di un sistema.'},
           {'term': 'Data logger',
            'definition': 'Dispositivo che acquisisce e conserva nel tempo le misure prodotte da uno o piu '
                          'sensori, anche quando la connessione non e disponibile.'},
           {'term': 'Digital Twin',
            'definition': "Rappresentazione digitale di un impianto o di un'infrastruttura, alimentata da "
                          'dati reali per comprenderne stato e comportamento.',
            'aliases': ['Gemello digitale']},
           {'term': 'Edge computing',
            'definition': 'Elaborazione dei dati vicino al punto in cui vengono prodotti. Riduce tempi di '
                          'risposta e quantita di informazioni da inviare al sistema centrale.'},
           {'term': 'Fail-safe',
            'definition': 'Principio di progettazione per cui, in caso di guasto, il sistema passa '
                          'automaticamente alla condizione considerata piu sicura.'},
           {'term': 'Firmware',
            'definition': 'Software installato direttamente in un dispositivo elettronico. Controlla '
                          'sensori, consumi, memoria, comunicazioni e comportamento operativo.'},
           {'term': 'Fessurimetro',
            'definition': "Sensore che misura l'apertura e l'evoluzione di una fessura in una struttura."},
           {'term': 'Gateway',
            'definition': 'Apparato che collega dispositivi o reti differenti. In una rete LoRaWAN riceve i '
                          'messaggi radio dei sensori e li inoltra al network server.'},
           {'term': 'Georeferenziazione',
            'definition': 'Associazione di un dato o di un oggetto a una posizione geografica precisa, così '
                          'da rappresentarlo e consultarlo su una mappa.'},
           {'term': 'Inclinometro',
            'definition': 'Sensore che misura variazioni di inclinazione. Viene usato per seguire movimenti '
                          'e deformazioni di strutture o terreni.'},
           {'term': 'Interoperabilita',
            'definition': 'Capacita di sistemi diversi di comunicare, scambiarsi informazioni e lavorare '
                          'insieme senza perdere il significato dei dati.'},
           {'term': 'IoT',
            'definition': 'Internet of Things: rete di oggetti fisici dotati di sensori, software e '
                          'connettivita, capaci di raccogliere dati e comunicare con altri sistemi.',
            'aliases': ['Internet of Things', 'Internet delle cose']},
           {'term': 'KPI',
            'definition': 'Indicatore sintetico usato per misurare prestazioni, risultati o andamento di un '
                          'processo rispetto a un obiettivo.',
            'aliases': ['Key Performance Indicator']},
           {'term': 'LoRaWAN',
            'definition': 'Protocollo radio a lungo raggio e basso consumo pensato per collegare molti '
                          'sensori. Copre aree estese, richiede poca energia e non necessita di una SIM per '
                          'ogni dispositivo.',
            'aliases': ['Long Range Wide Area Network', 'LoRa']},
           {'term': 'LPWAN',
            'definition': 'Famiglia di reti wireless progettate per trasmettere piccole quantita di dati su '
                          'lunghe distanze consumando poca energia. LoRaWAN ne e un esempio.',
            'aliases': ['Low Power Wide Area Network']},
           {'term': 'Middleware',
            'definition': 'Software intermedio che riceve dati da dispositivi o applicazioni, li normalizza '
                          'e li rende disponibili agli altri componenti del sistema.'},
           {'term': 'Network server',
            'definition': 'Componente centrale di una rete LoRaWAN che gestisce dispositivi, sicurezza e '
                          'messaggi ricevuti dai gateway.'},
           {'term': 'Particolato',
            'definition': "Insieme di particelle solide e liquide sospese nell'aria. Le sigle PM10 e PM2.5 "
                          'indicano particelle con dimensioni differenti.'},
           {'term': 'PLC',
            'definition': 'Controllore industriale programmabile che legge segnali dal campo ed esegue in '
                          'modo affidabile logiche, sequenze e comandi sugli impianti.',
            'aliases': ['Programmable Logic Controller']},
           {'term': 'Protocollo',
            'definition': 'Insieme condiviso di regole e formati che consente a dispositivi e software di '
                          'comunicare correttamente.'},
           {'term': 'Real-time',
            'definition': 'Modalita in cui dati ed eventi vengono acquisiti, elaborati e resi disponibili '
                          'con un ritardo sufficientemente breve per intervenire subito.',
            'aliases': ['Tempo reale']},
           {'term': 'SCADA',
            'definition': 'Sistema software per supervisionare e controllare impianti. Visualizza sinottici, '
                          'misure e allarmi e permette agli operatori autorizzati di inviare comandi.',
            'aliases': ['Supervisory Control and Data Acquisition']},
           {'term': 'Sensore',
            'definition': 'Dispositivo che rileva una grandezza fisica o ambientale, come temperatura, '
                          'livello, inclinazione o concentrazione di un inquinante, e la trasforma in un '
                          'dato.'},
           {'term': 'Sinottico',
            'definition': 'Rappresentazione grafica semplificata di un impianto che mostra collegamenti, '
                          'stati, misure e comandi in una sola schermata.'},
           {'term': 'Soglia',
            'definition': 'Valore configurato oltre il quale una misura cambia livello di attenzione o '
                          'genera una segnalazione.'},
           {'term': 'Telemetria',
            'definition': 'Raccolta e trasmissione a distanza delle misure prodotte da sensori, macchine o '
                          'impianti.'},
           {'term': 'Videoanalisi',
            'definition': 'Elaborazione automatica delle immagini di una telecamera per riconoscere oggetti, '
                          'comportamenti o eventi, come code e veicoli fermi.'}]}

# Starter FAQ, created as a DRAFT (not published) for marketing to review.
# Every answer reuses statements already on the site (Chi siamo, LoRaWAN,
# Monitoraggio, AngelBPM, Collaudo e manutenzione pages).
FAQ_DRAFT = {
    "slug": "faq",
    "title": "FAQ",
    "eyebrow": "Risposte utili",
    "introduction": "Le domande più frequenti su soluzioni, tecnologie, installazione e assistenza.",
    "items": [
        ("Di cosa si occupa Axatel?",
         "Dal 2012 progettiamo a Vicenza sistemi di automazione, monitoraggio e IoT per rendere infrastrutture e "
         "territori più osservabili e sicuri. Seguiamo l'intera filiera: sensori ed elettronica, comunicazione, "
         "automazione, software di supervisione e servizi operativi."),
        ("Che cosa potete monitorare?",
         "Lavoriamo in particolare su strade, gallerie, dissesto idrogeologico e monitoraggio ambientale e "
         "strutturale: qualità dell'aria, fiumi, frane, traffico, cantieri, ponti ed edifici."),
        ("Servono corrente elettrica o una SIM dati sul posto?",
         "Non sempre. La rete LoRaWAN collega sensori distribuiti via radio a lungo raggio, con bassi consumi e "
         "senza una SIM per ogni dispositivo, anche lontano dalla rete elettrica o dalla copertura cellulare. "
         "Alcune soluzioni, come Cerere Pro Aria, hanno anche alimentazione autonoma."),
        ("Come si consultano i dati?",
         "Dashboard, mappe e grafici mostrano le misure in tempo reale e lo storico, che si può anche esportare. "
         "Console web e app mobile permettono la consultazione da remoto; le console sono disponibili presso il "
         "cliente o come servizio web."),
        ("Come funzionano gli allarmi?",
         "Soglie configurabili attivano avvisi di guardia o di allarme. Eventi e allarmi arrivano agli operatori "
         "con il contesto necessario per valutare la situazione e intervenire rapidamente."),
        ("Vi occupate anche di installazione e manutenzione?",
         "Sì: seguiamo i progetti dalla progettazione alla direzione lavori. Test funzionali e messa in servizio "
         "verificano il sistema, e una diagnostica chiara con la documentazione agevola gli interventi durante "
         "l'intero ciclo di vita."),
        ("Come posso chiedere un preventivo?",
         "Dalle pagine di prodotti e soluzioni, con il pulsante \"Richiedi un preventivo\", oppure dalla pagina "
         "Contatti: la richiesta arriva direttamente ad Axatel."),
    ],
}
