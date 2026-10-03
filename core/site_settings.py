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


@register_setting(icon="site")
class FooterSettings(BaseSiteSetting):
    """Footer contacts and company registration details."""

    contacts = StreamField(
        [("contact", FooterContactBlock())],
        use_json_field=True,
        blank=True,
        verbose_name="Contatti",
    )

    vat_label = models.CharField(max_length=60, blank=True, default="Partita IVA:")
    vat_value = models.CharField(max_length=60, blank=True)
    tax_label = models.CharField(max_length=60, blank=True, default="Codice Fiscale:")
    tax_value = models.CharField(max_length=60, blank=True)

    panels = [
        FieldPanel("contacts"),
        MultiFieldPanel([
            FieldPanel("vat_label"),
            FieldPanel("vat_value"),
            FieldPanel("tax_label"),
            FieldPanel("tax_value"),
        ], heading="Dati aziendali"),
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

    panels = [
        FieldPanel("enabled"),
        FieldPanel("title"),
        FieldPanel("welcome_message"),
        FieldPanel("placeholder"),
        FieldPanel("suggestions"),
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
