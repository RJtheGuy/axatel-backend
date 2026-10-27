"""
Product catalogue: one page per device or system, like Move Solutions'
sensor pages. URL: /prodotti/<slug>/

A ProductPage has a model name, a category, a short tagline (used on
cards), a picture, a table of specifications, an optional datasheet and a
normal block body for anything else.
"""
from django.conf import settings
from django.db import models
from rest_framework.fields import Field
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Locale, Page
from wagtail.search import index
from wagtailseo.models import SeoMixin

from core.api_blocks import ImageAPIField
from core.blocks import BODY_BLOCKS

CATEGORY_CHOICES = [
    ("sistemi", "Sistemi di monitoraggio"),
    ("sensori", "Sensori e stazioni"),
    ("piattaforme", "Piattaforme software"),
    ("comunicazione", "Gateway e comunicazione"),
]


class DocumentAPIField(Field):
    def to_representation(self, value):
        if not value:
            return None
        # Direct file URL under /media/, made absolute like images are.
        url = value.file.url
        base = getattr(settings, "WAGTAILADMIN_BASE_URL", "") or ""
        if url.startswith("/") and base:
            url = base.rstrip("/") + url
        return {"id": value.id, "title": value.title, "url": url}


class SpecBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=80, label="Caratteristica", help_text="Es. 'Connettività'")
    value = blocks.CharBlock(max_length=240, label="Valore", help_text="Es. 'LoRaWAN'")

    class Meta:
        icon = "list-ul"
        label = "Specifica"


LAYOUT_CHOICES = [
    ("categories", "Raggruppati per categoria (un titolo per gruppo)"),
    ("single", "Un'unica griglia, senza gruppi"),
]
COLUMN_CHOICES = [
    ("auto", "Automatico (quante ne stanno)"),
    ("2", "2 per riga"),
    ("3", "3 per riga"),
    ("4", "4 per riga"),
]
ORDER_HELP = (
    "<p><b>Ordine dei prodotti</b>: è quello dell'elenco in <i>Pagine → Prodotti</i>. "
    "Apri l'elenco, scegli <i>Gestisci l'ordine del menu</i> e trascina i prodotti. "
    "Con i gruppi per categoria, l'ordine vale dentro ogni gruppo.</p>"
    "<p>Queste impostazioni valgono per tutte le lingue: si cambiano sulla pagina italiana.</p>"
)


class ProductIndexPage(SeoMixin, Page):
    """Listing of all products. URL: /prodotti/

    How the cards are laid out (update 58): grouped by category or one grid,
    the order of the groups, cards per row. The order of the products is the
    page order in the CMS (Pagine → Prodotti → "Gestisci l'ordine del menu").
    """

    api_fields = [APIField("intro"), APIField("display")]

    intro = models.TextField(blank=True, verbose_name="Introduzione", help_text="Testo sopra l'elenco dei prodotti.")
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default="categories",
                              verbose_name="Disposizione")
    category_order = StreamField(
        [("category", blocks.ChoiceBlock(choices=CATEGORY_CHOICES, label="Categoria"))],
        use_json_field=True, blank=True, verbose_name="Ordine delle categorie",
        help_text="Aggiungi le categorie e trascinale nell'ordine voluto. Quelle non elencate vengono dopo. "
                  "Vuoto = ordine standard (Sistemi, Sensori, Piattaforme, Comunicazione).",
    )
    columns = models.CharField(max_length=4, choices=COLUMN_CHOICES, default="auto",
                               verbose_name="Prodotti per riga",
                               help_text="Su schermi grandi. Su tablet sono al massimo 2, sul telefono 1.")

    parent_page_types = ["home.HomePage"]
    subpage_types = ["products.ProductPage"]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel([
            HelpPanel(content=ORDER_HELP),
            FieldPanel("layout"),
            FieldPanel("category_order"),
            FieldPanel("columns"),
        ], heading="Disposizione delle card"),
    ]

    @property
    def display(self):
        """Layout settings, always those of the Italian page (all languages
        show the products the same way)."""
        source = self
        default = Locale.get_default()
        if self.locale_id != default.id:
            source = self.get_translation_or_none(default) or self
        order, seen = [], set()
        for block in source.category_order:
            if block.value and block.value not in seen:
                order.append(block.value)
                seen.add(block.value)
        return {"layout": source.layout or "categories", "columns": source.columns or "auto",
                "category_order": order}
    promote_panels = SeoMixin.promote_panels

    class Meta:
        verbose_name = "Indice Prodotti"


class ProductPage(SeoMixin, Page):
    api_fields = [
        APIField("model_code"),
        APIField("category"),
        APIField("tagline"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("specs"),
        APIField("datasheet", serializer=DocumentAPIField()),
        APIField("datasheet_url"),
        APIField("body"),
    ]

    model_code = models.CharField(max_length=80, blank=True, verbose_name="Modello / codice",
                                  help_text="Es. 'AXE-STD-LR-2'. Lascia vuoto se il nome basta.")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="sistemi", verbose_name="Categoria")
    tagline = models.TextField(max_length=300, blank=True, verbose_name="Descrizione breve (card)",
                               help_text="Mostrata nelle card e usata come meta description se il tab Promuovi è vuoto.")
    cover_image = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+", verbose_name="Immagine")
    specs = StreamField([("spec", SpecBlock())], use_json_field=True, blank=True, verbose_name="Specifiche tecniche")
    datasheet = models.ForeignKey("wagtaildocs.Document", null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+", verbose_name="Scheda tecnica (PDF)")
    datasheet_url = models.URLField(max_length=400, blank=True, verbose_name="Scheda tecnica (link esterno)",
                                    help_text="Usato solo se non è caricato un PDF qui sopra.")
    body = StreamField(BODY_BLOCKS, use_json_field=True, blank=True, verbose_name="Contenuto")

    search_fields = Page.search_fields + [
        index.SearchField("model_code"),
        index.SearchField("tagline"),
        index.FilterField("category"),
    ]

    parent_page_types = ["products.ProductIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("model_code"),
            FieldPanel("category"),
            FieldPanel("tagline"),
            FieldPanel("cover_image"),
        ], heading="Scheda prodotto"),
        FieldPanel("specs"),
        MultiFieldPanel([FieldPanel("datasheet"), FieldPanel("datasheet_url")], heading="Scheda tecnica"),
        FieldPanel("body"),
    ]
    promote_panels = SeoMixin.promote_panels

    def get_meta_description(self):
        return self.search_description or self.tagline

    class Meta:
        verbose_name = "Prodotto"
        verbose_name_plural = "Prodotti"
