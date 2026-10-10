from django import forms
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField
from core.api_blocks import PageChooserBlock


def _visible(value) -> bool:
    """Entries saved before the "Visibile" switch existed count as visible."""
    flag = value.get("visible")
    return True if flag is None else bool(flag)


def _label(value, context) -> str:
    """Menu label in the requested language (?locale=en → label_en),
    falling back to the Italian label when no translation was entered."""
    language = (context or {}).get("locale")
    if language and language != "it":
        translated = (value.get(f"label_{language}") or "").strip()
        if translated:
            return translated
    return value.get("label", "")


class NavSubLinkBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=60, help_text="Testo del link, es. 'Sensori'")
    label_en = blocks.CharBlock(max_length=60, required=False, label="Etichetta EN")
    label_fr = blocks.CharBlock(max_length=60, required=False, label="Etichetta FR")
    visible = blocks.BooleanBlock(
        required=False, default=True, label="Visibile",
        help_text="Togli la spunta per nascondere questa voce dal sito senza cancellarla.",
    )
    page = PageChooserBlock(
        required=False,
        help_text="Preferito: collega una pagina reale del sito. L'URL resta sempre corretto anche se cambia lo slug.",
    )
    custom_url = blocks.CharBlock(
        max_length=200, required=False,
        help_text="Usa SOLO per ancore (#sezione) o link esterni. Ignorato se sopra è selezionata una pagina.",
    )
    open_in_new_tab = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "link"
        label = "Link"

    def get_api_representation(self, value, context=None):
        page_block = self.child_blocks["page"]
        page_repr = page_block.get_api_representation(value.get("page"), context=context) if value.get("page") else None
        return {
            "label": _label(value, context),
            "href": page_repr["url"] if page_repr else value.get("custom_url", ""),
            "open_in_new_tab": bool(value.get("open_in_new_tab")),
            "visible": _visible(value),
        }


NAV_COLUMN_CHOICES = [("", "Automatica"), ("1", "Colonna 1 (sinistra)"), ("2", "Colonna 2"), ("3", "Colonna 3")]


class NavGroupBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=60, help_text="Titolo colonna, es. 'Piattaforme'")
    label_en = blocks.CharBlock(max_length=60, required=False, label="Etichetta EN")
    label_fr = blocks.CharBlock(max_length=60, required=False, label="Etichetta FR")
    visible = blocks.BooleanBlock(
        required=False, default=True, label="Visibile",
        help_text="Togli la spunta per nascondere questa voce dal sito senza cancellarla.",
    )
    column = blocks.ChoiceBlock(
        choices=NAV_COLUMN_CHOICES, default="", required=False, label="Colonna",
        help_text="Dove sta il gruppo nel menu a tendina (da computer). Automatica = sotto la colonna più corta. "
                  "Più gruppi nella stessa colonna stanno uno sotto l'altro, nell'ordine dell'elenco.",
    )
    links = blocks.ListBlock(NavSubLinkBlock())

    class Meta:
        icon = "list-ul"
        label = "Gruppo (colonna del menu a tendina)"

    def get_api_representation(self, value, context=None):
        links_block = self.child_blocks["links"]
        links = [link for link in value.get("links", []) if _visible(link)]
        column = str(value.get("column") or "")
        return {
            "label": _label(value, context),
            "visible": _visible(value),
            "column": int(column) if column.isdigit() else None,
            "links": links_block.get_api_representation(links, context=context),
        }


