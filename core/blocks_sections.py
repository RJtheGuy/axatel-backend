from wagtail import blocks
from .api_blocks import DocumentChooserBlock, ImageChooserBlock
from .blocks_shared import INLINE_TEXT_FEATURES, ExpandedRichTextBlock


class SolutionCardItemBlock(blocks.StructBlock):
    icon = ImageChooserBlock(required=False, help_text="Icona SVG/PNG, es. smart-road.svg")
    title = ExpandedRichTextBlock(max_length=60, features=INLINE_TEXT_FEATURES)
    description = ExpandedRichTextBlock(max_length=200, features=INLINE_TEXT_FEATURES)
    link_url = blocks.CharBlock(max_length=200, required=False)  # URL - stays plain
    link_label = ExpandedRichTextBlock(max_length=40, default="Scopri", features=INLINE_TEXT_FEATURES)

    class Meta:
        icon = "grip"
        label = "Card soluzione"


class SolutionCardsBlock(blocks.StructBlock):
    """Free-form marketing tiles, deliberately NOT a PageChooserBlock
    like ServiceCardsBlock - these point at anchors/sections, not
    always real pages (e.g. '/strade#soluzioni')."""
    heading = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)
    cards = blocks.ListBlock(SolutionCardItemBlock())

    class Meta:
        icon = "grip"
        label = "Card soluzioni"


class FeatureItemBlock(blocks.StructBlock):
    icon = ImageChooserBlock(required=False)
    title = ExpandedRichTextBlock(max_length=60, features=INLINE_TEXT_FEATURES)
    # Optional: the frontend must hide the element when this is empty,
    # otherwise an empty gap is left under the title.
    description = ExpandedRichTextBlock(max_length=200, required=False, features=INLINE_TEXT_FEATURES)
    # How much of the grid row this item takes. "full" = 100% of the width.
    width = blocks.ChoiceBlock(
        choices=[
            ("normal", "Normale (1 colonna)"),
            ("wide", "Largo (2 colonne)"),
            ("full", "Intera larghezza (100%)"),
        ],
        default="normal", required=False,
        label="Larghezza",
        help_text="Su cellulare ogni vantaggio occupa comunque tutta la larghezza.",
    )

    class Meta:
        icon = "success"
        label = "Vantaggio"


class FeatureGridBlock(blocks.StructBlock):
    heading = ExpandedRichTextBlock(max_length=160, required=False, features=INLINE_TEXT_FEATURES)
    subheading = ExpandedRichTextBlock(max_length=250, required=False, features=INLINE_TEXT_FEATURES)
    # Both switches default to False, so grids already saved keep their
    # current look until an editor ticks them.
    center_heading = blocks.BooleanBlock(
        required=False, default=False,
        label="Centra titolo e sottotitolo",
    )
    center_items = blocks.BooleanBlock(
        required=False, default=False,
        label="Centra il contenuto dei vantaggi",
        help_text="Centra icona, titolo e descrizione di ogni vantaggio.",
    )
    columns = blocks.ChoiceBlock(
        choices=[
            ("auto", "Automatico"),
            ("2", "2 per riga"),
            ("3", "3 per riga"),
            ("4", "4 per riga"),
            ("5", "5 per riga"),
            ("6", "6 per riga"),
        ],
        default="auto", required=False,
        label="Card per riga",
        help_text="Su tablet e cellulare il numero si riduce da solo per restare leggibile.",
    )
    # Layout of the whole section. "auto" = the current look, so grids
    # already saved don't change until an editor picks something.
    max_width = blocks.ChoiceBlock(
        choices=[
            ("auto", "Predefinita"),
            ("narrow", "Stretta (720 px)"),
            ("normal", "Media (1000 px)"),
            ("wide", "Larga (1280 px)"),
            ("full", "Intera larghezza disponibile"),
        ],
        default="auto", required=False,
        label="Larghezza della sezione",
    )
    padding_y = blocks.ChoiceBlock(
        choices=[("auto", "Predefinito"), ("none", "Nessuno"), ("small", "Piccolo"), ("large", "Grande")],
        default="auto", required=False,
        label="Spazio sopra e sotto",
    )
    padding_x = blocks.ChoiceBlock(
        choices=[("auto", "Predefinito"), ("none", "Nessuno"), ("small", "Piccolo"), ("large", "Grande")],
        default="auto", required=False,
        label="Spazio ai lati",
    )
    gap = blocks.ChoiceBlock(
        choices=[("auto", "Predefinita"), ("small", "Piccola"), ("large", "Grande")],
        default="auto", required=False,
        label="Distanza tra i vantaggi",
    )
    # Space between the heading and what follows it. "small" = today's
    # look, so grids already saved don't change until an editor picks.
    heading_gap = blocks.ChoiceBlock(
        choices=[
            ("small", "Piccolo (com'è oggi)"),
            ("medium", "Medio"),
            ("large", "Grande"),
            ("xlarge", "Molto grande"),
        ],
        default="small", required=False,
        label="Spazio sotto il titolo",
        help_text="Distanza tra il titolo della griglia e i titoli dei vantaggi (o il sottotitolo).",
    )
    features = blocks.ListBlock(FeatureItemBlock())

    class Meta:
        icon = "list-ul"
        label = "Griglia vantaggi"


