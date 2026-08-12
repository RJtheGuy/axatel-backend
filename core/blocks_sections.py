from wagtail import blocks
from .api_blocks import ImageChooserBlock
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
    description = ExpandedRichTextBlock(max_length=200, features=INLINE_TEXT_FEATURES)

    class Meta:
        icon = "success"
        label = "Vantaggio"


class FeatureGridBlock(blocks.StructBlock):
    heading = ExpandedRichTextBlock(max_length=160, required=False, features=INLINE_TEXT_FEATURES)
    subheading = ExpandedRichTextBlock(max_length=250, required=False, features=INLINE_TEXT_FEATURES)
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