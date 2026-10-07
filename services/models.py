from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtailseo.models import SeoMixin
from wagtail.api import APIField

from core.api_blocks import ImageAPIField, TagListField
from core.blocks import BODY_BLOCKS
from core.page_meta import (
    CARD_DESCRIPTION_HELP, category_field, cover_image_field, cover_position_field, show_card_title_field,
)


class ServicesIndexPage(SeoMixin, Page):
    """
    Listing page for all services. URL: /servizi/
    The agent controls the intro content via blocks.
    The list of service cards below is auto-generated from child ServicePages.
    """
    api_fields = [
        APIField("intro"),
    ]
    intro = StreamField(
        BODY_BLOCKS, use_json_field=True, blank=True,
        verbose_name="Introduzione (sopra le card servizi)",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types     = ["services.ServicePage"]

    def get_context(self, request):
        ctx = super().get_context(request)
        ctx["services"] = (
            ServicePage.objects.live()
            .descendant_of(self)
            .order_by("title")
        )
        return ctx

    content_panels = Page.content_panels + [FieldPanel("intro")]
    promote_panels = SeoMixin.promote_panels

    class Meta:
        verbose_name = "Indice Servizi"


class ServicePage(SeoMixin, Page):
    """
    A single service page. URL: /servizi/<slug>/
    Has a summary section (shown on index cards) and a full StreamField body.
    Schema.org Service structured data is injected automatically in the template
    using the schema_service_type field.
    """
    api_fields = [
        APIField("icon"),
        APIField("category"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("cover_position"),
        APIField("short_description"),
        APIField("show_card_title"),
        APIField("tags", serializer=TagListField()),
        APIField("body"),
        APIField("schema_service_type"),
    ]


    icon              = models.CharField(
        max_length=10, blank=True,
        help_text="Emoji usata sulla card — es: 📞 🌐 🔒",
        verbose_name="Emoji icona",
    )
    short_description = models.TextField(
        max_length=300, blank=True,
        help_text=CARD_DESCRIPTION_HELP,
        verbose_name="Descrizione (card)",
    )
    category = category_field()
    cover_image = cover_image_field()
    cover_position = cover_position_field()
    show_card_title = show_card_title_field()
    tags = ClusterTaggableManager(through="services.ServicePageTag", blank=True)

    body = StreamField(
        BODY_BLOCKS, use_json_field=True, blank=True,
        verbose_name="Contenuto dettaglio servizio",
    )

    # Schema.org — helps Google understand this is a service page
    schema_service_type = models.CharField(
        max_length=120, blank=True,
        help_text="Valore Schema.org serviceType — es: 'VoIP Telephony', 'Fiber Internet'",
        verbose_name="Tipo servizio (Schema.org)",
    )

    parent_page_types = ["services.ServicesIndexPage"]
    subpage_types     = []

    # Same "📋 Meta" panel as Monitoraggio, Soluzioni and the informative
    # pages (core/page_meta.py), tags after the content like on the success stories.
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("category"),
            FieldPanel("cover_image"),
            FieldPanel("cover_position"),
            FieldPanel("short_description"),
            FieldPanel("show_card_title"),
            FieldPanel("icon"),
        ], heading="📋 Meta"),
        FieldPanel("body"),
        FieldPanel("tags"),
        MultiFieldPanel(
            [FieldPanel("schema_service_type")],
            heading="🔍 Dati strutturati Schema.org",
        ),
    ]
    promote_panels = SeoMixin.promote_panels

    def get_meta_description(self):
        """Fallback meta description to short_description if Promote tab is empty."""
        return self.search_description or self.short_description

    class Meta:
        verbose_name        = "Servizio"
        verbose_name_plural = "Servizi"


class ServicePageTag(TaggedItemBase):
    content_object = ParentalKey(
        "services.ServicePage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )
