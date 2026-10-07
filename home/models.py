from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from rest_framework.fields import Field
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page
from wagtailseo.models import SeoMixin

from core.api_blocks import ImageAPIField, TagListField
from core.blocks import BODY_BLOCKS
from core.blocks_solutions import _image
from core.page_meta import category_field, cover_position_field


class TrustLogoBlock(blocks.StructBlock):
    """A client, partner or certification shown in the homepage trust strip."""
    name = blocks.CharBlock(max_length=120, label="Nome", help_text="Mostrato come testo se manca il logo; usato anche come testo alternativo.")
    logo = ImageChooserBlock(required=False, label="Logo")
    url = blocks.URLBlock(required=False, label="Link (facoltativo)")

    class Meta:
        icon = "image"
        label = "Logo"

    def get_api_representation(self, value, context=None):
        return {"name": value.get("name", ""), "logo": _image(value.get("logo")), "url": value.get("url") or ""}


class HomePage(SeoMixin, Page):

    api_fields = [
        APIField("hero_tagline"),
        APIField("hero_description"),
        APIField("hero_cta_label"),
        APIField("hero_cta_url"),
        APIField("hero_frasi"),
        APIField("hero_quote_text"),
        APIField("hero_cases_logo", serializer=ImageAPIField()),
        APIField("top_kicker"),
        APIField("top_title_before"),
        APIField("top_title_accent"),
        APIField("top_title_after"),
        APIField("top_intro"),
        APIField("top_cta_primary_label"),
        APIField("top_cta_primary_url"),
        APIField("top_cta_secondary_label"),
        APIField("top_cta_secondary_url"),
        APIField("top_show_status"),
        APIField("is_alias"),
        APIField("body"),
        APIField("trust_clients"),
        APIField("trust_certifications"),
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

    
    # First screen of the home ("Sistemi di monitoraggio real-time per la
    # riduzione del rischio"). Empty = the built-in text in that language.
    top_kicker = models.CharField(max_length=80, blank=True, verbose_name="Occhiello",
                                  help_text="Riga piccola sopra il titolo. Vuoto = 'Tecnologia che protegge'.")
    top_title_before = models.CharField(max_length=120, blank=True, verbose_name="Titolo — prima parte",
                                        help_text="Vuoto = 'Sistemi di monitoraggio'.")
    top_title_accent = models.CharField(max_length=60, blank=True, verbose_name="Titolo — parte colorata",
                                        help_text="Mostrata in azzurro. Vuoto = 'real-time'.")
    top_title_after = models.CharField(max_length=120, blank=True, verbose_name="Titolo — ultima parte",
                                       help_text="Vuoto = 'per la riduzione del rischio'.")
    top_intro = models.TextField(max_length=400, blank=True, verbose_name="Testo sotto il titolo")
    top_cta_primary_label = models.CharField(max_length=40, blank=True, verbose_name="Pulsante rosso — testo",
                                             help_text="Vuoto = 'Parla con un esperto'.")
    top_cta_primary_url = models.CharField(max_length=200, blank=True, verbose_name="Pulsante rosso — link",
                                           help_text="Vuoto = /contatti")
    top_cta_secondary_label = models.CharField(max_length=40, blank=True, verbose_name="Secondo pulsante — testo",
                                               help_text="Vuoto = 'Cosa monitoriamo'. Scrivi un trattino (-) per nasconderlo.")
    top_cta_secondary_url = models.CharField(max_length=200, blank=True, verbose_name="Secondo pulsante — link",
                                             help_text="Vuoto = /monitoraggio")
    top_show_status = models.BooleanField(default=True, verbose_name="Mostra 'Monitoraggio attivo 24/7'")

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

    # Trust strip above the footer. Hidden on the site while both are empty.
    trust_clients = StreamField(
        [("logo", TrustLogoBlock())],
        use_json_field=True,
        blank=True,
        verbose_name="Clienti e partner",
        help_text="Loghi di clienti o partner (solo con il loro consenso).",
    )
    trust_certifications = StreamField(
        [("logo", TrustLogoBlock())],
        use_json_field=True,
        blank=True,
        verbose_name="Certificazioni e riconoscimenti",
        help_text="Es. ISO 9001, LoRa Alliance. Solo certificazioni effettivamente ottenute.",
    )

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "services.ServicesIndexPage",
        "blog.BlogIndexPage",
        "home.FlexPage",
        "casi.CasiIndexPage",
        "monitoring.MonitoringIndexPage",
        "solutions.SolutionsIndexPage",
        "products.ProductIndexPage",
        "home.InfoIndexPage",
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("top_kicker"),
            FieldPanel("top_title_before"),
            FieldPanel("top_title_accent"),
            FieldPanel("top_title_after"),
            FieldPanel("top_intro"),
            FieldPanel("top_cta_primary_label"),
            FieldPanel("top_cta_primary_url"),
            FieldPanel("top_cta_secondary_label"),
            FieldPanel("top_cta_secondary_url"),
            FieldPanel("top_show_status"),
        ], heading="🏁 Prima schermata — titolo e pulsanti (vuoto = testo predefinito)"),
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
        MultiFieldPanel([
            FieldPanel("trust_clients"),
            FieldPanel("trust_certifications"),
        ], heading="🤝 Fiducia — loghi sopra il footer (nascosta se vuota)"),
        FieldPanel("body"),
    ]

    promote_panels = SeoMixin.promote_panels

    @property
    def is_alias(self) -> bool:
        """True for an English/French Home that only mirrors the Italian one
        (a Wagtail alias, not a translation): the site then keeps its own
        translated texts instead of showing the Italian ones."""
        return self.alias_of_id is not None

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