class NavItemBlock(blocks.StructBlock):
    """One entry in the top navbar. Leave `groups` empty for a plain
    direct link (e.g. 'Casi di successo'); fill it in for a dropdown
    (e.g. 'Come lo realizziamo?')."""
    label = blocks.CharBlock(max_length=60)
    label_en = blocks.CharBlock(max_length=60, required=False, label="Etichetta EN")
    label_fr = blocks.CharBlock(max_length=60, required=False, label="Etichetta FR")
    visible = blocks.BooleanBlock(
        required=False, default=True, label="Visibile",
        help_text="Togli la spunta per nascondere questa voce dal sito senza cancellarla.",
    )
    page = PageChooserBlock(required=False, help_text="Per un link diretto senza tendina.")
    custom_url = blocks.CharBlock(max_length=200, required=False)
    groups = blocks.ListBlock(
        NavGroupBlock(), required=False,
        help_text="Aggiungi una o più colonne per un menu a tendina. Lascia vuoto per un link diretto.",
    )

    class Meta:
        icon = "arrow-down-big"
        label = "Voce di menu"

    def get_api_representation(self, value, context=None):
        page_block = self.child_blocks["page"]
        groups_block = self.child_blocks["groups"]
        page_repr = page_block.get_api_representation(value.get("page"), context=context) if value.get("page") else None
        return {
            "label": _label(value, context),
            "href": page_repr["url"] if page_repr else (value.get("custom_url") or None),
            "visible": _visible(value),
            "groups": groups_block.get_api_representation(
                [group for group in value.get("groups", []) if _visible(group)], context=context
            ),
        }


@register_setting(icon="list-ul")
class NavigationSettings(BaseSiteSetting):
    """Navbar structure + the header CTA button.

    STEP: replaces the old flat `links` StreamField (NavLinkBlock) with
    `items` (NavItemBlock), which can represent grouped dropdowns.
    """

    items = StreamField(
        [("item", NavItemBlock())],
        use_json_field=True,
        blank=True,
        verbose_name="Voci del menu",
        help_text="Ordine e contenuto del menu principale, incluse le tendine.",
    )

    cta_label = models.CharField(
        max_length=60, blank=True, default="Parla con un esperto",
        verbose_name="Testo pulsante header",
    )
    cta_url = models.CharField(
        max_length=200, blank=True, default="/contatti",
        verbose_name="URL pulsante header",
    )
    cta_visible = models.BooleanField(
        default=True, verbose_name="Mostra pulsante header",
    )
    cta_label_en = models.CharField(max_length=60, blank=True, verbose_name="Testo pulsante header (EN)")
    cta_label_fr = models.CharField(max_length=60, blank=True, verbose_name="Testo pulsante header (FR)")

    panels = [
        FieldPanel("items"),
        MultiFieldPanel([
            FieldPanel("cta_visible"),
            FieldPanel("cta_label"),
            FieldPanel("cta_label_en"),
            FieldPanel("cta_label_fr"),
            FieldPanel("cta_url"),
        ], heading="Pulsante header"),
    ]

    class Meta:
        verbose_name = "Navigazione"


class FooterContactBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=60, help_text="Es. 'Chiamaci'")
    value = blocks.CharBlock(max_length=200, help_text="Es. '+39 0444 963891'")
    href = blocks.CharBlock(
        max_length=250,
        help_text="Es. 'tel:+390444963891', 'mailto:info@axatel.it', o un URL",
    )
    external = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "mail"
        label = "Contatto footer"


SOCIAL_CHOICES = [
    ("linkedin", "LinkedIn"),
    ("facebook", "Facebook"),
    ("instagram", "Instagram"),
    ("youtube", "YouTube"),
    ("x", "X (Twitter)"),
    ("other", "Altro"),
]


class SocialLinkBlock(blocks.StructBlock):
    network = blocks.ChoiceBlock(choices=SOCIAL_CHOICES, default="linkedin", label="Social")
    url = blocks.URLBlock(label="Indirizzo della pagina")
    label = blocks.CharBlock(max_length=40, required=False, label="Nome mostrato",
                             help_text="Vuoto = il nome del social (es. 'Facebook').")
    visible = blocks.BooleanBlock(required=False, default=True, label="Visibile")

    class Meta:
        icon = "link-external"
        label = "Social"


