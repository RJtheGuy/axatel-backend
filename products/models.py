"""
Product catalogue: one page per device or system, like Move Solutions'
sensor pages. URL: /prodotti/<slug>/

A ProductPage has a model name, a category, a short tagline (used on
cards), a picture, a table of specifications, an optional datasheet and a
normal block body for anything else.
"""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from rest_framework.fields import Field
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, HelpPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Locale, Page
from wagtail.search import index
from wagtailseo.models import SeoMixin

from core.api_blocks import ImageAPIField
from core.blocks import BODY_BLOCKS

# Product categories (update 73, Marco's list). The key is stored on each
# product; the labels are shown on the site in the page's language. To add a
# category: add one line here and one in CATEGORY_LABELS, then
# `manage.py makemigrations products`.
CATEGORY_CHOICES = [
    ("lavoratori", "Protezione lavoratori"),
    ("idrogeologico", "Dissesto idrogeologico"),
    ("ambiente", "Ambiente - Verde"),
    ("strutturale", "Strutturale"),
    ("predittiva", "Manutenzione predittiva"),
    ("stradale", "Stradale"),
    ("lorawan", "Rete LoRaWAN"),
    ("master-slave", "Master-Slave-Box"),
    ("edili", "Opere edili accessorie"),
]
CATEGORY_LABELS = {
    "it": dict(CATEGORY_CHOICES),
    "en": {
        "lavoratori": "Worker protection",
        "idrogeologico": "Hydrogeological instability",
        "ambiente": "Environment - Green",
        "strutturale": "Structural",
        "predittiva": "Predictive maintenance",
        "stradale": "Roads",
        "lorawan": "LoRaWAN network",
        "master-slave": "Master-Slave-Box",
        "edili": "Ancillary building works",
    },
    "fr": {
        "lavoratori": "Protection des travailleurs",
        "idrogeologico": "Instabilité hydrogéologique",
        "ambiente": "Environnement - Espaces verts",
        "strutturale": "Structurel",
        "predittiva": "Maintenance prédictive",
        "stradale": "Routier",
        "lorawan": "Réseau LoRaWAN",
        "master-slave": "Master-Slave-Box",
        "edili": "Travaux de construction annexes",
    },
}


def category_label(key, language="it"):
    """Label of a category in a language (Italian if missing); '' for an unknown key."""
    labels = CATEGORY_LABELS.get((language or "it")[:2], CATEGORY_LABELS["it"])
    return labels.get(key) or CATEGORY_LABELS["it"].get(key, "")


# Where the product picture goes on the product page (same choice as the
# "Immagine nella pagina" of the informative pages).
COVER_POSITION_CHOICES = [
    ("side", "Accanto alla descrizione (com'è oggi)"),
    ("top", "Grande, in apertura (come nei casi di successo)"),
]


# How the picture fills its space on the cards of the Prodotti list (update 74).
CARD_FIT_CHOICES = [
    ("cover", "Riempi lo spazio (i bordi possono essere tagliati)"),
    ("contain", "Immagine intera (con margini se serve)"),
]
CARD_FIT_PRODUCT_CHOICES = [("", "Come impostato sulla pagina Prodotti")] + CARD_FIT_CHOICES


def _translation_source(page):
    """The Italian (default-language) version of a page, so the card settings
    are set once and are the same in every language."""
    default = Locale.get_default()
    if page.locale_id and page.locale_id != default.id:
        return page.get_translation_or_none(default) or page
    return page


class DocumentAPIField(Field):
    def to_representation(self, value):
        if not value:
            return None
        # Direct file URL under /media/, made absolute like images are.
        url = value.file.url
        base = getattr(settings, "WAGTAILADMIN_BASE_URL", "") or ""
        if url.startswith("/") and base:
            url = base.rstrip("/") + url
        return {"id": value.id, "title": value.title, "url": url}


class SpecBlock(blocks.StructBlock):
    label = blocks.CharBlock(max_length=80, label="Caratteristica", help_text="Es. 'Connettività'")
    value = blocks.CharBlock(max_length=240, label="Valore", help_text="Es. 'LoRaWAN'")

    class Meta:
        icon = "list-ul"
        label = "Specifica"


LAYOUT_CHOICES = [
    ("categories", "Raggruppati per categoria (un titolo per gruppo)"),
    ("single", "Un'unica griglia, senza gruppi"),
]
COLUMN_CHOICES = [
    ("auto", "Automatico (quante ne stanno)"),
    ("2", "2 per riga"),
    ("3", "3 per riga"),
    ("4", "4 per riga"),
]
ORDER_HELP = (
    "<p><b>Ordine dei prodotti</b>: è quello dell'elenco in <i>Pagine → Prodotti</i>. "
    "Apri l'elenco, scegli <i>Gestisci l'ordine del menu</i> e trascina i prodotti. "
    "Con i gruppi per categoria, l'ordine vale dentro ogni gruppo.</p>"
    "<p>Queste impostazioni valgono per tutte le lingue: si cambiano sulla pagina italiana.</p>"
)


