from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField
from core.api_blocks import PageChooserBlock


class NavSubLinkBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=60, help_text="Testo del link, es. 'Sensori'")
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
            "label": value.get("label", ""),
            "href": page_repr["url"] if page_repr else value.get("custom_url", ""),
            "open_in_new_tab": bool(value.get("open_in_new_tab")),
        }


class NavGroupBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=60, help_text="Titolo colonna, es. 'Piattaforme'")
    links = blocks.ListBlock(NavSubLinkBlock())

    class Meta:
        icon = "list-ul"
        label = "Gruppo (colonna del menu a tendina)"

    def get_api_representation(self, value, context=None):
        links_block = self.child_blocks["links"]
        return {
            "label": value.get("label", ""),
            "links": links_block.get_api_representation(value.get("links", []), context=context),
        }


class NavItemBlock(blocks.StructBlock):
    """One entry in the top navbar. Leave `groups` empty for a plain
    direct link (e.g. 'Casi di successo'); fill it in for a dropdown
    (e.g. 'Come lo realizziamo?')."""
    label = blocks.CharBlock(max_length=60)
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
            "label": value.get("label", ""),
            "href": page_repr["url"] if page_repr else (value.get("custom_url") or None),
            "groups": groups_block.get_api_representation(value.get("groups", []), context=context),
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

    panels = [
        FieldPanel("items"),
        MultiFieldPanel([
            FieldPanel("cta_visible"),
            FieldPanel("cta_label"),
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