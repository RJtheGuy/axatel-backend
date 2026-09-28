from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField

from core.api_blocks import ImageAPIField
from core.base_pages import CardSectionIndexPage, CardDetailPage

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
        APIField("cover_image", serializer=ImageAPIField()),
    ]

    group = models.CharField(max_length=40, choices=GROUP_CHOICES, blank=True, verbose_name="Gruppo",
                             help_text="Colonna del menu 'Come lo realizziamo?' a cui appartiene.")
    eyebrow = models.CharField(max_length=80, blank=True, verbose_name="Sottotitolo breve",
                               help_text="Es. 'Supervisione e controllo'")
    cover_image = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+", verbose_name="Immagine")

    content_panels = CardDetailPage.content_panels[:1] + [
        MultiFieldPanel([
            FieldPanel("group"),
            FieldPanel("eyebrow"),
            FieldPanel("icon"),
            FieldPanel("short_description"),
            FieldPanel("cover_image"),
        ], heading="Intestazione e card"),
        FieldPanel("body"),
    ]

    parent_page_types = ["solutions.SolutionsIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Soluzione"
        verbose_name_plural = "Soluzioni"
