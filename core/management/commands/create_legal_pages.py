"""
Create the Privacy policy and Cookie policy pages as DRAFTS, from a template
written for what this site actually does (forms, CV uploads, chatbot log,
server logs; no tracking cookies, videos load only on click).

    python manage.py create_legal_pages --dry-run
    python manage.py create_legal_pages

The pages are /privacy-policy and /cookie-policy (Pagina generica under
Home). They are linked in Impostazioni → Footer → Pagine legali, so the
footer and the consent checkbox of every form point to them as soon as they
are published. Text in [square brackets] must be completed and the whole
text checked by Axatel's privacy adviser before pressing Pubblica.
Running it again changes nothing once the pages exist.
"""
from django.core.management.base import BaseCommand
from wagtail.models import Site
from wagtail.rich_text import RichText

PRIVACY = """
<p><b>[BOZZA DA VERIFICARE CON IL CONSULENTE PRIVACY PRIMA DELLA PUBBLICAZIONE. Completa le parti tra parentesi quadre.]</b></p>
<p>Questa informativa spiega quali dati personali tratta il sito di Axatel, perché e per quanto tempo, ai sensi degli articoli 13 e 14 del Regolamento (UE) 2016/679 (GDPR).</p>
<h2>1. Titolare del trattamento</h2>
<p>Axatel S.r.l., Viale del Mercato Nuovo 75, 36100 Vicenza (VI), P.IVA [DA COMPLETARE]. Per qualsiasi domanda sui tuoi dati: <a href="mailto:info@axatel.it">info@axatel.it</a> [o indirizzo privacy dedicato].</p>
<h2>2. Quali dati trattiamo</h2>
<ul>
<li><b>Dati inviati con i moduli</b> (contatti, preventivi, candidature, proposte di collaborazione): nome, azienda, e-mail, telefono, messaggio, eventuale documento o CV allegato, lingua del sito usata e conferma della presa visione di questa informativa.</li>
<li><b>Domande al chatbot</b>: solo il testo della domanda, senza nome, indirizzo IP o altri dati che identifichino chi scrive. Non inserire dati personali nelle domande.</li>
<li><b>Dati di navigazione</b>: il server registra per motivi di sicurezza l'indirizzo IP, la data e l'ora e la pagina richiesta.</li>
</ul>
<h2>3. Perché li trattiamo e su quale base</h2>
<ul>
<li>Rispondere alle richieste di informazioni e preventivo: esecuzione di misure precontrattuali richieste dall'interessato (art. 6.1.b GDPR).</li>
<li>Valutare le candidature spontanee: art. 6.1.b GDPR e art. 111-bis del D.Lgs. 196/2003.</li>
<li>Proteggere il sito da abusi e attacchi e migliorare le risposte del chatbot: legittimo interesse del titolare (art. 6.1.f GDPR).</li>
</ul>
<p>Il conferimento dei dati richiesti nei moduli è necessario per rispondere; senza di essi la richiesta non può essere inviata. Non usiamo i dati per marketing né per profilazione e non prendiamo decisioni automatizzate.</p>
<h2>4. Dove e come</h2>
<p>I dati sono conservati su server situati nell'Unione Europea [verificare: Aruba S.p.A., Italia]. La traduzione automatica e il chatbot funzionano sui nostri server: i testi non vengono inviati a servizi esterni.</p>
<h2>5. Chi può vederli</h2>
<p>Il personale di Axatel autorizzato e i fornitori che gestiscono per nostro conto il server [Aruba S.p.A.] e la posta elettronica [DA COMPLETARE], nominati responsabili del trattamento. I dati non sono diffusi e non sono trasferiti fuori dall'Unione Europea [verificare con il fornitore di posta].</p>
<h2>6. Per quanto tempo</h2>
<ul>
<li>Richieste di contatto e preventivo: [24 mesi] dall'ultimo contatto.</li>
<li>Candidature e CV: [12 mesi], salvo assunzione.</li>
<li>Domande al chatbot: 180 giorni.</li>
<li>Registri del server: [14 giorni].</li>
</ul>
<h2>7. I tuoi diritti</h2>
<p>Puoi chiedere in ogni momento l'accesso ai tuoi dati, la rettifica, la cancellazione, la limitazione o l'opposizione al trattamento e la portabilità (articoli 15–22 GDPR), scrivendo a <a href="mailto:info@axatel.it">info@axatel.it</a>. Hai inoltre diritto di proporre reclamo al Garante per la protezione dei dati personali (<a href="https://www.garanteprivacy.it">www.garanteprivacy.it</a>).</p>
<h2>8. Cookie</h2>
<p>Il sito non usa cookie di profilazione né di statistica: i dettagli sono nella Cookie policy.</p>
<p>Ultimo aggiornamento: [DATA].</p>
"""

