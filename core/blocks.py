# """
# core/blocks.py

# The single source of truth for every "component" an editor can drop into a
# page's StreamField body. Each block class here maps 1:1 to a Blade partial
# in resources/views/partials/blocks/ — the `type` name Wagtail serializes in
# the API response (e.g. "hero", "rich_text") must match the partial filename
# exactly. Add a block here + a partial there, and every page type that uses
# BODY_BLOCKS gets it for free.
# """

# from wagtail import blocks
# from wagtail.embeds.blocks import EmbedBlock

# from .api_blocks import ImageChooserBlock
# from .api_blocks import DocumentChooserBlock
# from .blocks_additions import StatsBlock, NetworkDiagramBlock
# from .blocks_sections import (
#     SolutionCardsBlock,
#     FeatureGridBlock,
#     TestimonialBlock,
#     PartnerLogosBlock,
#     PortfolioGridBlock,
# )


# class HeroBlock(blocks.StructBlock):
#     heading = blocks.CharBlock(max_length=120, required=True)
#     subheading = blocks.CharBlock(max_length=200, required=False)
#     background_image = ImageChooserBlock(required=False)
#     cta_label = blocks.CharBlock(max_length=40, required=False)
#     cta_url = blocks.CharBlock(max_length=200, required=False)

#     class Meta:
#         icon = "image"
#         label = "Hero"
#         template = None


# class RichTextBlock(blocks.RichTextBlock):
#     class Meta:
#         icon = "doc-full"
#         label = "Testo"
#         features = [
#             "bold", "italic", "link", "ol", "ul",
#             "h2", "h3", "h4", "document-link",
#         ]


# class ImageBlock(blocks.StructBlock):
#     image = ImageChooserBlock(required=True)
#     caption = blocks.CharBlock(max_length=250, required=False)
#     alt_text = blocks.CharBlock(max_length=250, required=False)

#     class Meta:
#         icon = "image"
#         label = "Immagine"


# class QuoteBlock(blocks.StructBlock):
#     quote = blocks.TextBlock(required=True)
#     attribution = blocks.CharBlock(max_length=120, required=False)

#     class Meta:
#         icon = "openquote"
#         label = "Citazione"


# class CTABlock(blocks.StructBlock):
#     heading = blocks.CharBlock(max_length=120, required=True)
#     body = blocks.TextBlock(required=False)
#     button_label = blocks.CharBlock(max_length=40, default="Contattaci")
#     button_url = blocks.CharBlock(max_length=200, default="/contatti/")
#     style = blocks.ChoiceBlock(
#         choices=[("primary", "Primario"), ("subtle", "Discreto")],
#         default="primary",
#     )

#     class Meta:
#         icon = "pick"
#         label = "Invito all'azione"


# class ServiceCardsBlock(blocks.StructBlock):
#     heading = blocks.CharBlock(max_length=120, required=False)
#     services = blocks.ListBlock(
#         blocks.PageChooserBlock(page_type="services.ServicePage")
#     )

#     class Meta:
#         icon = "list-ul"
#         label = "Card servizi (selezione manuale)"


# class ColumnsBlock(blocks.StructBlock):
#     left = blocks.StreamBlock([
#         ("rich_text", RichTextBlock()),
#         ("image", ImageBlock()),
#     ], required=False)
#     right = blocks.StreamBlock([
#         ("rich_text", RichTextBlock()),
#         ("image", ImageBlock()),
#     ], required=False)

#     class Meta:
#         icon = "grip"
#         label = "Due colonne"


# class VideoEmbedBlock(blocks.StructBlock):
#     embed = EmbedBlock(required=True, help_text="URL YouTube o Vimeo")
#     caption = blocks.CharBlock(max_length=250, required=False)

#     class Meta:
#         icon = "media"
#         label = "Video"


# class DownloadBlock(blocks.StructBlock):
#     document = DocumentChooserBlock(required=True)
#     label = blocks.CharBlock(max_length=120, required=False)

#     class Meta:
#         icon = "doc-full-inverse"
#         label = "Download"


