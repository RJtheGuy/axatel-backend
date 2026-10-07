import re
from html import unescape

from django.db import models
from django.utils.text import Truncator
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index
from wagtailseo.models import SeoMixin

from core.api_blocks import ImageAPIField, TagListField


class CasiIndexPage(SeoMixin, Page):
    """
    Listing page. URL: /casi/
    The Nuxt frontend queries child pages directly via the API rather
    than relying on get_context(), which the API never calls.
    """

    api_fields = [
        APIField("intro"),
    ]

    intro = models.TextField(
        blank=True,
        verbose_name="Introduzione",
        help_text="Testo mostrato sopra l'elenco dei casi.",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = ["casi.CasoSuccessoPage"]

    content_panels = Page.content_panels + [FieldPanel("intro")]
    promote_panels = SeoMixin.promote_panels

    class Meta:
        verbose_name = "Indice Casi di successo"


class CasoSuccessoTag(TaggedItemBase):
    content_object = ParentalKey(
        "casi.CasoSuccessoPage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class CasoSuccessoPage(SeoMixin, Page):
    """
    A single case study. URL: /casi/<slug>/

    `body` is a plain RichTextField rather than BODY_BLOCKS on purpose:
    the existing content is straight h3/p/ul/strong prose, not
    component-composed layout. Using StreamField here would force
    editors to wrap every paragraph in a block for no gain.
    """

    api_fields = [
        APIField("client_label"),
        APIField("client"),
        APIField("category"),
        APIField("event_date"),
        APIField("description"),
        APIField("card_excerpt"),
        APIField("show_card_title"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("tags", serializer=TagListField()),
        APIField("body"),
    ]

    client_label = models.CharField(
        max_length=50,
        blank=True,
        default="Cliente",
        verbose_name="Etichetta cliente",
        help_text="Testo mostrato prima del cliente (es. 'Cliente', 'Committente'). "
                  "Lascia vuoto per mostrare solo il nome del cliente, senza etichetta.",
    )
    client = models.CharField(
        max_length=150, blank=True, verbose_name="Cliente",
        help_text="Es. 'Provincia di Belluno · ANAS'",
    )
    category = models.CharField(
        max_length=100, blank=True, verbose_name="Categoria",
        help_text="Es. 'Smart Road', 'Gallerie', 'Corporate'",
    )
    event_date = models.DateField(
        null=True, blank=True, verbose_name="Data del progetto",
        help_text="Quando si è svolto il progetto o l'evento (basta anche il 1° del mese). "
                  "Nell'elenco e in homepage i casi più recenti compaiono per primi; "
                  "quelli senza data vengono dopo, nell'ordine di pubblicazione.",
    )
    description = models.TextField(
        max_length=300, blank=True,
        verbose_name="Descrizione (card)",
        help_text="Testo mostrato nella card del carosello. "
                  "Se vuoto, viene generato automaticamente un estratto del contenuto. "
                  "Usato anche come meta description se il tab Promuovi è vuoto.",
    )
    show_card_title = models.BooleanField(
        default=False,
        verbose_name="Mostra titolo nella card",
        help_text="Attiva se l'immagine di copertina non contiene già il titolo.",
    )
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Immagine di copertina",
    )
    body = RichTextField(
        blank=True,
        features=["bold", "italic", "link", "ol", "ul", "h3", "h4", "highlight"],
        verbose_name="Contenuto",
    )
    tags = ClusterTaggableManager(through=CasoSuccessoTag, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField("description"),
        index.SearchField("body"),
        index.FilterField("category"),
    ]

    parent_page_types = ["casi.CasiIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel("client_label", classname="col3"),
                FieldPanel("client", classname="col9"),
            ]),
            FieldPanel("category"),
            FieldPanel("event_date"),
            FieldPanel("cover_image"),
            FieldPanel("description"),
            FieldPanel("show_card_title"),
        ], heading="📋 Meta caso"),
        FieldPanel("body"),
        FieldPanel("tags"),
    ]
    promote_panels = SeoMixin.promote_panels

    @property
    def card_excerpt(self):
        """
        Text for the card: the manual description if present, otherwise
        an automatic excerpt of the body (~22 words, ending with an ellipsis).
        """
        if self.description:
            return self.description
        text = re.sub(r"<[^>]+>", " ", self.body or "")  # tags -> space, so headings don't glue to paragraphs
        text = re.sub(r"\s+", " ", unescape(text)).strip()
        return Truncator(text).words(22, truncate="…")

    def get_meta_description(self):
        return self.search_description or self.description

    class Meta:
        verbose_name = "Caso di successo"
        verbose_name_plural = "Casi di successo"
