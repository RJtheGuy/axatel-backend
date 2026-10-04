"""
Blocks for structured solution and product pages (the Move Solutions-style
layout): a text section with highlights, a featured product, "what we
measure", "how it works" steps, device cards and case-study cards.

They are part of BODY_BLOCKS, so editors can use them on any page.
"""
from wagtail import blocks
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.models import Page
from wagtail.rich_text import expand_db_html

from .blocks_shared import INLINE_TEXT_FEATURES, ExpandedRichTextBlock, _absolutize_media_urls, document_file_url


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


BUTTON_STYLE_CHOICES = [("secondary", "Contorno"), ("primary", "Pieno (rosso)")]


class LinkButtonBlock(blocks.StructBlock):
    """One button: to a page of the site, to a PDF in Documenti, or to any
    address. If more than one is filled in, the page wins, then the PDF."""
    label = blocks.CharBlock(max_length=60, label="Testo del pulsante", help_text="Es. 'Scheda tecnica', 'Manuale', 'Video'")
    page = blocks.PageChooserBlock(required=False, label="Pagina del sito")
    document = DocumentChooserBlock(
        required=False, label="Documento (PDF)",
        help_text="Carica il file in Documenti: resta sul vostro server e si apre in una nuova scheda.",
    )
    url = blocks.CharBlock(max_length=300, required=False, label="Oppure un indirizzo", help_text="Es. https://… o /contatti")
    style = blocks.ChoiceBlock(choices=BUTTON_STYLE_CHOICES, default="secondary", label="Aspetto")

    class Meta:
        icon = "link"
        label = "Pulsante"

    def get_api_representation(self, value, context=None):
        page = _live_specific([value.get("page")])
        if page:
            href, kind = page[0].url, "page"
        elif value.get("document"):
            href, kind = document_file_url(value["document"]), "document"
        else:
            href = (value.get("url") or "").strip()
            kind = "page" if href.startswith("/") and not href.startswith("/media/") else "url"
        return {"label": value.get("label", ""), "href": href, "kind": kind, "style": value.get("style") or "secondary"}


class ProductFeatureBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=60, required=False, label="Etichetta", help_text="Es. 'La soluzione Axatel'")
    name = blocks.CharBlock(max_length=120, label="Nome prodotto o servizio")
    description = blocks.TextBlock(label="Descrizione")
    product = blocks.PageChooserBlock(
        page_type="products.ProductPage", required=False, label="Pagina prodotto",
        help_text="Se scelta, il primo pulsante (rosso) rimanda alla scheda del prodotto.",
    )
    link_url = blocks.CharBlock(
        max_length=300, required=False, label="Link alternativo",
        help_text="Vecchio campo per un solo link: per i PDF usa i Pulsanti qui sotto.",
    )
    link_label = blocks.CharBlock(max_length=60, required=False, label="Testo link")
    buttons = blocks.ListBlock(
        LinkButtonBlock(), required=False, label="Pulsanti",
        help_text="Quanti ne servono: schede tecniche, manuali, pagine collegate. Trascina per cambiare l'ordine.",
    )

    class Meta:
        icon = "pick"
        label = "Prodotto in evidenza"

    def get_api_representation(self, value, context=None):
        product = _live_specific([value.get("product")])
        button_block = self.child_blocks["buttons"].child_block
        buttons = [button_block.get_api_representation(item, context=context) for item in value.get("buttons") or []]
        buttons = [b for b in buttons if b["label"] and b["href"]]
        return {
            "label": value.get("label", ""),
            "name": value.get("name", ""),
            "description": value.get("description", ""),
            "product_url": product[0].url if product else None,
            "link_url": value.get("link_url", ""),
            "link_label": value.get("link_label", ""),
            "buttons": buttons,
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


class FaqItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(max_length=200, label="Domanda")
    answer = blocks.RichTextBlock(features=["bold", "italic", "link", "ol", "ul"], label="Risposta")

    class Meta:
        icon = "help"
        label = "Domanda"


class FaqBlock(blocks.StructBlock):
    """Questions and answers that open one at a time. The site also tells
    search engines they are an FAQ (schema.org FAQPage)."""
    heading = blocks.CharBlock(max_length=120, required=False, default="Domande frequenti", label="Titolo")
    items = blocks.ListBlock(FaqItemBlock(), label="Domande")

    class Meta:
        icon = "help"
        label = "Domande frequenti"

    def get_api_representation(self, value, context=None):
        return {
            "heading": value.get("heading", ""),
            "items": [
                {
                    "question": item.get("question", ""),
                    "answer": _absolutize_media_urls(expand_db_html(item["answer"].source)) if item.get("answer") else "",
                }
                for item in value.get("items", [])
            ],
        }


CONTACT_FORM_TYPES = [
    ("contact", "Richiesta di contatto"),
    ("partner", "Proposta di collaborazione (Diventa partner)"),
    ("candidate", "Candidatura (Lavora con noi)"),
    ("quote", "Richiesta di preventivo"),
]


class ContactFormBlock(blocks.StructBlock):
    """A contact form right on the page, so visitors don't need an extra
    click to /contatti. Requests arrive in the same list as the contact
    page (django-admin → Richieste di contatto), marked with their type.
    Add or remove the block to switch the form on or off for a page."""
    heading = blocks.CharBlock(max_length=120, required=False, default="Scrivici", label="Titolo")
    intro = blocks.TextBlock(required=False, label="Testo sopra il modulo")
    form_type = blocks.ChoiceBlock(
        choices=CONTACT_FORM_TYPES, default="contact", label="Tipo di richiesta",
        help_text="Così sai da quale pagina arriva la richiesta.",
    )
    show_company = blocks.BooleanBlock(required=False, default=True, label="Chiedi l'azienda")
    show_phone = blocks.BooleanBlock(required=False, default=True, label="Chiedi il telefono")
    show_message = blocks.BooleanBlock(required=False, default=True, label="Chiedi un messaggio")
    show_attachment = blocks.BooleanBlock(
        required=False, default=False, label="Permetti un allegato (CV o documento)",
        help_text="PDF, Word, ODT, RTF o TXT, massimo 10 MB.",
    )
    submit_label = blocks.CharBlock(max_length=40, required=False, label="Testo del pulsante", help_text="Vuoto = 'Invia richiesta'.")
    success_message = blocks.CharBlock(max_length=200, required=False, label="Messaggio dopo l'invio",
                                       help_text="Vuoto = 'Richiesta inviata. Ti risponderemo al più presto.'")

    class Meta:
        icon = "mail"
        label = "Modulo di contatto"

    def get_api_representation(self, value, context=None):
        return {
            "heading": value.get("heading") or "",
            "intro": value.get("intro") or "",
            "form_type": value.get("form_type") or "contact",
            "show_company": bool(value.get("show_company")),
            "show_phone": bool(value.get("show_phone")),
            "show_message": bool(value.get("show_message")),
            "show_attachment": bool(value.get("show_attachment")),
            "submit_label": value.get("submit_label") or "",
            "success_message": value.get("success_message") or "",
        }