class ProductIndexPage(SeoMixin, Page):
    """Listing of all products. URL: /prodotti/

    How the cards are laid out (update 58): grouped by category or one grid,
    the order of the groups, cards per row. The order of the products is the
    page order in the CMS (Pagine → Prodotti → "Gestisci l'ordine del menu").
    """

    api_fields = [APIField("intro"), APIField("display"), APIField("categories")]

    intro = models.TextField(blank=True, verbose_name="Introduzione", help_text="Testo sopra l'elenco dei prodotti.")
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default="categories",
                              verbose_name="Disposizione")
    category_order = StreamField(
        [("category", blocks.ChoiceBlock(choices=CATEGORY_CHOICES, label="Categoria"))],
        use_json_field=True, blank=True, verbose_name="Ordine delle categorie",
        help_text="Aggiungi le categorie e trascinale nell'ordine voluto. Quelle non elencate vengono dopo. "
                  "Vuoto = ordine standard (quello dell'elenco delle categorie). Vale anche per la barra "
                  "delle categorie in cima all'elenco.",
    )
    columns = models.CharField(max_length=4, choices=COLUMN_CHOICES, default="auto",
                               verbose_name="Prodotti per riga",
                               help_text="Su schermi grandi. Su tablet sono al massimo 2, sul telefono 1.")
    # Pictures on the cards (update 74).
    card_image_height = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(100)],
        verbose_name="Altezza delle immagini nelle card (%)",
        help_text="In percentuale della larghezza della card, da 30 a 100. Es. 50 = alta la metà della "
                  "larghezza, 75 = formato 4:3, 100 = quadrata. Vuoto = come oggi (190 px).",
    )
    card_image_fit = models.CharField(
        max_length=8, choices=CARD_FIT_CHOICES, default="cover",
        verbose_name="Adattamento delle immagini nelle card",
        help_text="Si può cambiare anche per un singolo prodotto, nella sua pagina.",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = ["products.ProductPage"]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel([
            HelpPanel(content=ORDER_HELP),
            FieldPanel("layout"),
            FieldPanel("category_order"),
            FieldPanel("columns"),
            FieldPanel("card_image_height"),
            FieldPanel("card_image_fit"),
        ], heading="Disposizione delle card"),
    ]

    @property
    def display(self):
        """Layout settings, always those of the Italian page (all languages
        show the products the same way)."""
        source = self
        default = Locale.get_default()
        if self.locale_id != default.id:
            source = self.get_translation_or_none(default) or self
        order, seen = [], set()
        for block in source.category_order:
            if block.value and block.value not in seen:
                order.append(block.value)
                seen.add(block.value)
        return {"layout": source.layout or "categories", "columns": source.columns or "auto",
                "category_order": order, "image_height": source.card_image_height,
                "image_fit": source.card_image_fit or "cover"}

    @property
    def categories(self):
        """All categories in display order ("Ordine delle categorie", then the
        standard order), with their label in this page's language. The site
        builds the category bar from this and shows only those with products."""
        valid = [key for key, _ in CATEGORY_CHOICES]
        chosen = [key for key in self.display["category_order"] if key in valid]
        language = self.locale.language_code if self.locale_id else "it"
        return [{"key": key, "label": category_label(key, language)}
                for key in chosen + [k for k in valid if k not in chosen]]

    promote_panels = SeoMixin.promote_panels

    class Meta:
        verbose_name = "Indice Prodotti"