@register_setting(icon="site")
class FooterSettings(BaseSiteSetting):
    """Footer contacts and company registration details."""

    contacts = StreamField(
        [("contact", FooterContactBlock())],
        use_json_field=True,
        blank=True,
        verbose_name="Contatti",
    )

    social = StreamField(
        [("social", SocialLinkBlock())],
        use_json_field=True,
        blank=True,
        verbose_name="Seguici (social)",
        help_text="Mostrati nel footer sotto 'Seguici'. Spegni 'Visibile' per nasconderne uno.",
    )

    privacy_page = models.ForeignKey(
        "wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="Pagina Privacy policy",
        help_text="Linkata nel footer e accanto alla casella del consenso in ogni modulo.",
    )
    cookie_page = models.ForeignKey(
        "wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="Pagina Cookie policy", help_text="Linkata nel footer.",
    )

    # Information notice about cookies (not a consent banner: the site uses
    # only technical storage). Shown once; "OK" hides it in that browser.
    cookie_notice_enabled = models.BooleanField(
        default=True, verbose_name="Mostra l'avviso sui cookie",
        help_text="Barra informativa in basso alla prima visita, con il link alla Cookie policy e il pulsante OK.",
    )
    cookie_notice_it = models.TextField(
        max_length=300, blank=True, verbose_name="Testo dell'avviso (IT)",
        help_text="Vuoto = \"Questo sito usa solo cookie tecnici, necessari al suo funzionamento.\"",
    )
    cookie_notice_en = models.TextField(max_length=300, blank=True, verbose_name="Testo dell'avviso (EN)")
    cookie_notice_fr = models.TextField(max_length=300, blank=True, verbose_name="Testo dell'avviso (FR)")

    vat_label = models.CharField(max_length=60, blank=True, default="Partita IVA:")
    vat_value = models.CharField(max_length=60, blank=True)
    tax_label = models.CharField(max_length=60, blank=True, default="Codice Fiscale:")
    tax_value = models.CharField(max_length=60, blank=True)

    panels = [
        FieldPanel("contacts"),
        FieldPanel("social"),
        MultiFieldPanel([
            FieldPanel("vat_label"),
            FieldPanel("vat_value"),
            FieldPanel("tax_label"),
            FieldPanel("tax_value"),
        ], heading="Dati aziendali"),
        MultiFieldPanel([
            FieldPanel("privacy_page"),
            FieldPanel("cookie_page"),
        ], heading="Pagine legali"),
        MultiFieldPanel([
            FieldPanel("cookie_notice_enabled"),
            FieldPanel("cookie_notice_it"),
            FieldPanel("cookie_notice_en"),
            FieldPanel("cookie_notice_fr"),
        ], heading="Avviso sui cookie",
           help_text="Informativo: il sito usa solo cookie tecnici, quindi non serve chiedere il consenso. "
                     "Se in futuro si aggiungono statistiche o pubblicità, serve un vero banner di consenso."),
    ]

    class Meta:
        verbose_name = "Footer"