class TestimonialBlock(blocks.StructBlock):
    """Richer than QuoteBlock's plain 'attribution' string - separate
    name/role fields so the partial can style them independently
    (e.g. name bold, role in mono/uppercase like the rest of the UI)."""
    quote = ExpandedRichTextBlock(required=True, features=INLINE_TEXT_FEATURES)
    name = ExpandedRichTextBlock(max_length=100, required=False, features=INLINE_TEXT_FEATURES)
    role = ExpandedRichTextBlock(max_length=100, required=False, features=INLINE_TEXT_FEATURES)
    avatar = ImageChooserBlock(required=False)
    variant = blocks.ChoiceBlock(
        choices=[("default", "Predefinito"), ("accent", "Accento"), ("muted", "Attenuato")],
        default="default", required=False,
        help_text="Stile della sezione - usa i colori del tema attivo.",
    )

    class Meta:
        icon = "openquote"
        label = "Testimonianza"


class CertificationItemBlock(blocks.StructBlock):
    logo = ImageChooserBlock(required=False, label="Logo del certificato")
    title = ExpandedRichTextBlock(
        max_length=80, features=INLINE_TEXT_FEATURES, label="Nome",
        help_text="Es. ISO 9001:2015",
    )
    text = ExpandedRichTextBlock(
        max_length=300, required=False, features=INLINE_TEXT_FEATURES,
        label="Testo (facoltativo)",
        help_text="Es. Sistema di gestione per la qualità.",
    )
    document = DocumentChooserBlock(
        required=False, label="Certificato PDF (facoltativo)",
        help_text="Se scelto, cliccando il certificato si apre il PDF.",
    )

    class Meta:
        icon = "success"
        label = "Certificato"


class CertificationsBlock(blocks.StructBlock):
    heading = ExpandedRichTextBlock(
        max_length=120, required=False, features=INLINE_TEXT_FEATURES,
        label="Titolo (facoltativo)", help_text="Es. Certificazioni",
    )
    columns = blocks.ChoiceBlock(
        choices=[("1", "1 per riga"), ("2", "2 per riga"), ("3", "3 per riga"), ("4", "4 per riga")],
        default="3", required=False,
        label="Certificati per riga",
        help_text="Quelli in più vanno a capo nella riga sotto. Su tablet e cellulare il numero si riduce da solo.",
    )
    items = blocks.ListBlock(CertificationItemBlock(), label="Certificati")

    class Meta:
        icon = "success"
        label = "Certificazioni"


class PartnerLogosBlock(blocks.StructBlock):
    heading = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)
    logos = blocks.ListBlock(ImageChooserBlock())

    class Meta:
        icon = "image"
        label = "Loghi partner"


class PortfolioItemBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    title = ExpandedRichTextBlock(max_length=120, features=INLINE_TEXT_FEATURES)
    client = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)
    excerpt = ExpandedRichTextBlock(max_length=200, required=False, features=INLINE_TEXT_FEATURES)
    url = blocks.CharBlock(max_length=200, required=False)  # URL - stays plain

    class Meta:
        icon = "doc-full"
        label = "Caso di successo"


class PortfolioGridBlock(blocks.StructBlock):
    heading = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)
    view_all_url = blocks.CharBlock(max_length=200, required=False)  # URL - stays plain
    view_all_label = ExpandedRichTextBlock(max_length=40, default="Vedi tutto", features=INLINE_TEXT_FEATURES)
    items = blocks.ListBlock(PortfolioItemBlock())

    class Meta:
        icon = "grip"
        label = "Griglia casi di successo"