class ProductPage(SeoMixin, Page):
    api_fields = [
        APIField("model_code"),
        APIField("product_codes"),
        APIField("available_models"),
        APIField("category"),
        APIField("category_label"),
        APIField("cover_position"),
        APIField("card_image"),
        APIField("tagline"),
        APIField("cover_image", serializer=ImageAPIField()),
        APIField("specs"),
        APIField("datasheet", serializer=DocumentAPIField()),
        APIField("datasheet_url"),
        APIField("body"),
        APIField("show_intro"),
    ]

    model_code = models.CharField(max_length=80, blank=True, verbose_name="Codice prodotto",
                                  help_text="Es. 'AXE-STD-LR-2'. Il codice principale: compare anche nelle card. "
                                            "Lascia vuoto se il nome basta.")
    # More codes for the same product (update 73).
    extra_codes = StreamField(
        [("code", blocks.CharBlock(max_length=80, label="Codice"))],
        use_json_field=True, blank=True, verbose_name="Altri codici prodotto",
        help_text="Aggiungi un codice per ogni riga, oltre a quello principale qui sopra.",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, blank=True, default="",
                                verbose_name="Categoria",
                                help_text="La categoria in cui il prodotto compare nella barra in cima all'elenco Prodotti.")
    # Variants of the same product (update 73), e.g. "Angel River 1" / "Angel River Pro".
    available_models = StreamField(
        [("model", blocks.CharBlock(max_length=120, label="Modello"))],
        use_json_field=True, blank=True, verbose_name="Modelli disponibili",
        help_text="Se il prodotto esiste in più varianti, scrivi il nome di ognuna. "
                  "Vuoto = la sezione non compare.",
    )
    cover_position = models.CharField(
        max_length=8, choices=COVER_POSITION_CHOICES, default="side", verbose_name="Immagine nella pagina",
        help_text="Nella card dell'elenco Prodotti l'immagine compare comunque.",
    )
    # This product's picture on the cards of the Prodotti list (update 74).
    card_image_fit = models.CharField(
        max_length=8, choices=CARD_FIT_PRODUCT_CHOICES, blank=True, default="",
        verbose_name="Immagine nella card: adattamento",
    )
    card_image_width = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(20), MaxValueValidator(100)],
        verbose_name="Immagine nella card: larghezza (%)",
        help_text="Da 20 a 100: rimpicciolisce l'immagine dentro il suo spazio (utile con «Immagine intera»). "
                  "Vuoto = 100. L'altezza dello spazio è la stessa per tutte le card: si imposta sulla pagina Prodotti.",
    )
    tagline = models.TextField(max_length=300, blank=True, verbose_name="Descrizione breve (card)",
                               help_text="Mostrata nelle card e usata come meta description se il tab Promuovi è vuoto.")
    cover_image = models.ForeignKey("wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="+", verbose_name="Immagine")
    specs = StreamField([("spec", SpecBlock())], use_json_field=True, blank=True, verbose_name="Specifiche tecniche")
    datasheet = models.ForeignKey("wagtaildocs.Document", null=True, blank=True, on_delete=models.SET_NULL,
                                  related_name="+", verbose_name="Scheda tecnica (PDF)")
    datasheet_url = models.URLField(max_length=400, blank=True, verbose_name="Scheda tecnica (link esterno)",
                                    help_text="Usato solo se non è caricato un PDF qui sopra.")
    body = StreamField(BODY_BLOCKS, use_json_field=True, blank=True, verbose_name="Contenuto")
    # Off = the "Scheda prodotto" (name, description, picture, buttons) stays
    # on the cards of the Prodotti list but is not shown at the top of this page.
    show_intro = models.BooleanField(
        default=True, verbose_name="Mostra la scheda in cima alla pagina",
        help_text="Se la togli, categoria, modello, descrizione, immagine e pulsanti "
                  "restano nella card dell'elenco Prodotti ma non compaiono in cima a questa pagina.",
    )

    search_fields = Page.search_fields + [
        index.SearchField("model_code"),
        index.SearchField("extra_codes"),
        index.SearchField("available_models"),
        index.SearchField("tagline"),
        index.FilterField("category"),
    ]

    parent_page_types = ["products.ProductIndexPage"]
    subpage_types = []

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("model_code"),
            FieldPanel("extra_codes"),
            FieldPanel("category"),
            FieldPanel("tagline"),
            FieldPanel("cover_image"),
            FieldPanel("cover_position"),
            FieldPanel("card_image_fit"),
            FieldPanel("card_image_width"),
            FieldPanel("show_intro"),
        ], heading="Scheda prodotto"),
        FieldPanel("available_models"),
        FieldPanel("specs"),
        MultiFieldPanel([FieldPanel("datasheet"), FieldPanel("datasheet_url")], heading="Scheda tecnica"),
        FieldPanel("body"),
    ]
    promote_panels = SeoMixin.promote_panels

    def get_meta_description(self):
        return self.search_description or self.tagline

    @property
    def product_codes(self):
        """Main code first, then the others; blanks and repeats left out."""
        codes = [self.model_code] + [block.value for block in self.extra_codes]
        seen, out = set(), []
        for code in codes:
            code = (code or "").strip()
            if code and code.lower() not in seen:
                seen.add(code.lower())
                out.append(code)
        return out

    @property
    def card_image(self):
        """Card picture settings, those of the Italian page ('' / None = page default)."""
        source = _translation_source(self)
        return {"fit": source.card_image_fit or "", "width": source.card_image_width}

    @property
    def category_label(self):
        """The category's name in this page's language ('' if not set)."""
        language = self.locale.language_code if self.locale_id else "it"
        return category_label(self.category, language)

    class Meta:
        verbose_name = "Prodotto"
        verbose_name_plural = "Prodotti"