@register_setting(icon="help")
class ChatbotSettings(BaseSiteSetting):
    """Presentation of the chat widget. The answers themselves live in
    chatbot/engine.py - this only controls whether and how it appears."""

    enabled = models.BooleanField(default=True, verbose_name="Chatbot attivo")
    title = models.CharField(
        max_length=60, blank=True, default="Chiedi ad Axatel",
        verbose_name="Titolo finestra",
    )
    welcome_message = models.TextField(
        blank=True,
        default="Ciao! Posso rispondere a domande su Axatel, "
                "le nostre soluzioni IoT e i casi di successo.",
        verbose_name="Messaggio di benvenuto",
    )
    placeholder = models.CharField(
        max_length=100, blank=True, default="Scrivi una domanda...",
        verbose_name="Testo segnaposto",
    )

    suggestions = StreamField(
        [("suggestion", blocks.CharBlock(
            max_length=80,
            help_text="Domanda suggerita, es. 'Dove siete?'",
        ))],
        use_json_field=True,
        blank=True,
        verbose_name="Domande suggerite",
        help_text="Mostrate come pulsanti cliccabili all'apertura della chat.",
    )

    # Page suggestions: a small bubble above the chat button, after a while
    # on a page, proposing questions about that page (chatbot/hints.py).
    hints_enabled = models.BooleanField(
        default=True, verbose_name="Suggerimenti sulla pagina",
        help_text="Dopo qualche secondo su una pagina, una nuvoletta sopra il pulsante della chat propone "
                  "domande su quella pagina. Al massimo una volta per pagina; chi preme \"No grazie\" non la "
                  "rivede per tutta la visita.",
    )
    hint_delay = models.PositiveSmallIntegerField(
        default=20, verbose_name="Dopo quanti secondi",
        help_text="Tempo sulla pagina prima che compaia la nuvoletta (minimo 5).",
    )
    hint_text_it = models.CharField(
        max_length=160, blank=True, default="Vuoi saperne di più su {title}?",
        verbose_name="Testo della nuvoletta (IT)",
        help_text="{title} = il nome della pagina. Sulle pagine senza nome (homepage, elenchi) si usa un testo generico.",
    )
    hint_text_en = models.CharField(max_length=160, blank=True, default="Would you like to know more about {title}?",
                                    verbose_name="Testo della nuvoletta (EN)")
    hint_text_fr = models.CharField(max_length=160, blank=True, default="Vous voulez en savoir plus sur {title} ?",
                                    verbose_name="Testo della nuvoletta (FR)")
    hint_excluded = models.TextField(
        blank=True, default="/contatti\n/privacy-policy\n/cookie-policy",
        verbose_name="Pagine senza nuvoletta",
        help_text="Un indirizzo per riga (anche l'inizio di un indirizzo, es. /azienda). Vale in tutte le lingue.",
    )

    # Reply to "uff", "boh", "asdfgh" or one unknown word (chatbot/understanding.py).
    unclear_reply_it = models.TextField(
        blank=True,
        default="Non ho capito la domanda. Puoi scriverla con qualche parola in più? "
                "Per esempio: «Come monitorate le frane?»",
        verbose_name="Risposta a una domanda non chiara (IT)",
        help_text="Per messaggi senza senso o troppo vaghi (\"uff\", \"ok\", lettere a caso, una parola che il "
                  "chatbot non conosce). Vuoto = testo predefinito. Li trovi in Domande dei visitatori come "
                  "\"Domanda non chiara\".",
    )
    unclear_reply_en = models.TextField(
        blank=True,
        default="I didn't understand the question. Could you write it with a few more words? "
                "For example: \"How do you monitor landslides?\"",
        verbose_name="Risposta a una domanda non chiara (EN)",
    )
    unclear_reply_fr = models.TextField(
        blank=True,
        default="Je n'ai pas compris la question. Pouvez-vous l'écrire avec quelques mots de plus ? "
                "Par exemple : « Comment surveillez-vous les glissements de terrain ? »",
        verbose_name="Risposta a una domanda non chiara (FR)",
    )

    # How the chatbot talks (chatbot/engine.py respond()).
    page_text_answers = models.BooleanField(
        default=True, verbose_name="Risposte dal testo delle pagine",
        help_text="Oltre alla descrizione breve, il chatbot risponde con il paragrafo della pagina che "
                  "parla di ciò che è stato chiesto, e propone \"Dimmi di più\" per continuare.",
    )
    related_pages = models.BooleanField(
        default=True, verbose_name="Proponi pagine correlate",
        help_text="Sotto una risposta, fino a due pulsanti verso argomenti vicini (es. dopo \"frane\": "
                  "\"Monitoraggio fiumi\").",
    )
    contact_button = models.BooleanField(
        default=True, verbose_name="Pulsante \"Parla con un esperto\"",
        help_text="Quando il chatbot non sa rispondere, o si chiede di prezzi e preventivi, propone il "
                  "modulo di contatto.",
    )
    contact_path = models.CharField(
        max_length=200, blank=True, default="/contatti",
        verbose_name="Pagina del pulsante",
        help_text="Indirizzo in italiano, es. /contatti (vale anche per /en e /fr).",
    )

    panels = [
        FieldPanel("enabled"),
        FieldPanel("title"),
        FieldPanel("welcome_message"),
        FieldPanel("placeholder"),
        FieldPanel("suggestions"),
        MultiFieldPanel([
            FieldPanel("page_text_answers"),
            FieldPanel("related_pages"),
            FieldPanel("contact_button"),
            FieldPanel("contact_path"),
        ], heading="Conversazione",
           help_text="Le domande ricevute e una prova del chatbot: menu Chatbot a sinistra."),
        MultiFieldPanel([
            FieldPanel("hints_enabled"),
            FieldPanel("hint_delay"),
            FieldPanel("hint_text_it"),
            FieldPanel("hint_text_en"),
            FieldPanel("hint_text_fr"),
            FieldPanel("hint_excluded"),
        ], heading="Suggerimenti sulla pagina",
           help_text="Testi e domande su misura per una pagina: Chatbot → Suggerimenti."),
        MultiFieldPanel([
            FieldPanel("unclear_reply_it"),
            FieldPanel("unclear_reply_en"),
            FieldPanel("unclear_reply_fr"),
        ], heading="Domande non chiare",
           help_text="A un saluto (\"ciao\") il chatbot risponde con il messaggio di benvenuto; a un "
                     "ringraziamento con \"Prego!\"."),
    ]

    class Meta:
        verbose_name = "Chatbot"

