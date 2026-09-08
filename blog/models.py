from django.db import models
from django.utils import timezone
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtailseo.models import SeoMixin

from core.api_blocks import ImageAPIField, TagListField
from core.blocks import BODY_BLOCKS


class BlogIndexPage(SeoMixin, Page):
    """
    Blog listing page. URL: /blog/
    """

    api_fields = [
        APIField("intro"),
    ]

    intro = StreamField(
        BODY_BLOCKS, use_json_field=True, blank=True,
        verbose_name="Introduzione blog",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BlogPost"]
    content_panels = Page.content_panels + [FieldPanel("intro")]
    promote_panels = SeoMixin.promote_panels

    class Meta:
        verbose_name = "Indice Blog"


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
        verbose_name = "Articolo Blog"
        verbose_name_plural = "Articoli Blog"