
"""
Why pages and not a StreamField block: each case is a full article with
its own slug route (/casi/<slug>), client, category, tag set and
multi-section HTML body. The existing `portfolio_grid` block in
core/blocks_sections.py is card-shaped (image/title/client/excerpt/url)
and would drop the routing, tags and per-case SEO entirely.

Structurally this mirrors blog.BlogIndexPage / blog.BlogPost - same
parent/child arrangement, same tagging approach - so anything already
built against the blog API shape works here with minimal changes.

STEP 3 of the theme rollout adds "highlight" to body's features list -
see core/wagtail_hooks.py for what that feature does. Purely additive:
existing case-study bodies that never used it are unaffected.
"""

from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
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
        APIField("client"),
        APIField("category"),
        APIField("description"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("tags", serializer=TagListField()),
        APIField("body"),
    ]

    client = models.CharField(
        max_length=150, blank=True, verbose_name="Cliente",
        help_text="Es. 'Provincia di Belluno · ANAS'",
    )
    category = models.CharField(
        max_length=100, blank=True, verbose_name="Categoria",
        help_text="Es. 'Smart Road', 'Gallerie', 'Corporate'",
    )
    description = models.TextField(
        max_length=300, blank=True,
        verbose_name="Descrizione (card)",
        help_text="Testo mostrato nella card del carosello. "
                  "Usato anche come meta description se il tab Promuovi è vuoto.",
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
            FieldPanel("client"),
            FieldPanel("category"),
            FieldPanel("cover_image"),
            FieldPanel("description"),
        ], heading="📋 Meta caso"),
        FieldPanel("body"),
        FieldPanel("tags"),
    ]
    promote_panels = SeoMixin.promote_panels

    def get_meta_description(self):
        return self.search_description or self.description

    class Meta:
        verbose_name = "Caso di successo"
        verbose_name_plural = "Casi di successo"