# ── Team (Impostazioni → Team) ────────────────────────────────────────────
# The people shown on /azienda/team. One entry per person, in the order of
# the list (drag to reorder). "Visibile" hides a person without deleting
# them. While the list is empty, the site shows its built-in example team.


TEAM_LABEL_CHOICES = [
    ("department", "Reparto (solo sotto i responsabili)"),
    ("role", "Ruolo (sotto ogni persona)"),
    ("both", "Ruolo e reparto"),
    ("none", "Nessuna etichetta"),
]


@register_setting(icon="group")
class TeamSettings(ClusterableModel, BaseSiteSetting):
    label_mode = models.CharField(
        max_length=20,
        choices=TEAM_LABEL_CHOICES,
        default="department",
        verbose_name="Etichetta sotto il nome",
        help_text="Cosa evidenziare sotto ogni persona nell'organigramma.",
    )

    panels = [
        FieldPanel("label_mode"),
        InlinePanel(
            "members",
            heading="Persone del team",
            label="Persona",
            help_text="Ordine = ordine sulla pagina Team (trascina per spostare). "
                      "Ruolo e descrizione in inglese e francese sono facoltativi: "
                      "se vuoti, si usa il testo italiano.",
        ),
    ]

    class Meta:
        verbose_name = "Team"


