from django.db import models
from django.utils import timezone
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Locale, Page
from wagtail.search import index
from wagtailseo.models import SeoMixin

from core.api_blocks import ImageAPIField, TagListField
from core.blocks import BODY_BLOCKS


CARDS_PER_ROW = [
    ("auto", "Automatico (quante ne stanno)"),
    ("2", "2 per riga"),
    ("3", "3 per riga"),
    ("4", "4 per riga"),
]
TONES = [
    ("light", "Chiaro (sfondo bianco)"),
    ("dark", "Scuro (sfondo blu notte)"),
]
CARD_TAGS = [
    ("all", "Tutti i tag"),
    ("3", "Al massimo 3 tag"),
    ("none", "Nessun tag"),
]


class BlogIndexPage(SeoMixin, Page):
    """
    Blog listing page. URL: /blog/

    How the cards look (update 61): cards per row and the tags on the cards;
    light or dark background for the list and for the articles (update 62).
    Set on the Italian page and used for every language.
    """

    api_fields = [
        APIField("intro"),
        APIField("empty_title"),
        APIField("empty_text"),
        APIField("display"),
    ]

    intro = StreamField(
        BODY_BLOCKS, use_json_field=True, blank=True,
        verbose_name="Introduzione blog",
    )
    # Shown on /news while no article is published yet.
    empty_title = models.CharField(
        max_length=120, blank=True, verbose_name="Titolo",
        help_text="Vuoto = \"Le news arriveranno presto\" (tradotto in EN/FR).",
    )
    empty_text = models.TextField(
        max_length=400, blank=True, verbose_name="Testo",
        help_text="Vuoto = testo predefinito. Sotto compaiono i pulsanti verso i casi di successo e i contatti.",
    )

    cards_per_row = models.CharField(
        max_length=4, choices=CARDS_PER_ROW, default="auto", verbose_name="News per riga",
        help_text="Su schermi grandi. Su tablet sono al massimo 2, sul telefono 1.",
    )
    card_tags = models.CharField(
        max_length=4, choices=CARD_TAGS, default="all", verbose_name="Tag sulle card",
        help_text="I tag restano comunque visibili dentro ogni news.",
    )

    tone_index = models.CharField(
        max_length=8, choices=TONES, default="light", verbose_name="Sfondo dell'elenco News",
    )
    tone_articles = models.CharField(
        max_length=8, choices=TONES, default="light", verbose_name="Sfondo delle singole news",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BlogPost"]
    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel([
            FieldPanel("cards_per_row"),
            FieldPanel("card_tags"),
            FieldPanel("tone_index"),
            FieldPanel("tone_articles"),
        ], heading="Disposizione e colori",
           help_text="Vale per tutte le lingue: si cambia sulla pagina italiana."),
        MultiFieldPanel([
            FieldPanel("empty_title"),
            FieldPanel("empty_text"),
        ], heading="Quando non ci sono news",
           help_text="Il riquadro \"Prossimamente\" mostrato su /news finché non c'è nessun articolo pubblicato."),
    ]
    promote_panels = SeoMixin.promote_panels

    @property
    def display(self):
        """Card settings, always those of the Italian page."""
        source = self
        default = Locale.get_default()
        if self.locale_id != default.id:
            source = self.get_translation_or_none(default) or self
        return {"cards_per_row": source.cards_per_row or "auto", "card_tags": source.card_tags or "all",
                "tone_index": source.tone_index or "light", "tone_articles": source.tone_articles or "light"}

    class Meta:
        verbose_name = "Indice News"


class BlogPostTag(TaggedItemBase):
    content_object = ParentalKey(
        "blog.BlogPost",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class BlogPost(SeoMixin, Page):
    """
    A single blog/news article. URL: /blog/<slug>/
    Fully StreamField body — same block palette as all other pages.
    """

    api_fields = [
        APIField("author"),
        APIField("date"),
        APIField("intro"),
        APIField("body"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("tags", serializer=TagListField()),
    ]

    author = models.CharField(
        max_length=100, blank=True, default="Axatel Team",
        verbose_name="Autore",
    )
    date = models.DateField(default=timezone.now, verbose_name="Data pubblicazione")
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Immagine di copertina",
    )
    intro = models.TextField(
        max_length=400, blank=True,
        help_text="Estratto mostrato nelle card e usato come meta description.",
        verbose_name="Estratto",
    )
    body = StreamField(
        BODY_BLOCKS, use_json_field=True, blank=True,
        verbose_name="Corpo articolo",
    )
    tags = ClusterTaggableManager(through=BlogPostTag, blank=True)

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.FilterField("date"),
    ]

    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("author"),
            FieldPanel("date"),
            FieldPanel("cover_image"),
            FieldPanel("intro"),
        ], heading="📰 Meta articolo"),
        FieldPanel("body"),
        FieldPanel("tags"),
    ]
    promote_panels = SeoMixin.promote_panels

    def get_meta_description(self):
        return self.search_description or self.intro

    class Meta:
        verbose_name = "Articolo News"
        verbose_name_plural = "Articoli Blog"