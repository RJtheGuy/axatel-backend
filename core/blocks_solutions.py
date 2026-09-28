"""
Blocks for structured solution and product pages (the Move Solutions-style
layout): a text section with highlights, a featured product, "what we
measure", "how it works" steps, device cards and case-study cards.

They are part of BODY_BLOCKS, so editors can use them on any page.
"""
from wagtail import blocks
from wagtail.models import Page
from wagtail.rich_text import expand_db_html

from .blocks_shared import INLINE_TEXT_FEATURES, ExpandedRichTextBlock, _absolutize_media_urls


def _image(image):
    if not image:
        return None
    rendition = image.get_rendition("original")
    return {
        "url": rendition.full_url,
        "alt": getattr(image, "default_alt_text", None) or image.title,
        "width": rendition.width,
        "height": rendition.height,
    }


def _live_specific(pages):
    """Chosen pages, skipping ones that were deleted or unpublished."""
    result = []
    for page in pages:
        if page is None:
            continue
        page = page.specific if isinstance(page, Page) else page
        if getattr(page, "live", False):
            result.append(page)
    return result


class TextSectionBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=160, label="Titolo")
    text = blocks.RichTextBlock(features=["bold", "italic", "link", "ol", "ul", "highlight"], label="Testo")
    highlights = blocks.ListBlock(
        blocks.CharBlock(max_length=60), required=False, label="Punti chiave",
        help_text="Brevi etichette mostrate come pillole sotto il testo, es. 'Eventi real-time'.",
    )

    class Meta:
        icon = "doc-full"
        label = "Sezione di testo"

    def get_api_representation(self, value, context=None):
        return {
            "heading": value.get("heading", ""),
            "text": _absolutize_media_urls(expand_db_html(value["text"].source)) if value.get("text") else "",
            "highlights": [h for h in value.get("highlights", []) if h],
        }


class ProductFeatureBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=60, required=False, label="Etichetta", help_text="Es. 'La soluzione Axatel'")
    name = blocks.CharBlock(max_length=120, label="Nome prodotto o servizio")
    description = blocks.TextBlock(label="Descrizione")
    product = blocks.PageChooserBlock(
        page_type="products.ProductPage", required=False, label="Pagina prodotto",
        help_text="Se scelta, il riquadro rimanda alla scheda del prodotto.",
    )
    link_url = blocks.CharBlock(max_length=300, required=False, label="Link alternativo", help_text="Es. una scheda tecnica PDF.")
    link_label = blocks.CharBlock(max_length=60, required=False, label="Testo link")

    class Meta:
        icon = "pick"
        label = "Prodotto in evidenza"

    def get_api_representation(self, value, context=None):
        product = _live_specific([value.get("product")])
        return {
            "label": value.get("label", ""),
            "name": value.get("name", ""),
            "description": value.get("description", ""),
            "product_url": product[0].url if product else None,
            "link_url": value.get("link_url", ""),
            "link_label": value.get("link_label", ""),
        }


class MeasureItemBlock(blocks.StructBlock):
    quantity = blocks.CharBlock(max_length=80, label="Grandezza", help_text="Es. 'Inclinazione'")
    unit = blocks.CharBlock(max_length=30, required=False, label="Unità", help_text="Es. 'mrad', 'µg/m³', 'veic/h'")
    note = blocks.CharBlock(max_length=160, required=False, label="Nota")


class MeasuresBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120, default="Cosa misuriamo", label="Titolo")
    items = blocks.ListBlock(MeasureItemBlock(), label="Grandezze")

    class Meta:
        icon = "table"
        label = "Cosa misuriamo"


class StepItemBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=80, label="Titolo")
    text = blocks.TextBlock(required=False, label="Testo")


class StepsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120, default="Come funziona", label="Titolo")
    steps = blocks.ListBlock(StepItemBlock(), label="Passaggi")

    class Meta:
        icon = "list-ol"
        label = "Come funziona (passaggi)"


class DeviceCardsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120, default="Dispositivi utilizzati", label="Titolo")
    products = blocks.ListBlock(blocks.PageChooserBlock(page_type="products.ProductPage"), label="Prodotti")

    class Meta:
        icon = "cogs"
        label = "Schede dispositivi"

    def get_api_representation(self, value, context=None):
        return {
            "heading": value.get("heading", ""),
            "items": [
                {
                    "title": p.title,
                    "url": p.url,
                    "model_code": getattr(p, "model_code", ""),
                    "tagline": getattr(p, "tagline", ""),
                    "image": _image(getattr(p, "cover_image", None)),
                }
                for p in _live_specific(value.get("products", []))
            ],
        }


class CaseCardsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120, default="Casi di successo", label="Titolo")
    cases = blocks.ListBlock(blocks.PageChooserBlock(page_type="casi.CasoSuccessoPage"), label="Casi")

    class Meta:
        icon = "doc-full-inverse"
        label = "Casi di successo collegati"

    def get_api_representation(self, value, context=None):
        return {
            "heading": value.get("heading", ""),
            "items": [
                {
                    "title": p.title,
                    "url": p.url,
                    "client": getattr(p, "client", ""),
                    "category": getattr(p, "category", ""),
                    "description": getattr(p, "description", ""),
                    "image": _image(getattr(p, "cover_image", None)),
                }
                for p in _live_specific(value.get("cases", []))
            ],
        }