class TeamMember(ClusterableModel, Orderable):
    setting = ParentalKey(TeamSettings, related_name="members", on_delete=models.CASCADE)
    name = models.CharField(max_length=120, verbose_name="Nome e cognome")
    role = models.CharField(max_length=120, blank=True, verbose_name="Ruolo")
    role_en = models.CharField(max_length=120, blank=True, verbose_name="Ruolo (EN)")
    role_fr = models.CharField(max_length=120, blank=True, verbose_name="Ruolo (FR)")
    bio = models.TextField(max_length=600, blank=True, verbose_name="Descrizione")
    bio_en = models.TextField(max_length=600, blank=True, verbose_name="Descrizione (EN)")
    bio_fr = models.TextField(max_length=600, blank=True, verbose_name="Descrizione (FR)")
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Foto",
        help_text="Meglio quadrata, almeno 400×400 px. Viene ritagliata al centro.",
    )
    visible = models.BooleanField(
        default=True,
        verbose_name="Visibile",
        help_text="Spegni per nascondere la persona dal sito senza cancellarla.",
    )
    # Organisation chart: who this person reports to, and the department
    # they lead (if any). The team page draws a line only between a person
    # and the one they report to, so departments read as separate branches.
    reports_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
        verbose_name="Riporta a",
        help_text="La persona a cui risponde (es. il responsabile del reparto, o il CEO). "
                  "Vuoto = in cima all'organigramma. Una persona appena aggiunta compare "
                  "in questo elenco dopo il primo salvataggio.",
    )
    # Extra managers (matrix reporting, e.g. a person working for two
    # departments). The person stays placed under "Riporta a"; the page
    # draws a lighter line to each of these.
    also_reports_to = ParentalManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="dotted_reports",
        verbose_name="Riporta anche a",
        help_text="Facoltativo: altri responsabili di questa persona. Sulla pagina compare "
                  "una linea più sottile verso ciascuno.",
    )
    department = models.CharField(
        max_length=80,
        blank=True,
        verbose_name="Guida il reparto",
        help_text="Solo per i responsabili: nome del reparto che guidano, es. 'Tecnico'. "
                  "Le persone che riportano a loro fanno parte di quel reparto.",
    )
    department_en = models.CharField(max_length=80, blank=True, verbose_name="Reparto (EN)")
    department_fr = models.CharField(max_length=80, blank=True, verbose_name="Reparto (FR)")

    panels = [
        FieldRowPanel([FieldPanel("name"), FieldPanel("visible")]),
        FieldPanel("photo"),
        FieldRowPanel([FieldPanel("role"), FieldPanel("role_en"), FieldPanel("role_fr")], heading="Ruolo"),
        FieldPanel("bio"),
        MultiFieldPanel([FieldPanel("bio_en"), FieldPanel("bio_fr")], heading="Descrizione EN / FR", classname="collapsed"),
        MultiFieldPanel([
            FieldPanel("reports_to"),
            FieldPanel("also_reports_to", widget=forms.CheckboxSelectMultiple),
            FieldRowPanel([FieldPanel("department"), FieldPanel("department_en"), FieldPanel("department_fr")]),
        ], heading="Organigramma"),
    ]

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        if self.pk and self.reports_to_id == self.pk:
            raise ValidationError({"reports_to": "Una persona non può riportare a se stessa."})

    class Meta(Orderable.Meta):
        ordering = ["sort_order"]

    def translated(self, field: str, language: str) -> str:
        if language != "it":
            value = (getattr(self, f"{field}_{language}", "") or "").strip()
            if value:
                return value
        return getattr(self, field, "") or ""

    def __str__(self):
        return self.name


@register_setting(icon="image")
class BrandingSettings(BaseSiteSetting):
    """Logo and pictures used across the whole site. Empty = the built-in
    files shipped with the site. SVG or PNG with a transparent background
    work best."""

    logo = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="Logo",
        help_text="Nel menu in alto e nell'animazione a particelle della home. SVG o PNG trasparente.",
    )
    particle_logo = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="Logo per l'animazione a particelle",
        help_text="Facoltativo: un'altra versione del logo solo per le particelle. Vuoto = il logo qui sopra.",
    )
    header_wing = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="Ala nelle intestazioni",
        help_text="Il disegno accanto al titolo in cima alle pagine e nella citazione della home. PNG trasparente.",
    )

    panels = [FieldPanel("logo"), FieldPanel("particle_logo"), FieldPanel("header_wing")]

    class Meta:
        verbose_name = "Logo e immagini del sito"


