
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from core.api_blocks import ImageAPIField, TagListField
from core.base_pages import CardSectionIndexPage, CardDetailPage
 
 
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
    tags = ClusterTaggableManager(through=MonitoringPageTag, blank=True)

    content_panels = CardDetailPage.content_panels + [
        MultiFieldPanel([
            FieldPanel("category"),
            FieldPanel("cover_image"),
            FieldPanel("tags"),
        ], heading="Meta monitoraggio"),
    ]

    parent_page_types = ["monitoring.MonitoringIndexPage"]
    subpage_types = []
 
    class Meta:
        verbose_name = "Argomento monitoraggio"
        verbose_name_plural = "Argomenti monitoraggio"