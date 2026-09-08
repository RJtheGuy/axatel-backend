from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtailseo.models import SeoMixin

from core.api_blocks import ImageAPIField
from core.blocks import BODY_BLOCKS


class HomePage(SeoMixin, Page):

    api_fields = [
        APIField("hero_tagline"),
        APIField("hero_description"),
        APIField("hero_cta_label"),
        APIField("hero_cta_url"),
        APIField("hero_frasi"),
        APIField("hero_quote_text"),
        APIField("hero_cases_logo", serializer=ImageAPIField()),
        APIField("body"),
    ]

    
    hero_tagline = models.CharField(
        max_length=120, default="Connettività e telefonia per il tuo business",
        verbose_name="Tagline hero",
    )
    hero_description = models.TextField(
        blank=True, default="Soluzioni su misura per PMI e grandi aziende.",
        verbose_name="Descrizione hero",
    )
    hero_cta_label = models.CharField(
        max_length=40, default="Scopri i servizi",
        verbose_name="Testo pulsante hero",
    )
    hero_cta_url = models.CharField(
        max_length=200, default="/servizi/",
        verbose_name="URL pulsante hero",
    )

    
    hero_frasi = StreamField(
        [("frase", blocks.CharBlock(
            max_length=200,
            help_text="Una frase della rotazione. Usa \\n per forzare un a capo.",
        ))],
        use_json_field=True,
        blank=True,
        verbose_name="Frasi rotanti hero",
    )
    hero_quote_text = models.TextField(
        blank=True,
        verbose_name="Citazione hero",
        help_text="Citazione mostrata nell'hero. Le righe vuote separano "
                  "il testo dalla firma (nome e ruolo).",
    )
    hero_cases_logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Logo hero",
    )

    body = StreamField(
        BODY_BLOCKS,
        use_json_field=True,
        blank=True,
        verbose_name="Contenuto pagina (blocchi)",
    )

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "services.ServicesIndexPage",
        "blog.BlogIndexPage",
        "home.FlexPage",
        "casi.CasiIndexPage",
        "monitoring.MonitoringIndexPage",
        "solutions.SolutionsIndexPage",
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("hero_frasi"),
            FieldPanel("hero_quote_text"),
            FieldPanel("hero_cases_logo"),
        ], heading="🦸 Hero — sezione in cima alla home"),
        MultiFieldPanel([
            FieldPanel("hero_tagline"),
            FieldPanel("hero_description"),
            FieldPanel("hero_cta_label"),
            FieldPanel("hero_cta_url"),
        ], heading="🦸 Hero — campi legacy (non usati dalla home attuale)"),
        FieldPanel("body"),
    ]

    promote_panels = SeoMixin.promote_panels

    class Meta:
        verbose_name = "Home Page"


FLEX_PAGE_TEMPLATES = {
    "conosci-axatel":           "home/conosci_axatel_page.html",
    "iot":                      "home/iot_page.html",
    "supervisione-e-controllo":  "home/supervisione_page.html",
    "ingegneria":               "home/ingegneria_page.html",
    "sviluppo-elettronico":     "home/sviluppo_page.html",
    "diventa-partner":          "home/partner_page.html",
    "casi-di-successo":         "home/casi_page.html",
    "contatti":                 "home/contatti_page.html",
}


class FlexPage(SeoMixin, Page):
    """
    Generic flexible page, fully block-driven.
    Routed in Nuxt via pages/[...slug].vue, which resolves the path
    through the API rather than a Django template.
    """

    api_fields = [
        APIField("body"),
    ]

    body = StreamField(
        BODY_BLOCKS,
        use_json_field=True,
        blank=True,
        verbose_name="Contenuto (blocchi)",
    )

    parent_page_types = ["home.HomePage", "home.FlexPage"]
    subpage_types = ["home.FlexPage"]

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]
    promote_panels = SeoMixin.promote_panels

    class Meta:
        verbose_name = "Pagina generica"