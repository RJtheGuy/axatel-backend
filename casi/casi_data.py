"""
casi/casi_data.py

The nine success cases, lifted verbatim from the hardcoded
`dashboardConfig.successCases.items` array that used to live in
frontend/app/pages/index.vue.

This exists ONLY to seed the database once (see
management/commands/seed_casi.py). After seeding, the CMS is the source
of truth and this file can be deleted — it is not imported by models,
views or the API.

`image` holds the original /immagini/... path. The seeder does not
attempt to import these into the Wagtail image library (it has no way to
reach files that live in the Nuxt public/ directory), so cover_image is
left unset and an editor attaches the real image in the admin. The path
is kept here as a reference for which file to upload.
"""

CASI = [
    {
        "title": "Automazione e monitoraggio SS51 Alemagna",
        "slug": "automazione-e-monitoraggio-in-ss51-alemagna-bl",
        "client": "Provincia di Belluno · ANAS",
        "category": "Smart Road",
        "image": "/immagini/casi-di-successo/ss51-alemagna.webp",
        "description": (
            "Sistema di monitoraggio e automazione installato lungo la SS51 "
            "Alemagna per aumentare la sicurezza della viabilità in un'area "
            "soggetta a frane e colate detritiche."
        ),
        "tags": ["LoRaWAN", "Monitoraggio", "Automazione", "Smart Road"],
        "body": """<p>Per garantire la <b>sicurezza della SS51 Alemagna</b>, una delle principali arterie di collegamento con Cortina d'Ampezzo, Axatel ha realizzato un sistema intelligente di <b>monitoraggio delle colate detritiche</b> nell'area della <b>Croda Marcora</b>, nel comune di <b>San Vito di Cadore (BL)</b>.</p>

<p>L'intervento ha previsto l'installazione di una rete di <b>sensori IoT</b> lungo i canaloni e nelle aree a valle maggiormente esposte al rischio idrogeologico, con l'obiettivo di rilevare tempestivamente qualsiasi movimento anomalo del terreno e attivare automaticamente le procedure di emergenza.</p>

<h3>Protezione automatica della viabilità</h3>

<p>Il sistema non si limita al monitoraggio, ma interviene in modo completamente automatico. Al superamento delle soglie di rischio configurate, vengono immediatamente attivati i dispositivi di sicurezza presenti lungo la viabilità:</p>

<ul><li><b>Semafori intelligenti</b> che bloccano il traffico veicolare.</li><li><b>Sirene di allarme</b> per avvisare automobilisti, ciclisti e pedoni.</li><li><b>Notifiche istantanee</b> inviate agli enti responsabili della gestione dell'emergenza.</li></ul>

<p>La protezione interessa sia la <b>Strada Statale Alemagna</b> sia la <b>pista ciclabile adiacente</b>, due infrastrutture particolarmente frequentate durante tutto l'anno e, soprattutto, nella stagione turistica.</p>

<h3>Monitoraggio continuo in tempo reale</h3>

<p>La piattaforma raccoglie dati in tempo reale attraverso una rete di sensori composta da:</p>

<ul><li>Pluviometri per il monitoraggio delle precipitazioni.</li><li>Clinometri per rilevare eventuali variazioni di inclinazione del terreno.</li><li>Accelerometri per individuare vibrazioni e movimenti improvvisi.</li></ul>

<p>Tutti i dati vengono centralizzati nella piattaforma Axatel, che consente agli operatori di visualizzare lo stato dell'impianto, consultare lo storico delle misurazioni e ricevere notifiche immediate in caso di criticità.</p>

<h3>Un'infrastruttura progettata per prevenire</h3>

<p>Oltre a garantire una risposta automatica durante gli eventi franosi, il sistema permette di costruire uno <b>storico completo dei fenomeni</b>, fornendo informazioni preziose per l'analisi dell'evoluzione del dissesto idrogeologico e per la pianificazione degli interventi futuri.</p>

<p><b>Prevenzione, monitoraggio continuo e automazione</b> lavorano insieme per aumentare la sicurezza di cittadini, operatori e turisti, riducendo i tempi di intervento e contribuendo alla continuità della viabilità in uno dei tratti stradali più importanti delle Dolomiti.</p>""",
    },
    {
        "title": "Galleria Caltanissetta SS640",
        "slug": "galleria-caltanissetta-ss640-opera-completata",
        "client": "ANAS",
        "category": "Gallerie",
        "image": "/immagini/casi-di-successo/ss640.webp",
        "description": (
            "Tecnologie di supervisione e controllo per la nuova galleria "
            "SS640, a supporto dell'apertura completa dell'infrastruttura."
        ),
        "tags": ["Galleria", "SCADA", "Supervisione"],
        "body": """<p>La <b>Galleria Caltanissetta</b>, lungo la <b>Strada Statale 640 "Strada degli Scrittori"</b>, rappresenta una delle infrastrutture più importanti per il collegamento tra <b>Caltanissetta</b> e <b>Agrigento</b>. Per garantire elevati standard di sicurezza e continuità operativa, Axatel ha partecipato alla realizzazione degli impianti tecnologici in collaborazione con <b>Pagano S.p.A.</b> per conto di <b>ANAS</b>.</p>

<p>L'intervento ha riguardato l'installazione e l'integrazione dei sistemi di <b>automazione</b>, <b>monitoraggio</b> e <b>controllo della circolazione</b>, contribuendo al completamento dell'opera e alla successiva apertura al traffico dell'intera infrastruttura.</p>

<h3>Sicurezza integrata della galleria</h3>

<p>L'impianto è stato progettato per garantire la massima sicurezza degli utenti attraverso un insieme di sistemi intelligenti che operano in modo coordinato.</p>

<ul><li><b>By-pass pedonali</b> per l'evacuazione in caso di emergenza.</li><li><b>Sistemi di rilevazione incendio</b> con monitoraggio continuo.</li><li><b>Segnaletica luminosa dinamica</b> per la gestione della viabilità.</li><li><b>Videosorveglianza</b> distribuita lungo tutta la galleria.</li><li><b>Stazioni SOS</b> per le comunicazioni di emergenza.</li><li><b>Sensori ambientali</b> per il monitoraggio della qualità dell'aria.</li></ul>

<h3>Monitoraggio e controllo in tempo reale</h3>

<p>Tutti i dispositivi sono collegati a una piattaforma di supervisione che permette agli operatori di monitorare costantemente lo stato dell'infrastruttura, ricevere segnalazioni immediate in caso di anomalie e intervenire rapidamente per garantire la continuità del servizio.</p>

<p>La gestione centralizzata consente di controllare contemporaneamente gli impianti tecnologici, i sistemi di sicurezza e le condizioni ambientali della galleria, riducendo i tempi di intervento e aumentando l'affidabilità dell'intera infrastruttura.</p>

<h3>Una galleria progettata per il futuro</h3>

<p>Grazie all'integrazione di <b>automazione, sensoristica IoT e supervisione avanzata</b>, la Galleria Caltanissetta rappresenta un esempio di infrastruttura moderna, capace di offrire elevati standard di sicurezza e una gestione efficiente durante tutto il suo ciclo di vita.</p>

<p>L'intervento conferma l'esperienza di Axatel nello sviluppo di soluzioni tecnologiche dedicate alle <b>Smart Road</b>, contribuendo a rendere le infrastrutture stradali più sicure, intelligenti e affidabili.</p>""",
    },
    {
        "title": "Certificazione ESG",
        "slug": "certificazione-esg",
        "client": "Axatel",
        "category": "Corporate",
        "image": "/immagini/casi-di-successo/esg.webp",
        "description": (
            "Raggiungimento della certificazione ESG con livello C, "
            "confermando l'impegno dell'azienda verso sostenibilità, "
            "governance e responsabilità sociale."
        ),
        "tags": ["ESG", "Sostenibilità"],
        "body": """<p>La sostenibilità rappresenta un valore fondamentale per la crescita di Axatel. Per questo motivo l'azienda ha intrapreso un percorso volto a integrare i principi <b>ESG (Environmental, Social &amp; Governance)</b> all'interno delle proprie attività, ottenendo la certificazione con il livello <b>"C - Satisfactory Level of Sustainability"</b>.</p>

<p>Questo riconoscimento testimonia l'impegno concreto verso una gestione responsabile dell'azienda, orientata non solo all'innovazione tecnologica, ma anche alla tutela dell'ambiente, al benessere delle persone e a una governance trasparente.</p>

<h3>Un impegno concreto verso la sostenibilità</h3>

<p>Il percorso ESG di Axatel si basa su una strategia che coinvolge tutti gli aspetti dell'organizzazione, con l'obiettivo di creare valore nel lungo periodo per clienti, collaboratori, partner e territorio.</p>

<ul><li><b>Riduzione dell'impatto ambientale</b> attraverso processi più efficienti e tecnologie sostenibili.</li><li><b>Valorizzazione delle persone</b>, promuovendo inclusione, sicurezza e crescita professionale.</li><li><b>Governance trasparente</b> fondata su etica, responsabilità e rispetto delle normative.</li><li><b>Innovazione sostenibile</b> nello sviluppo di soluzioni IoT e Smart Infrastructure.</li></ul>

<h3>La tecnologia al servizio dell'ambiente</h3>

<p>Le soluzioni sviluppate da Axatel contribuiscono ogni giorno a rendere infrastrutture, città e territori più sicuri ed efficienti. Attraverso sistemi di <b>monitoraggio intelligente</b>, sensoristica IoT e piattaforme di supervisione, è possibile ridurre gli sprechi, ottimizzare le risorse e intervenire tempestivamente in caso di criticità.</p>

<p>L'innovazione tecnologica diventa così uno strumento concreto per favorire uno sviluppo più sostenibile, migliorando la qualità dei servizi e contribuendo alla tutela dell'ambiente.</p>

<h3>Guardare al futuro con responsabilità</h3>

<p>La certificazione ESG rappresenta un importante traguardo, ma soprattutto un punto di partenza. Axatel continuerà a investire in ricerca, innovazione e sostenibilità per sviluppare soluzioni sempre più affidabili, intelligenti e rispettose dell'ambiente, contribuendo alla costruzione di infrastrutture moderne e di un futuro più sostenibile.</p>

<p><b>Innovazione, responsabilità e sostenibilità</b> sono i principi che guidano ogni progetto Axatel e che continuano a creare valore per clienti, comunità e territorio.</p>""",
    },
    {
        "title": "Galleria Caltanissetta SS640 - Apertura canna sinistra",
        "slug": "galleria-caltanissetta-ss640-apertura-canna-sinistra",
        "client": "ANAS",
        "category": "Gallerie",
        "image": "/immagini/casi-di-successo/ss640.webp",
        "description": (
            "Supporto tecnologico per l'apertura della canna sinistra della "
            "galleria SS640 attraverso sistemi di monitoraggio e supervisione."
        ),
        "tags": ["Galleria", "Monitoraggio", "Smart Road"],
        "body": """<p>L'apertura della <b>canna sinistra della Galleria Caltanissetta SS640</b> ha rappresentato una fase importante nel percorso di completamento dell'infrastruttura. Axatel ha supportato il progetto contribuendo all'integrazione dei sistemi tecnologici necessari alla supervisione e alla gestione in sicurezza della tratta.</p>

<p>L'intervento ha richiesto il coordinamento di dispositivi di monitoraggio, automazione e controllo pensati per garantire continuità operativa e risposte rapide in caso di anomalie o condizioni critiche.</p>

<h3>Supporto all'apertura al traffico</h3>

<p>La messa in esercizio della canna sinistra ha beneficiato di una piattaforma di controllo capace di centralizzare le informazioni provenienti dagli impianti e di supportare gli operatori nelle attività di supervisione quotidiana.</p>

<ul><li><b>Supervisione degli impianti</b> tecnologici della galleria.</li><li><b>Monitoraggio in tempo reale</b> delle condizioni operative.</li><li><b>Gestione centralizzata</b> degli allarmi e delle segnalazioni.</li><li><b>Supporto alla sicurezza</b> per utenti e operatori.</li></ul>

<h3>Controllo e affidabilità</h3>

<p>L'integrazione dei sistemi consente di verificare costantemente lo stato dell'infrastruttura, individuare tempestivamente eventuali criticità e coordinare gli interventi in modo più efficiente.</p>

<p>La disponibilità di dati aggiornati e centralizzati permette agli operatori di mantenere alto il livello di sicurezza e di ridurre i tempi di risposta durante le fasi di esercizio.</p>

<h3>Infrastrutture più intelligenti</h3>

<p>Il progetto conferma il ruolo delle tecnologie di monitoraggio e automazione nella gestione delle infrastrutture moderne. Axatel continua a contribuire allo sviluppo di soluzioni per strade e gallerie più sicure, connesse e affidabili.</p>

<p><b>Supervisione, automazione e sicurezza</b> sono gli elementi che rendono la gestione della galleria più efficace e pronta a rispondere alle esigenze del traffico moderno.</p>""",
    },
    {
        "title": "Partnership TAV",
        "slug": "tav-partner-ideale-per-la-distribuzione-delle-nostre-soluzioni",
        "client": "TAV - Trans Audio Video",
        "category": "Partnership",
        "image": "/immagini/casi-di-successo/tav.webp",
        "description": (
            "Collaborazione strategica con TAV per distribuire le soluzioni "
            "Axatel sul mercato nazionale."
        ),
        "tags": ["Partner", "Distribuzione"],
        "body": """<p>Per rendere le proprie soluzioni sempre più accessibili sul territorio nazionale, Axatel ha avviato una collaborazione strategica con <b>TAV (Trans Audio Video)</b>, uno dei principali distributori italiani nel settore dell'Information Technology.</p>

<p>Questa partnership nasce con l'obiettivo di ampliare la rete commerciale e offrire a system integrator, installatori e rivenditori un accesso diretto alle soluzioni Axatel dedicate al <b>monitoraggio IoT</b>, alle <b>Smart Road</b> e alle <b>Smart City</b>.</p>

<h3>Una partnership strategica</h3>

<p>Grazie all'esperienza e alla capillarità di TAV nel mercato italiano, le tecnologie Axatel possono raggiungere un numero sempre maggiore di professionisti e aziende, garantendo un supporto commerciale e tecnico qualificato durante tutte le fasi del progetto.</p>

<ul><li><b>Distribuzione nazionale</b> delle soluzioni Axatel.</li><li><b>Supporto tecnico e commerciale</b> per partner e rivenditori.</li><li><b>Maggiore disponibilità dei prodotti</b> sul territorio italiano.</li><li><b>Collaborazione continua</b> per lo sviluppo di nuove opportunità di business.</li></ul>

<h3>Innovazione alla portata di tutti</h3>

<p>La collaborazione con TAV permette di mettere a disposizione del mercato un ecosistema completo di tecnologie dedicate al monitoraggio intelligente delle infrastrutture, al controllo ambientale e all'automazione, semplificando l'accesso alle soluzioni Axatel e accelerandone l'adozione in nuovi progetti.</p>

<p>Grazie a questa sinergia, clienti e partner possono contare su una filiera affidabile, competenze specialistiche e un servizio efficiente, dalla consulenza iniziale fino all'implementazione delle soluzioni.</p>

<h3>Un obiettivo comune</h3>

<p>La partnership tra <b>Axatel</b> e <b>TAV</b> rappresenta un importante passo nella diffusione delle tecnologie IoT sul territorio nazionale, con l'obiettivo di offrire strumenti sempre più innovativi per il monitoraggio, la sicurezza e la gestione intelligente delle infrastrutture.</p>

<p><b>Innovazione, competenza e collaborazione</b> sono i valori che guidano questa partnership, creando nuove opportunità per clienti, integratori e professionisti del settore.</p>""",
    },
    {
        "title": "Angel River",
        "slug": "angel-river-il-sistema-di-monitoraggio-dei-livelli-dei-corsi-dacqua",
        "client": "Pubbliche Amministrazioni",
        "category": "Monitoraggio Ambientale",
        "image": "/immagini/casi-di-successo/angel-river.webp",
        "description": (
            "Sistema IoT per il monitoraggio dei livelli dei corsi d'acqua "
            "con notifiche e allarmi in tempo reale."
        ),
        "tags": ["LoRaWAN", "Allerta", "Idrometria"],
        "body": """<p><b>Angel River</b> è la soluzione sviluppata da Axatel per il <b>monitoraggio intelligente dei livelli di fiumi, torrenti e bacini idrici</b>. Progettato per supportare enti pubblici, concessionarie stradali e gestori delle infrastrutture, il sistema consente di rilevare in tempo reale le variazioni del livello dell'acqua e prevedere l'evoluzione degli eventi di piena, contribuendo alla protezione del territorio e delle persone.</p>

<p>Basato su tecnologia <b>radar contactless</b>, Angel River monitora costantemente il comportamento dei corsi d'acqua senza entrare in contatto con l'acqua stessa, garantendo misurazioni affidabili anche durante eventi meteorologici estremi.</p>

<h3>Monitoraggio continuo dei corsi d'acqua</h3>

<p>La piattaforma acquisisce e analizza in tempo reale i dati provenienti dai sensori installati lungo l'asta fluviale, permettendo di individuare tempestivamente condizioni di rischio e fornendo agli operatori un quadro completo della situazione.</p>

<ul><li><b>Misurazione continua</b> del livello dei corsi d'acqua.</li><li><b>Tecnologia radar</b> ad alta affidabilità e senza contatto.</li><li><b>Monitoraggio dei flussi</b> per stimare l'evoluzione delle piene.</li><li><b>Raccolta dei parametri ambientali</b> per analisi e prevenzione.</li></ul>

<h3>Allerta automatica e protezione del territorio</h3>

<p>Quando vengono superate le soglie di sicurezza configurate, il sistema genera automaticamente gli allarmi previsti, inviando notifiche immediate agli enti competenti e attivando, ove installati, dispositivi di segnalazione acustica e visiva per avvisare la popolazione.</p>

<p>La piattaforma permette inoltre di personalizzare le soglie di intervento e le modalità di notifica in base alle caratteristiche del territorio e alle esigenze operative dell'ente gestore.</p>

<h3>Prevenzione attraverso i dati</h3>

<p>Oltre alla gestione delle emergenze, Angel River costruisce uno <b>storico completo delle misurazioni</b>, consentendo di analizzare il comportamento dei corsi d'acqua nel tempo e supportando le decisioni relative alla manutenzione, alla pianificazione e alla mitigazione del rischio idrogeologico.</p>

<p>Grazie all'integrazione tra <b>sensoristica IoT</b>, <b>monitoraggio in tempo reale</b> e <b>automazione degli allarmi</b>, Angel River rappresenta una soluzione completa per aumentare la sicurezza del territorio e ridurre i tempi di risposta durante gli eventi di piena.</p>""",
    },
    {
        "title": "Geo Angel - Tre anni di operatività",
        "slug": "3-anni-dallinstallazione-di-geo-angel",
        "client": "ANAS",
        "category": "Monitoraggio Frane",
        "image": "/immagini/casi-di-successo/geo-angel-3anni.webp",
        "description": (
            "Tre anni di funzionamento continuo del sistema Geo Angel per il "
            "monitoraggio di frane e dissesti lungo la rete stradale."
        ),
        "tags": ["Frane", "LoRaWAN", "Geo Angel"],
        "body": """<p>A tre anni dalla sua installazione, <b>Geo Angel</b> continua a dimostrare la propria affidabilità come sistema di <b>monitoraggio e allerta per il rischio franoso</b>. Progettato per garantire la sicurezza della viabilità in aree soggette a dissesto idrogeologico, il sistema opera ininterrottamente rilevando in tempo reale i movimenti del terreno e attivando automaticamente le procedure di emergenza.</p>

<p>La prima installazione è stata realizzata lungo la <b>SS51 Alemagna, in località Fadalto</b>, dove la tecnologia Axatel ha contribuito alla riapertura della viabilità anche nelle ore notturne, aumentando il livello di sicurezza per automobilisti e operatori.</p>

<h3>Monitoraggio intelligente del territorio</h3>

<p>Geo Angel utilizza una rete di sensori installati nelle aree a rischio per monitorare costantemente la stabilità del terreno e individuare tempestivamente eventuali movimenti anomali.</p>

<ul><li><b>Rilevamento continuo</b> dei movimenti franosi.</li><li><b>Attivazione automatica dei semafori</b> per bloccare la circolazione in caso di pericolo.</li><li><b>Monitoraggio video</b> tramite telecamere installate sulle aree controllate.</li><li><b>Gestione remota</b> attraverso piattaforma web e applicazione mobile.</li></ul>

<h3>Allerta immediata e controllo remoto</h3>

<p>Quando vengono superate le soglie di sicurezza configurate, il sistema genera automaticamente gli allarmi, inviando notifiche agli operatori e attivando i dispositivi di segnalazione presenti lungo la strada. La piattaforma consente inoltre di verificare in tempo reale lo stato dell'area monitorata grazie all'integrazione con il sistema di videosorveglianza.</p>

<p>Operatori e tecnici possono accedere in qualsiasi momento allo storico delle misurazioni, visualizzare lo stato dei sensori e gestire l'intero impianto da remoto tramite un'interfaccia intuitiva e sempre aggiornata.</p>

<h3>Tre anni di affidabilità sul campo</h3>

<p>Dalla sua messa in esercizio, <b>Geo Angel ha operato senza generare falsi allarmi</b>, confermando l'affidabilità della soluzione anche durante eventi meteorologici complessi. L'esperienza maturata sul campo dimostra come l'integrazione tra <b>sensoristica IoT</b>, <b>automazione</b> e <b>monitoraggio in tempo reale</b> rappresenti uno strumento fondamentale per la prevenzione del rischio idrogeologico.</p>

<p>Grazie a Geo Angel, Axatel continua a supportare enti pubblici e gestori delle infrastrutture nella protezione del territorio, contribuendo a rendere le strade più sicure e a ridurre i tempi di intervento durante le emergenze.</p>""",
    },
    {
        "title": "Nuove frane sul Fadalto",
        "slug": "nuove-frane-sul-fadalto-nuovo-record-per-geo-angel",
        "client": "ANAS",
        "category": "Protezione Civile",
        "image": "/immagini/casi-di-successo/fadalto.webp",
        "description": (
            "Il sistema Geo Angel rileva nuove colate detritiche e attiva "
            "automaticamente le procedure di sicurezza."
        ),
        "tags": ["Frane", "Allarmi", "Automazione"],
        "body": """<p>Nel corso degli anni il tratto della <b>SS51 Alemagna in località Fadalto</b> è stato interessato da numerosi eventi franosi che hanno rappresentato un rischio concreto per la sicurezza della circolazione. Per affrontare questa criticità, Axatel ha sviluppato <b>Geo Angel</b>, una piattaforma intelligente in grado di monitorare costantemente le aree instabili e attivare automaticamente le misure di sicurezza quando vengono rilevate situazioni di pericolo.</p>

<p>Anche durante i più recenti eventi franosi, il sistema ha dimostrato ancora una volta la propria affidabilità, individuando tempestivamente i movimenti del terreno e contribuendo alla protezione di automobilisti e operatori. Questo risultato conferma l'efficacia di una tecnologia progettata per intervenire prima che il rischio si trasformi in emergenza.</p>

<h3>Monitoraggio continuo del rischio</h3>

<p>Geo Angel controlla costantemente le aree soggette a dissesto attraverso una rete di sensori installati nei punti più critici, raccogliendo dati in tempo reale e analizzando ogni variazione del terreno.</p>

<ul><li><b>Monitoraggio H24</b> delle aree a rischio franoso.</li><li><b>Rilevamento immediato</b> di movimenti anomali del terreno.</li><li><b>Analisi continua</b> dei dati provenienti dalla sensoristica IoT.</li><li><b>Storico degli eventi</b> per supportare le attività di prevenzione e manutenzione.</li></ul>

<h3>Intervento automatico in caso di pericolo</h3>

<p>Quando vengono superate le soglie di sicurezza configurate, la piattaforma attiva automaticamente le procedure di emergenza, bloccando il traffico mediante semafori intelligenti, inviando notifiche agli enti competenti e consentendo agli operatori di verificare immediatamente la situazione attraverso i sistemi di supervisione.</p>

<p>L'automazione riduce drasticamente i tempi di reazione e permette di intervenire prima che il fenomeno possa mettere a rischio la sicurezza delle persone o compromettere la viabilità.</p>

<h3>Una tecnologia che continua a fare la differenza</h3>

<p>Ogni nuovo evento rappresenta una conferma dell'affidabilità di Geo Angel. La capacità di rilevare con precisione i fenomeni franosi e di attivare automaticamente le misure di protezione rende il sistema uno strumento fondamentale per la gestione del rischio idrogeologico lungo infrastrutture strategiche.</p>

<p>Grazie all'integrazione tra <b>sensoristica IoT</b>, <b>monitoraggio in tempo reale</b> e <b>automazione degli allarmi</b>, Axatel continua a supportare enti pubblici e gestori delle infrastrutture nella salvaguardia del territorio, contribuendo a rendere le strade più sicure e resilienti.</p>""",
    },
    {
        "title": "Nuova sede Axatel Sud Italia",
        "slug": "nuova-apertura-di-axatel",
        "client": "Axatel",
        "category": "Corporate",
        "image": "/immagini/casi-di-successo/sud-italia.webp",
        "description": (
            "Apertura della nuova sede operativa dedicata ai clienti del Sud "
            "Italia per garantire un supporto ancora più vicino al territorio."
        ),
        "tags": ["Azienda", "Espansione"],
        "body": """<p>Con l'apertura della nuova sede nel Sud Italia, Axatel compie un importante passo nel proprio percorso di crescita, rafforzando la presenza sul territorio nazionale e avvicinandosi ancora di più a clienti, partner e pubbliche amministrazioni.</p>

<p>La nuova sede nasce con l'obiettivo di offrire un supporto ancora più rapido e diretto nello sviluppo di soluzioni dedicate al <b>monitoraggio IoT</b>, alle <b>Smart Road</b>, alle <b>Smart City</b> e alla gestione intelligente delle infrastrutture, mettendo a disposizione competenze tecniche e servizi di assistenza sempre più vicini alle esigenze del territorio.</p>

<h3>Una presenza sempre più capillare</h3>

<p>L'espansione nel Sud Italia rappresenta un investimento strategico che consente ad Axatel di seguire con maggiore efficienza progetti distribuiti su tutto il territorio nazionale, garantendo tempi di risposta più rapidi e un supporto tecnico qualificato.</p>

<ul><li><b>Maggiore vicinanza ai clienti</b> e agli enti pubblici.</li><li><b>Supporto tecnico e commerciale</b> direttamente sul territorio.</li><li><b>Riduzione dei tempi di intervento</b> durante le fasi di installazione e assistenza.</li><li><b>Nuove opportunità di collaborazione</b> con partner locali e system integrator.</li></ul>

<h3>Innovazione senza confini</h3>

<p>La nuova sede permetterà di accelerare la diffusione delle tecnologie Axatel in nuove aree del Paese, favorendo lo sviluppo di progetti dedicati alla sicurezza delle infrastrutture, al monitoraggio ambientale e alla digitalizzazione dei servizi pubblici e privati.</p>

<p>L'esperienza maturata in anni di attività nel settore delle infrastrutture intelligenti viene così messa a disposizione di un numero sempre maggiore di realtà, contribuendo alla realizzazione di sistemi sempre più affidabili, connessi e orientati alla prevenzione.</p>

<h3>Uno sguardo al futuro</h3>

<p>L'apertura della sede nel Sud Italia non rappresenta soltanto un'espansione geografica, ma conferma la volontà di Axatel di continuare a investire in innovazione, ricerca e presenza sul territorio, costruendo relazioni solide con clienti e partner e sostenendo lo sviluppo di nuove infrastrutture intelligenti.</p>

<p><b>Crescita, innovazione e prossimità</b> sono i valori che guidano questa nuova fase del percorso di Axatel, con l'obiettivo di offrire soluzioni sempre più efficaci per un futuro connesso e sicuro.</p>""",
    },
    {
        "title": "Geo Angel in azione",
        "slug": "geo-angel-il-sistema-di-axatel-di-nuovo-in-azione",
        "client": "ANAS",
        "category": "Monitoraggio Frane",
        "image": "/immagini/casi-di-successo/geo-angel.webp",
        "description": (
            "Il sistema Geo Angel interviene nuovamente durante un evento "
            "franoso, contribuendo alla sicurezza della viabilità."
        ),
        "tags": ["Frane", "Monitoraggio", "Smart Road"],
        "body": """<p>La sicurezza della viabilità nelle aree soggette a rischio idrogeologico richiede sistemi in grado di intervenire in modo rapido e automatico. Con <b>Geo Angel</b>, Axatel ha sviluppato una piattaforma intelligente capace di rilevare in tempo reale i movimenti del terreno e attivare immediatamente le misure di protezione, riducendo il rischio per automobilisti e operatori.</p>

<p>Anche durante un recente evento franoso lungo la <b>SS51 Alemagna</b>, il sistema ha dimostrato ancora una volta la propria efficacia, rilevando il fenomeno e contribuendo alla gestione della viabilità attraverso l'attivazione automatica dei dispositivi di sicurezza installati sul territorio.</p>

<h3>Monitoraggio continuo H24</h3>

<p>Geo Angel utilizza una rete di sensori IoT installati nei punti più critici per controllare costantemente la stabilità dei versanti e individuare qualsiasi movimento anomalo prima che possa trasformarsi in un pericolo per la circolazione.</p>

<ul><li><b>Controllo continuo</b> delle aree a rischio franoso.</li><li><b>Rilevamento immediato</b> di movimenti del terreno.</li><li><b>Analisi in tempo reale</b> dei dati provenienti dai sensori.</li><li><b>Storico completo degli eventi</b> per supportare analisi e manutenzione.</li></ul>

<h3>Allerta automatica e gestione della viabilità</h3>

<p>Al superamento delle soglie configurate, la piattaforma genera automaticamente gli allarmi e attiva i dispositivi di segnalazione presenti lungo la strada, come semafori intelligenti, sirene e notifiche agli enti competenti. Questo permette di limitare immediatamente l'accesso alle aree interessate e ridurre drasticamente i tempi di intervento.</p>

<p>L'intero impianto è supervisionabile da remoto attraverso la piattaforma Axatel, consentendo agli operatori di verificare in tempo reale la situazione, consultare le immagini delle telecamere e coordinare rapidamente le operazioni di emergenza.</p>

<h3>Tecnologia al servizio della prevenzione</h3>

<p>Ogni nuovo evento conferma il valore di un approccio basato sulla prevenzione. Grazie all'integrazione tra <b>sensoristica IoT</b>, <b>automazione</b> e <b>monitoraggio in tempo reale</b>, Geo Angel rappresenta una soluzione affidabile per la protezione delle infrastrutture stradali e la salvaguardia delle persone.</p>

<p>L'esperienza maturata sul campo continua a dimostrare come la tecnologia possa trasformare il monitoraggio del territorio in uno strumento concreto di sicurezza, supportando enti pubblici e gestori delle infrastrutture nella gestione del rischio idrogeologico.</p>""",
    },
]