# ── Information pages: Azienda and Approfondimenti ─────────────────────────
# /azienda/chi-siamo, /azienda/bilancio-sostenibilita, /approfondimenti/faq …
# A "Sezione" (InfoIndexPage, slug "azienda" or "approfondimenti") holds
# "Pagina informativa" pages and the "Glossario". The URL is the path in the
# tree, so a page with slug "chi-siamo" under "azienda" is /azienda/chi-siamo.
# While a page doesn't exist here, the site shows its built-in version
# (axatel-frontend/app/data/contentPages.ts), so nothing disappears.


class InfoIndexPage(SeoMixin, Page):
    api_fields = [APIField("intro")]

    intro = models.TextField(blank=True, verbose_name="Introduzione")

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.InfoPage", "home.GlossaryPage"]

    content_panels = Page.content_panels + [FieldPanel("intro")]
    promote_panels = SeoMixin.promote_panels

    class Meta:
        verbose_name = "Sezione informativa"
        verbose_name_plural = "Sezioni informative"


class InfoPage(SeoMixin, Page):
    """A company or insight page: header (eyebrow, introduction, picture)
    and a body built from blocks."""

    api_fields = [
        APIField("category"),
        APIField("eyebrow"),
        APIField("introduction"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("cover_position"),
        APIField("tags", serializer=TagListField()),
        APIField("body"),
    ]

    eyebrow = models.CharField(
        max_length=80, blank=True, verbose_name="Occhiello",
        help_text="Parola chiave sopra l'introduzione, es. 'Tecnologia e infrastrutture'.",
    )
    introduction = models.TextField(
        max_length=400, blank=True, verbose_name="Introduzione",
        help_text="Una o due frasi in apertura. Usata anche come descrizione per Google se quella SEO è vuota.",
    )
    cover_image = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", verbose_name="Immagine di copertina",
    )
    category = category_field()
    cover_position = cover_position_field()
    body = StreamField(BODY_BLOCKS, use_json_field=True, blank=True, verbose_name="Contenuto")
    tags = ClusterTaggableManager(through="home.InfoPageTag", blank=True)

    parent_page_types = ["home.InfoIndexPage"]
    subpage_types = []

    # Same "📋 Meta" panel as Monitoraggio, Soluzioni and Servizi
    # (core/page_meta.py). These pages have no cards with a picture, so no
    # "Descrizione (card)" / "Mostra titolo nella card": the introduction
    # plays that part.
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("category"),
            FieldPanel("eyebrow"),
            FieldPanel("introduction"),
            FieldPanel("cover_image"),
            FieldPanel("cover_position"),
        ], heading="📋 Meta"),
        FieldPanel("body"),
        FieldPanel("tags"),
    ]
    promote_panels = SeoMixin.promote_panels

    def get_meta_description(self):
        return self.search_description or self.introduction

    class Meta:
        verbose_name = "Pagina informativa"
        verbose_name_plural = "Pagine informative"


class InfoPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "home.InfoPage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class GlossaryTermsField(Field):
    def to_representation(self, value):
        return [
            {
                "term": item.term,
                "definition": item.definition,
                "aliases": [a.strip() for a in (item.aliases or "").split(",") if a.strip()],
            }
            for item in value.all().order_by("sort_order")
        ]


class GlossaryPage(SeoMixin, Page):
    """/approfondimenti/glossario: a searchable list of terms. Translating
    the page ("Traduci") copies the terms, ready to be translated."""

    api_fields = [
        APIField("eyebrow"),
        APIField("introduction"),
        APIField("terms", serializer=GlossaryTermsField()),
    ]

    eyebrow = models.CharField(max_length=80, blank=True, verbose_name="Occhiello")
    introduction = models.TextField(max_length=400, blank=True, verbose_name="Introduzione")

    parent_page_types = ["home.InfoIndexPage"]
    subpage_types = []
    max_count_per_parent = 1

    content_panels = Page.content_panels + [
        FieldPanel("eyebrow"),
        FieldPanel("introduction"),
        InlinePanel("terms", heading="Termini", label="Termine",
                    help_text="L'ordine non conta: il sito li mostra in ordine alfabetico."),
    ]
    promote_panels = SeoMixin.promote_panels

    def get_meta_description(self):
        return self.search_description or self.introduction

    class Meta:
        verbose_name = "Glossario"


class GlossaryTerm(Orderable):
    page = ParentalKey(GlossaryPage, related_name="terms", on_delete=models.CASCADE)
    term = models.CharField(max_length=120, verbose_name="Termine")
    definition = models.TextField(max_length=800, verbose_name="Definizione")
    aliases = models.CharField(
        max_length=240, blank=True, verbose_name="Altri nomi",
        help_text="Separati da virgola; servono alla ricerca. Es. 'Application Programming Interface'.",
    )

    panels = [FieldPanel("term"), FieldPanel("definition"), FieldPanel("aliases")]

    def __str__(self):
        return self.term