COOKIE = """
<p><b>[BOZZA DA VERIFICARE PRIMA DELLA PUBBLICAZIONE. Aggiornarla se si aggiungono statistiche, mappe, chat esterne o altri servizi di terze parti.]</b></p>
<p>Questo sito usa solo strumenti tecnici, necessari al suo funzionamento. Non usa cookie di profilazione, pubblicità o statistiche di terze parti: per questo non mostra un banner per il consenso (Linee guida del Garante privacy del 10 giugno 2021).</p>
<h2>Cosa viene salvato nel tuo browser</h2>
<ul>
<li><b>ax-blog-seen</b> (memoria del browser): ricorda quali news hai già visto, per il pallino nel menu. Resta nel tuo browser finché non la cancelli; non viene inviata a noi.</li>
<li><b>alarms</b> (memoria del browser): gli eventi della demo interattiva in homepage. Resta nel tuo browser; il pulsante "Reset" della demo la svuota.</li>
<li><b>sessionid, csrftoken</b> (cookie tecnici): solo per chi accede all'area riservata di gestione del sito (/cms/); servono a mantenere l'accesso e a proteggere i moduli.</li>
</ul>
<h2>Video</h2>
<p>I video di YouTube o Vimeo inseriti nelle pagine non vengono caricati finché non premi play. Da quel momento il video è fornito da YouTube (in modalità privacy avanzata, youtube-nocookie.com) o da Vimeo (con "do not track"), secondo le loro informative.</p>
<h2>Come gestirli</h2>
<p>Puoi cancellare la memoria del browser e i cookie in qualsiasi momento dalle impostazioni del tuo browser. Il sito continuerà a funzionare.</p>
<p>Ultimo aggiornamento: [DATA].</p>
"""

PAGES = [
    ("privacy", "Privacy policy", "privacy-policy", PRIVACY,
     "Come Axatel tratta i dati personali raccolti dal sito: moduli di contatto, candidature, chatbot e navigazione."),
    ("cookie", "Cookie policy", "cookie-policy", COOKIE,
     "Il sito Axatel usa solo strumenti tecnici: nessun cookie di profilazione o di statistica di terze parti."),
]


class Command(BaseCommand):
    help = "Create draft Privacy policy and Cookie policy pages and link them in the footer settings."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, dry_run=False, **options):
        from core.site_settings import FooterSettings
        from home.models import FlexPage, HomePage

        home = HomePage.objects.filter(locale__language_code="it").first()
        if home is None:
            self.stderr.write("No Italian Home page found.")
            return
        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        footer = FooterSettings.for_site(site)
        changed = False
        for kind, title, slug, text, description in PAGES:
            page = FlexPage.objects.child_of(home).filter(slug=slug).first()
            if page:
                self.stdout.write(f"= /{slug}: already there ({'published' if page.live else 'draft'})")
            elif dry_run:
                self.stdout.write(f"+ /{slug}: would create the draft '{title}'")
            else:
                page = FlexPage(title=title, slug=slug, live=False, search_description=description,
                                body=[("rich_text", RichText(text.strip()))])
                home.add_child(instance=page)
                page.save_revision(log_action=True)
                self.stdout.write(self.style.SUCCESS(f"+ /{slug}: draft '{title}' created — complete it, have it checked, publish"))
            field = f"{kind}_page"
            if page and not dry_run and getattr(footer, f"{field}_id") != page.pk:
                setattr(footer, field, page)
                changed = True
                self.stdout.write(f"  linked in Impostazioni → Footer → Pagine legali")
        if changed:
            footer.save()
