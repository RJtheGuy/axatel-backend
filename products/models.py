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
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
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


class ProductIndexPage(SeoMixin, Page):
    """Listing of all products. URL: /prodotti/"""

    api_fields = [APIField("intro")]

    intro = models.TextField(blank=True, verbose_name="Introduzione", help_text="Testo sopra l'elenco dei prodotti.")

    parent_page_types = ["home.HomePage"]
    subpage_types = ["products.ProductPage"]

    content_panels = Page.content_panels + [FieldPanel("intro")]
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