# class SpacerBlock(blocks.StructBlock):
#     size = blocks.ChoiceBlock(
#         choices=[("sm", "Piccolo"), ("md", "Medio"), ("lg", "Grande")],
#         default="md",
#     )

#     class Meta:
#         icon = "horizontalrule"
#         label = "Spaziatore"


# # ── The registry ────────────────────────────────────────────────────────
# # 17 block types, each appearing exactly once. If you add a new block,
# # add it here ONCE — check this list before pasting, don't just append.
# BODY_BLOCKS = [
#     ("hero", HeroBlock()),
#     ("rich_text", RichTextBlock()),
#     ("image", ImageBlock()),
#     ("quote", QuoteBlock()),
#     ("cta", CTABlock()),
#     ("service_cards", ServiceCardsBlock()),
#     ("columns", ColumnsBlock()),
#     ("video_embed", VideoEmbedBlock()),
#     ("download", DownloadBlock()),
#     ("spacer", SpacerBlock()),
#     ("stats", StatsBlock()),
#     ("network_diagram", NetworkDiagramBlock()),
#     ("solution_cards", SolutionCardsBlock()),
#     ("feature_grid", FeatureGridBlock()),
#     ("testimonial", TestimonialBlock()),
#     ("partner_logos", PartnerLogosBlock()),
#     ("portfolio_grid", PortfolioGridBlock()),
# ]



"""
core/blocks.py

The single source of truth for every "component" an editor can drop into a
page's StreamField body. Each block class here maps 1:1 to a Blade partial
in resources/views/partials/blocks/ - the `type` name Wagtail serializes in
the API response (e.g. "hero", "rich_text") must match the partial filename
exactly. Add a block here + a partial there, and every page type that uses
BODY_BLOCKS gets it for free.

STEP 4: QuoteBlock.quote and CTABlock.body converted from plain TextBlock
to RichTextBlock(features=INLINE_TEXT_FEATURES) - editors can now bold/
highlight within them, same as the main Testo block, just with a smaller
feature set (no headings/lists - these are inline snippets, not articles).

Existing plain-text content in these fields is unaffected: a StreamField
TextBlock value is just a string, and RichTextBlock also stores a plain
string (interpreted as HTML) - so old entries with no markup render
identically either way. The thing that changes is what NEW entries can
contain, which means the frontend Cms* components for these two blocks
need to switch from plain text interpolation to HTML rendering (v-html /
your rich-text helper) BEFORE anyone actually bolds something in them -
otherwise the tags show up literally on the page. See the note wherever
these fields are consumed in the frontend.
"""

from wagtail import blocks
from wagtail.embeds.blocks import EmbedBlock

from .api_blocks import ImageChooserBlock
from .api_blocks import DocumentChooserBlock
from .api_blocks import PageChooserBlock
from .blocks_additions import StatsBlock, NetworkDiagramBlock
from .blocks_sections import (
    SolutionCardsBlock,
    FeatureGridBlock,
    TestimonialBlock,
    PartnerLogosBlock,
    PortfolioGridBlock,
)
from .blocks_shared import SECTION_VARIANT_CHOICES, INLINE_TEXT_FEATURES, ExpandedRichTextBlock


class HeroBlock(blocks.StructBlock):
    heading = ExpandedRichTextBlock(max_length=120, required=True, features=INLINE_TEXT_FEATURES)
    subheading = ExpandedRichTextBlock(max_length=200, required=False, features=INLINE_TEXT_FEATURES)
    background_image = ImageChooserBlock(required=False)
    cta_label = ExpandedRichTextBlock(max_length=40, required=False, features=INLINE_TEXT_FEATURES)
    cta_url = blocks.CharBlock(max_length=200, required=False)  # URL - stays plain, see module docstring
    variant = blocks.ChoiceBlock(
        choices=SECTION_VARIANT_CHOICES, default="default", required=False,
        help_text="Stile della sezione - usa i colori del tema attivo.",
    )

    class Meta:
        icon = "image"
        label = "Hero"
        template = None


