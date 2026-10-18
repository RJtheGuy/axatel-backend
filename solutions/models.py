from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField

from core.api_blocks import ImageAPIField, TagListField
from core.base_pages import CardSectionIndexPage, CardDetailPage
from core.blocks import BODY_BLOCKS
from core.page_meta import category_field, cover_position_field, image_frame_field, show_card_title_field

GROUP_CHOICES = [
    ("Piattaforme", "Piattaforme"),
    ("Sensori", "Sensori"),
    ("Tecnologie", "Tecnologie"),
    ("Servizi", "Servizi"),
]


class SolutionsIndexPage(CardSectionIndexPage):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["solutions.SolutionPage"]

    class Meta:
        verbose_name = "Indice Soluzioni"


class SolutionPage(CardDetailPage):
    """One page under "Come lo realizziamo?". URL: /soluzioni/<slug>/

    Body built from blocks; the structured ones (Sezione di testo, Cosa
    misuriamo, Come funziona, Schede dispositivi, Casi collegati) give the
    Move Solutions-style layout. Pages that don't exist here yet are still
    shown by the site from its built-in content.
    """

    api_fields = CardDetailPage.api_fields + [
        APIField("group"),
        APIField("eyebrow"),
        APIField("category"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("cover_position"),
        APIField("image_frame"),
        APIField("show_card_title"),
        APIField("body_after"),
        APIField("tags", serializer=TagListField()),
    ]

    group = models.CharField(max_length=40, choices=GROUP_CHOICES, blank=True, verbose_name="Gruppo",
                             help_text="Colonna del menu 'Come lo realizziamo?' a cui appartiene.")
    eyebrow = models.CharField(max_length=80, blank=True, verbose_name="Sottotitolo breve",
                               help_text="Es. 'Supervisione e controllo'")
    category = category_field()
    cover_image = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+", verbose_name="Immagine di copertina")
    cover_position = cover_position_field()
    # On by default here: the Soluzioni pictures have always been in the white box.
    image_frame = image_frame_field(default=True)
    show_card_title = show_card_title_field()
    # Blocks shown after "Come lavoriamo" and "Altre soluzioni", before the closing
    # "Hai un progetto da monitorare?" box: text, pictures, cards… as in Contenuto.
    body_after = StreamField(
        BODY_BLOCKS, use_json_field=True, blank=True,
        verbose_name="Contenuto in fondo (dopo 'Altre soluzioni')",
        help_text="Facoltativo. Blocchi mostrati dopo 'Come lavoriamo' e 'Altre soluzioni', "
                  "prima del riquadro finale 'Hai un progetto da monitorare?'.",
    )
    tags = ClusterTaggableManager(through="solutions.SolutionPageTag", blank=True)

    # Same "📋 Meta" panel as Monitoraggio, Servizi and the informative pages
    # (core/page_meta.py), tags after the content like on the success stories.
    content_panels = CardDetailPage.content_panels[:1] + [
        MultiFieldPanel([
            FieldPanel("group"),
            FieldPanel("eyebrow"),
            FieldPanel("category"),
            FieldPanel("cover_image"),
            FieldPanel("cover_position"),
            FieldPanel("image_frame"),
            FieldPanel("short_description"),
            FieldPanel("show_card_title"),
            FieldPanel("icon"),
        ], heading="📋 Meta"),
        FieldPanel("body"),
        FieldPanel("body_after"),
        FieldPanel("tags"),
    ]

    parent_page_types = ["solutions.SolutionsIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Soluzione"
        verbose_name_plural = "Soluzioni"


class SolutionPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "solutions.SolutionPage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )
