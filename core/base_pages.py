
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtailseo.models import SeoMixin
 
from core.blocks import BODY_BLOCKS
from core.page_meta import CARD_DESCRIPTION_HELP
 
 
class CardSectionIndexPage(SeoMixin, Page):

    api_fields = [APIField("intro")]
 
    intro = StreamField(
        BODY_BLOCKS, use_json_field=True, blank=True,
        verbose_name="Introduzione (sopra le card)",
    )
 
    content_panels = Page.content_panels + [FieldPanel("intro")]
    promote_panels = SeoMixin.promote_panels
 
    class Meta:
        abstract = True
 
 
class CardDetailPage(SeoMixin, Page):

    api_fields = [
        APIField("icon"),
        APIField("short_description"),
        APIField("body"),
    ]
 
    icon = models.CharField(
        max_length=10, blank=True,
        help_text="Emoji usata sulla card",
        verbose_name="Emoji icona",
    )
    short_description = models.TextField(
        max_length=700, blank=True,
        help_text=CARD_DESCRIPTION_HELP,
        verbose_name="Descrizione (card)",
    )
    body = StreamField(
        BODY_BLOCKS, use_json_field=True, blank=True,
        verbose_name="Contenuto",
    )
 
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("icon"),
            FieldPanel("short_description"),
        ], heading="📋 Riepilogo card (mostrato nell'indice)"),
        FieldPanel("body"),
    ]
    promote_panels = SeoMixin.promote_panels
 
    def get_meta_description(self):
        return self.search_description or self.short_description
 
    class Meta:
        abstract = True