class RichTextBlock(ExpandedRichTextBlock):
    class Meta:
        icon = "doc-full"
        label = "Testo"
        features = [
            "bold", "italic", "link", "ol", "ul",
            "h2", "h3", "h4", "document-link",
            "highlight",
        ]


class ImageBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = ExpandedRichTextBlock(max_length=250, required=False, features=INLINE_TEXT_FEATURES)
    alt_text = blocks.CharBlock(max_length=250, required=False)  # a11y attribute - stays plain, see module docstring

    class Meta:
        icon = "image"
        label = "Immagine"


class QuoteBlock(blocks.StructBlock):
    quote = ExpandedRichTextBlock(required=True, features=INLINE_TEXT_FEATURES)
    attribution = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)

    class Meta:
        icon = "openquote"
        label = "Citazione"


class CTABlock(blocks.StructBlock):
    heading = ExpandedRichTextBlock(max_length=120, required=True, features=INLINE_TEXT_FEATURES)
    body = ExpandedRichTextBlock(required=False, features=INLINE_TEXT_FEATURES)
    button_label = ExpandedRichTextBlock(max_length=40, default="Contattaci", features=INLINE_TEXT_FEATURES)
    button_url = blocks.CharBlock(max_length=200, default="/contatti/")  # URL - stays plain
    style = blocks.ChoiceBlock(
        choices=[("primary", "Primario"), ("subtle", "Discreto")],
        default="primary",
    )

    class Meta:
        icon = "pick"
        label = "Invito all'azione"


class ServiceCardsBlock(blocks.StructBlock):
    heading = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)
    services = blocks.ListBlock(
        PageChooserBlock(page_type="services.ServicePage")
    )

    class Meta:
        icon = "list-ul"
        label = "Card servizi (selezione manuale)"


class ColumnsBlock(blocks.StructBlock):
    left = blocks.StreamBlock([
        ("rich_text", RichTextBlock()),
        ("image", ImageBlock()),
    ], required=False)
    right = blocks.StreamBlock([
        ("rich_text", RichTextBlock()),
        ("image", ImageBlock()),
    ], required=False)

    class Meta:
        icon = "grip"
        label = "Due colonne"


class VideoEmbedBlock(blocks.StructBlock):
    embed = EmbedBlock(required=True, help_text="URL YouTube o Vimeo")
    caption = ExpandedRichTextBlock(max_length=250, required=False, features=INLINE_TEXT_FEATURES)

    class Meta:
        icon = "media"
        label = "Video"


class DownloadBlock(blocks.StructBlock):
    document = DocumentChooserBlock(required=True)
    label = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)

    class Meta:
        icon = "doc-full-inverse"
        label = "Download"


class SpacerBlock(blocks.StructBlock):
    size = blocks.ChoiceBlock(
        choices=[("sm", "Piccolo"), ("md", "Medio"), ("lg", "Grande")],
        default="md",
    )

    class Meta:
        icon = "horizontalrule"
        label = "Spaziatore"


# ── The registry ────────────────────────────────────────────────────────
# 17 block types, each appearing exactly once. If you add a new block,
# add it here ONCE - check this list before pasting, don't just append.
BODY_BLOCKS = [
    ("hero", HeroBlock()),
    ("rich_text", RichTextBlock()),
    ("image", ImageBlock()),
    ("quote", QuoteBlock()),
    ("cta", CTABlock()),
    ("service_cards", ServiceCardsBlock()),
    ("columns", ColumnsBlock()),
    ("video_embed", VideoEmbedBlock()),
    ("download", DownloadBlock()),
    ("spacer", SpacerBlock()),
    ("stats", StatsBlock()),
    ("network_diagram", NetworkDiagramBlock()),
    ("solution_cards", SolutionCardsBlock()),
    ("feature_grid", FeatureGridBlock()),
    ("testimonial", TestimonialBlock()),
    ("partner_logos", PartnerLogosBlock()),
    ("portfolio_grid", PortfolioGridBlock()),
]