DEFAULT_CONFIRMATION = {
    "it": "Gentile {nome},\n\ngrazie per averci scritto: abbiamo ricevuto la tua richiesta e ti risponderemo il prima possibile, di solito entro due giorni lavorativi.\n\nIl team Axatel",
    "en": "Dear {nome},\n\nthank you for writing to us: we have received your request and will reply as soon as possible, usually within two working days.\n\nThe Axatel team",
    "fr": "Bonjour {nome},\n\nmerci de nous avoir écrit : nous avons bien reçu votre demande et vous répondrons au plus vite, en général sous deux jours ouvrés.\n\nL'équipe Axatel",
}


@register_setting(icon="mail")
class FormNotificationSettings(BaseSiteSetting):
    """Impostazioni → Notifiche moduli: who is e-mailed about each kind of
    request sent from the site's forms, and the confirmation the visitor gets.
    The requests are always saved in Richieste di contatto as well."""

    emails_contact = models.TextField(
        blank=True, verbose_name="Richieste di contatto",
        help_text="Un indirizzo e-mail per riga. Vuoto = gli indirizzi di ADMIN_EMAILS nel file .env del server.",
    )
    emails_quote = models.TextField(blank=True, verbose_name="Richieste di preventivo",
                                    help_text="Un indirizzo per riga. Vuoto = come Richieste di contatto.")
    emails_candidate = models.TextField(blank=True, verbose_name="Candidature (CV)",
                                        help_text="Un indirizzo per riga. Vuoto = come Richieste di contatto.")
    emails_partner = models.TextField(blank=True, verbose_name="Proposte di collaborazione",
                                      help_text="Un indirizzo per riga. Vuoto = come Richieste di contatto.")
    attach_files = models.BooleanField(
        default=True, verbose_name="Allega i documenti all'e-mail",
        help_text="Il CV o il documento inviato dal visitatore viene allegato alla notifica.",
    )
    send_confirmation = models.BooleanField(
        default=True, verbose_name="Invia una conferma al visitatore",
        help_text="Un'e-mail che conferma la ricezione, nella lingua del sito usata dal visitatore.",
    )
    confirmation_it = models.TextField(blank=True, default=DEFAULT_CONFIRMATION["it"], verbose_name="Testo della conferma (IT)",
                                       help_text="{nome} viene sostituito con il nome del visitatore.")
    confirmation_en = models.TextField(blank=True, default=DEFAULT_CONFIRMATION["en"], verbose_name="Testo della conferma (EN)")
    confirmation_fr = models.TextField(blank=True, default=DEFAULT_CONFIRMATION["fr"], verbose_name="Testo della conferma (FR)")

    panels = [
        MultiFieldPanel([
            FieldPanel("emails_contact"),
            FieldPanel("emails_quote"),
            FieldPanel("emails_candidate"),
            FieldPanel("emails_partner"),
            FieldPanel("attach_files"),
        ], heading="Chi riceve le richieste"),
        MultiFieldPanel([
            FieldPanel("send_confirmation"),
            FieldPanel("confirmation_it"),
            FieldPanel("confirmation_en"),
            FieldPanel("confirmation_fr"),
        ], heading="Conferma al visitatore"),
    ]

    class Meta:
        verbose_name = "Notifiche moduli"


@register_setting(icon="search")
class SearchEngineSettings(BaseSiteSetting):
    """Impostazioni → Motori di ricerca: the go-live switch for Google.
    While it is off, every page and robots.txt tell search engines to stay
    away (the site must not compete with the live axatel.it). The frontend
    never allows indexing on a bare IP address, whatever this says."""

    allow_indexing = models.BooleanField(
        default=False, verbose_name="Consenti ai motori di ricerca di indicizzare il sito",
        help_text="Accendilo solo quando il sito è online sul dominio definitivo (axatel.it) e i vecchi "
                  "indirizzi sono reindirizzati. Spento = 'noindex' su ogni pagina e robots.txt che blocca tutto. "
                  "Sull'indirizzo IP del server il sito non è mai indicizzato.",
    )

    panels = [FieldPanel("allow_indexing")]

    class Meta:
        verbose_name = "Motori di ricerca"
