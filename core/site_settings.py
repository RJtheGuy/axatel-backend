"""
Site-wide content that is not page content: navbar links, the header
CTA, footer contacts, company registration details.

These live in wagtail.contrib.settings rather than on a page because
they appear on EVERY page.
Editors find these under Impostazioni in the Wagtail admin sidebar.
"""

from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField


class NavLinkBlock(blocks.StructBlock):

    label = blocks.CharBlock(max_length=40, help_text="Testo del link, es. 'Applicativi'")
    url = blocks.CharBlock(
        max_length=200,
        help_text="Percorso o ancora, es. '/casi' oppure '/#applicativi'",
    )
    open_in_new_tab = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "link"
        label = "Link di navigazione"


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


@register_setting(icon="list-ul")
class NavigationSettings(BaseSiteSetting):
    """Navbar links + the header CTA button."""

    links = StreamField(
        [("link", NavLinkBlock())],
        use_json_field=True,
        blank=True,
        verbose_name="Link del menu",
        help_text="Ordine e contenuto del menu principale.",
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
        FieldPanel("links"),
        MultiFieldPanel([
            FieldPanel("cta_visible"),
            FieldPanel("cta_label"),
            FieldPanel("cta_url"),
        ], heading="Pulsante header"),
    ]

    class Meta:
        verbose_name = "Navigazione"


@register_setting(icon="site")
class FooterSettings(BaseSiteSetting):
    """Footer contacts and company registration details.

    Previously hardcoded in pages/index.vue, which meant they were
    duplicated into every page that rendered a footer and could only be
    changed by a developer.
    """

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

    # Quick-reply chips shown under the welcome message.
    #
    # These should be phrased the way a visitor would actually ask, not
    # as menu labels: the answer is chosen by semantic similarity
    # against KNOWLEDGE_BASE in chatbot/engine.py, so "Dove siete?"
    # matches far better than "Sede". A chip that scores below
    # ChatbotEngine.THRESHOLD falls through to the generic fallback
    # answer, which looks broken - test each one after adding it.
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