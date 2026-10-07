
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.models import Page
from core.api_blocks import ImageAPIField, TagListField
from core.base_pages import CardSectionIndexPage, CardDetailPage
from core.page_meta import cover_position_field, show_card_title_field
 
 
class MonitoringIndexPage(CardSectionIndexPage):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["monitoring.MonitoringPage"]
 
    class Meta:
        verbose_name = "Indice Monitoraggio"
 
 
class MonitoringPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "monitoring.MonitoringPage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class MonitoringPage(CardDetailPage):
    api_fields = [
        APIField("category"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("tags", serializer=TagListField()),
        APIField("icon"),
        APIField("short_description"),
        APIField("image_frame"),
        APIField("cover_position"),
        APIField("show_card_title"),
        APIField("body"),
    ]

    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Categoria",
        help_text="Es. Ambiente, Viabilita o Strutture.",
    )
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Immagine di copertina",
    )
    image_frame = models.BooleanField(
        default=False,
        verbose_name="Riquadro bianco attorno all'immagine",
        help_text="Spento: l'immagine appoggia direttamente sullo sfondo (il bianco del disegno sparisce). "
                  "Acceso: l'immagine sta in un riquadro bianco con ombra.",
    )
    cover_position = cover_position_field()
    show_card_title = show_card_title_field()
    tags = ClusterTaggableManager(through=MonitoringPageTag, blank=True)

    # Same "📋 Meta" panel as Soluzioni, Servizi and the informative pages
    # (core/page_meta.py), tags after the content like on the success stories.
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("category"),
            FieldPanel("cover_image"),
            FieldPanel("cover_position"),
            FieldPanel("image_frame"),
            FieldPanel("short_description"),
            FieldPanel("show_card_title"),
            FieldPanel("icon"),
        ], heading="📋 Meta"),
        FieldPanel("body"),
        FieldPanel("tags"),
    ]

    parent_page_types = ["monitoring.MonitoringIndexPage"]
    subpage_types = []
 
    class Meta:
        verbose_name = "Argomento monitoraggio"
        verbose_name_plural = "Argomenti monitoraggio"