"""
"Card di pagine": cards for ANY pages of the site, chosen by the editor,
usable in every StreamField that uses BODY_BLOCKS.

It only READS the pages it is given and touches no model, so it can't
conflict with products, services, solutions or case studies. Each page type
keeps its own fields; this block just picks the card text and picture each
one already has:

    product       tagline            + cover_image
    case study    description        + cover_image (+ client)
    service etc.  short_description  (+ cover_image when the page has one)

Pages that are deleted or not published are skipped.
"""
import re

from django.utils.text import Truncator
from wagtail import blocks

from .blocks_solutions import _image, _live_specific

# Card text, in order of preference: the first one the page has and that is filled in.
DESCRIPTION_FIELDS = ("card_excerpt", "short_description", "tagline", "description", "introduction")


def _plain(value) -> str:
    """Text without HTML tags; anything that is not text gives ''."""
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def _card(page) -> dict:
    description = ""
    for name in DESCRIPTION_FIELDS:
        description = _plain(getattr(page, name, ""))
        if description:
            break

    # Product pages store a category key ("sistemi"): show its label instead.
    display = getattr(page, "get_category_display", None)
    category = display() if callable(display) else getattr(page, "category", "")

    return {
        "title": page.title,
        "url": page.url,
        "kind": page._meta.model_name,  # e.g. "productpage": the card shows product logos uncropped
        "category": category if isinstance(category, str) else "",
        "client": getattr(page, "client", "") or "",  # only case studies have one
        "model_code": getattr(page, "model_code", "") or "",  # only products have one
        "description": Truncator(description).chars(220),
        "image": _image(getattr(page, "cover_image", None)),
    }


class PageCardsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(max_length=120, required=False, label="Titolo")
    pages = blocks.ListBlock(
        blocks.PageChooserBlock(),
        label="Pagine",
        help_text="Qualsiasi pagina del sito: prodotti, servizi, soluzioni, casi di successo. "
                  "Trascina per cambiare l'ordine.",
    )
    columns = blocks.ChoiceBlock(
        choices=[("auto", "Automatico"), ("2", "2 per riga"), ("3", "3 per riga"), ("4", "4 per riga")],
        default="auto", required=False, label="Card per riga",
    )
    show_image = blocks.BooleanBlock(required=False, default=True, label="Mostra l'immagine")
    show_description = blocks.BooleanBlock(required=False, default=True, label="Mostra il testo breve")
    button_label = blocks.CharBlock(
        max_length=40, required=False, label="Testo del pulsante",
        help_text="Es. 'Scopri'. Vuoto = nessun pulsante: tutta la card resta un link.",
    )

    class Meta:
        icon = "doc-full-inverse"
        label = "Card di pagine (qualsiasi pagina)"

    def get_api_representation(self, value, context=None):
        cards = [_card(page) for page in _live_specific(value.get("pages", []))]
        return {
            "heading": value.get("heading", ""),
            "columns": value.get("columns") or "auto",
            "show_image": bool(value.get("show_image")),
            "show_description": bool(value.get("show_description")),
            "button_label": value.get("button_label", ""),
            "items": [card for card in cards if card["url"]],
        }
