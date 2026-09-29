"""The "Cosa monitoriamo?" topics as they were written in the frontend
(app/data/monitoring.ts), used once by `manage.py seed_monitoring`.
Edit the pages in the CMS, not here.

Topics marked "coming-soon" are not created in the CMS: the site keeps
showing its "coming soon" page for them until someone writes the page."""

DEFAULT_TOPICS = [{'slug': 'alberi',
  'title': 'Monitoraggio alberi',
  'group': 'Ambiente',
  'eyebrow': 'Verde pubblico',
  'introduction': 'Stiamo preparando una pagina dedicata alle soluzioni Axatel per il controllo del '
                  'patrimonio arboreo.',
  'status': 'coming-soon',
  'image': '',
  'image_alt': '',
  'feature': None,
  'sections': [],
  'feature_product': ''},
 {'slug': 'aria',
  'title': 'Monitoraggio aria',
  'group': 'Ambiente',
  'eyebrow': 'Qualita ambientale',
  'introduction': 'Dati ambientali continui aiutano amministrazioni e gestori a conoscere la qualita '
                  "dell'aria e a prendere decisioni piu consapevoli.",
  'status': 'published',
  'image': '',
  'image_alt': '',
  'feature': {'label': 'La soluzione Axatel',
              'name': 'Cerere Pro Aria',
              'description': 'Sistema radio LoRaWAN per rilevare in tempo reale gli inquinanti atmosferici e '
                             'rendere disponibili i dati alla piattaforma di supervisione.',
              'href': 'https://www.axatel.it/wp-content/uploads/2026/03/2025_CERERE-PRO-ARIA-PALO.pdf',
              'hrefLabel': 'Scheda tecnica'},
  'sections': [{'title': 'Misure continue e capillari',
                'paragraphs': ['La stazione misura parametri meteo, temperatura, pressione, umidita, '
                               "velocita e direzione del vento. Per la qualita dell'aria rileva CO, CO2, "
                               'NOx, NO2, SO2, O3, particolato e TVOC.',
                               "L'alimentazione autonoma e la comunicazione senza SIM dati rendono la "
                               'soluzione adatta anche a siti privi di rete elettrica o connettivita '
                               'tradizionale.'],
                'highlights': ['Inquinanti e particolato', 'Meteo locale', 'Installazione autonoma']},
               {'title': 'Controllo e storico',
                'paragraphs': ['Il portale web mostra i dati su mappe, grafici e andamenti per singolo '
                               'inquinante. Le misure storiche vengono conservate in cloud e possono essere '
                               'pubblicate sul web.',
                               'Soglie configurabili, allarmi, esportazione verso database esterni e '
                               'consultazione mobile completano la gestione da remoto.']}],
  'feature_product': 'cerere-pro-aria'},
 {'slug': 'fiumi',
  'title': 'Monitoraggio fiumi',
  'group': 'Ambiente',
  'eyebrow': 'Rischio idraulico',
  'introduction': 'Il controllo continuo del livello fluviale porta sul territorio informazioni utili per la '
                  'prevenzione e la gestione tempestiva delle criticita.',
  'status': 'published',
  'image': 'AngelRiver.png',
  'image_alt': "Sistema Angel River per il monitoraggio dei corsi d'acqua",
  'feature': {'label': 'La soluzione Axatel',
              'name': 'Angel River',
              'description': "Sistema per monitorare corsi d'acqua e bacini, con rilevamento dei livelli e "
                             'allerta di emergenza.',
              'href': 'https://www.axatel.it/wp-content/uploads/2026/03/2025_ANGEL-RIVER.pdf',
              'hrefLabel': 'Scheda tecnica'},
  'sections': [{'title': 'Livelli e allerta',
                'paragraphs': ['La dashboard mostra in tempo reale gli ultimi dati ricevuti e consente di '
                               'restringere la vista a un sensore, un oggetto idrico o una zona geografica.',
                               'Al superamento dei livelli impostati il sistema invia segnalazioni, pubblica '
                               'gli andamenti e puo attivare un allarme acustico in broadcast.'],
                'highlights': ['Dati real-time', 'Soglie di allarme', 'Mappe georeferenziate']},
               {'title': 'Un sistema completo',
                'paragraphs': ['La soluzione integra sensori, network server LoRaWAN, middleware e software '
                               'Axatel. Le console sono disponibili presso il cliente o come servizio web.',
                               'Storico, aggregazioni temporali ed esportazione dei dati supportano '
                               'Protezione Civile, consorzi di bonifica e gestori di sottopassi, bacini e '
                               'attraversamenti stradali.']}],
  'feature_product': 'angel-river'},
 {'slug': 'frane',
  'title': 'Monitoraggio frane',
  'group': 'Ambiente',
  'eyebrow': 'Dissesto idrogeologico',
  'introduction': 'Il monitoraggio dei versanti instabili rende osservabili nel tempo i fenomeni di dissesto '
                  'e supporta la sicurezza delle infrastrutture esposte.',
  'status': 'published',
  'image': 'GeoAngel.png',
  'image_alt': 'Sistema Geo Angel per il monitoraggio dei dissesti',
  'feature': {'label': 'La soluzione Axatel',
              'name': 'Geo Angel',
              'description': "Sistema real-time per il monitoraggio dei dissesti geologici e l'automazione "
                             'delle procedure di emergenza.',
              'href': 'https://www.axatel.it/wp-content/uploads/2026/03/2026_GEO-ANGEL.pdf',
              'hrefLabel': 'Scheda tecnica'},
  'sections': [{'title': 'Rilevazione e risposta',
                'paragraphs': ['Sensori georeferenziati rilevano i movimenti del terreno; accelerometri '
                               'installati su reti paramassi o barriere estendono il controllo ai punti '
                               'critici.',
                               'In caso di pericolo, semafori, pannelli a messaggio variabile e sirene '
                               'possono avvisare gli utenti e bloccare rapidamente la circolazione.'],
                'highlights': ['Movimenti del terreno', 'Reti paramassi', 'Automazioni di emergenza']},
               {'title': 'Supervisione centralizzata',
                'paragraphs': ['Il portale web visualizza dati, grafici e andamenti su mappe cartografiche, '
                               'conserva lo storico e permette di impostare soglie e frequenze di '
                               'aggiornamento.',
                               'La stazione meteo locale correla vento, pioggia, temperatura e umidita con '
                               'le misure del dissesto.']}],
  'feature_product': 'geo-angel'},
 {'slug': 'traffico',
  'title': 'Monitoraggio traffico',
  'group': 'Viabilità',
  'eyebrow': 'Smart mobility',
  'introduction': 'Conteggio dei veicoli, dati di mobilita e sistemi di controllo concorrono a una gestione '
                  'piu sicura ed efficiente della rete stradale.',
  'status': 'published',
  'image': 'TrafficAlert.png',
  'image_alt': 'Sistema Traffic Alert per la videoanalisi stradale',
  'feature': {'label': 'La soluzione Axatel',
              'name': 'Traffic Alert',
              'description': 'Sistema di videoanalisi real-time per generare e gestire allarmi relativi al '
                             'traffico stradale.',
              'href': 'https://www.axatel.it/wp-content/uploads/2026/03/traffic-alert.pdf',
              'hrefLabel': 'Scheda tecnica'},
  'sections': [{'title': 'Eventi rilevati in tempo reale',
                'paragraphs': ['Le telecamere riconoscono incidenti, code, veicoli fermi e guida contromano '
                               "attraverso il software di bordo, generando l'allarme senza attendere una "
                               'verifica manuale.',
                               'Snapshot e flussi video real-time permettono agli operatori di analizzare '
                               "l'evento e correggere gli eventuali falsi allarmi."],
                'highlights': ['Incidenti e code', 'Veicoli fermi', 'Guida contromano']},
               {'title': "Dall'allarme all'intervento",
                'paragraphs': ["Il programma di routing inoltra gli eventi all'applicazione web, ad Angel "
                               "BPM e a SCADA. L'operatore consulta l'archivio, gestisce soglie, anagrafiche "
                               'e progressive chilometriche.',
                               'La piattaforma puo pianificare gli interventi di soccorso e integrare '
                               'automazioni di campo come pannelli a messaggio variabile, semafori e sistemi '
                               'di allarme.']}],
  'feature_product': 'traffic-alert'},
 {'slug': 'cantieri',
  'title': 'Monitoraggio cantieri',
  'group': 'Viabilità',
  'eyebrow': 'Sicurezza stradale',
  'introduction': 'Tecnologie connesse supportano il tracciamento e la sicurezza dei cantieri stradali, '
                  'anche in contesti distribuiti lungo la rete.',
  'status': 'published',
  'image': 'AngelRoadsite.png',
  'image_alt': 'Sistema Angel Road Site per i cantieri stradali',
  'feature': {'label': 'La soluzione Axatel',
              'name': 'Angel Road Site',
              'description': 'Sistema real-time per il tracciamento e il controllo dello stato di sicurezza '
                             'nei cantieri stradali.',
              'href': 'https://www.axatel.it/wp-content/uploads/2026/03/2026_ANGEL-ROAD-SITE.pdf',
              'hrefLabel': 'Scheda tecnica'},
  'sections': [{'title': 'Persone, mezzi e segnaletica',
                'paragraphs': ["Sensori GPS tracciano cartelli e mezzi d'opera; dispositivi dedicati seguono "
                               'gli spostamenti degli operatori e segnalano condizioni di uomo a terra.',
                               'Urti, ribaltamenti o spostamenti della segnaletica vengono notificati in '
                               'tempo reale per consentire un ripristino rapido.'],
                'highlights': ['Tracciamento GPS', 'Uomo a terra', 'Urti alla segnaletica']},
               {'title': 'Controllo operativo',
                'paragraphs': ['La console remota visualizza posizione del cantiere, operatori, cartelli e '
                               'mezzi. Telecamere e radar aggiungono analisi del traffico, conteggio dei '
                               'veicoli, velocita e traiettorie.',
                               'Mappe georeferenziate possono importare il progetto da DWG; allarmi e '
                               'situazioni critiche sono disponibili anche su dispositivi mobili.']}],
  'feature_product': 'angel-road-site'},
 {'slug': 'gallerie',
  'title': 'Monitoraggio gallerie',
  'group': 'Viabilità',
  'eyebrow': 'Infrastrutture stradali',
  'introduction': 'Stiamo preparando una pagina dedicata alle soluzioni Axatel per la supervisione e la '
                  'sicurezza delle gallerie.',
  'status': 'coming-soon',
  'image': '',
  'image_alt': '',
  'feature': None,
  'sections': [],
  'feature_product': ''},
 {'slug': 'ponti',
  'title': 'Monitoraggio ponti',
  'group': 'Strutture',
  'eyebrow': 'Monitoraggio strutturale',
  'introduction': 'La conoscenza continua del comportamento di ponti e viadotti aiuta i gestori a seguire '
                  'nel tempo lo stato delle opere.',
  'status': 'published',
  'image': 'AngelBridge.png',
  'image_alt': 'Sistema Angel Bridge per il monitoraggio strutturale',
  'feature': {'label': 'La soluzione Axatel',
              'name': 'Angel Bridge',
              'description': 'Sistema hardware e software per il monitoraggio strutturale di ponti, '
                             'cavalcavia e costruzioni mediante tecnologia radio LoRaWAN.',
              'href': 'https://www.axatel.it/wp-content/uploads/2026/03/2026_ANGEL-BRIDGE.pdf',
              'hrefLabel': 'Scheda tecnica'},
  'sections': [{'title': "Misurare il comportamento dell'opera",
                'paragraphs': ['Kit di sensori strutturali, fessurimetri, inclinometri e accelerometri '
                               'raccolgono le misure e le trasmettono attraverso la rete LoRaWAN.',
                               'Soglie configurabili attivano avvisi di guardia o allarme; dashboard e mappe '
                               'mostrano gli ultimi dati per sensore, struttura o area geografica.'],
                'highlights': ['Fessurimetri', 'Inclinometri', 'Accelerometri']},
               {'title': 'Dati disponibili ovunque',
                'paragraphs': ['Console web e app mobile consentono la consultazione remota, la ricerca '
                               "nello storico e l'esportazione delle misure.",
                               'La cartografia vettoriale e le piante costruttive DWG possono completare i '
                               'sinottici; il sistema e integrabile con automazione SCADA.']}],
  'feature_product': 'angel-bridge'},
 {'slug': 'edifici',
  'title': 'Monitoraggio edifici',
  'group': 'Strutture',
  'eyebrow': 'Monitoraggio strutturale',
  'introduction': 'Il monitoraggio connesso estende agli edifici una lettura continua e centralizzata dei '
                  'parametri strutturali.',
  'status': 'published',
  'image': 'AngelBridge.png',
  'image_alt': 'Sistema Angel Bridge applicato agli edifici',
  'feature': {'label': 'La soluzione Axatel',
              'name': 'Angel Bridge',
              'description': 'Sistema hardware e software per il monitoraggio strutturale di edifici, '
                             'monumenti e altre costruzioni in tecnologia radio LoRaWAN.',
              'href': 'https://www.axatel.it/wp-content/uploads/2026/03/2026_ANGEL-BRIDGE.pdf',
              'hrefLabel': 'Scheda tecnica'},
  'sections': [{'title': 'Controllo di edifici e costruzioni',
                'paragraphs': ['Fessurimetri, inclinometri, accelerometri e altri sensori strutturali '
                               'seguono nel tempo gli edifici, anche nelle adiacenze di cantieri o in aree '
                               'sismiche.',
                               'Il sistema e indicato per amministrazioni, Protezione Civile, gestori '
                               'immobiliari e per il monitoraggio di monumenti.'],
                'highlights': ['Edifici', 'Monumenti', 'Aree sismiche']},
               {'title': 'Una vista unica sui dati',
                'paragraphs': ['La dashboard filtra le misure per sensore, costruzione o zona geografica, '
                               'conserva lo storico e invia segnalazioni al superamento delle soglie.',
                               'La soluzione opera anche in zone con scarsa copertura cellulare e puo '
                               'rappresentare gli impianti su mappe indoor o piante DWG.']}],
  'feature_product': 'angel-bridge'}]
