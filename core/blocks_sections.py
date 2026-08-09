# """
# core/blocks_sections.py

# Five block types to close the gap between what blocks.py currently
# offers and what the legacy Axatel homepage actually needs:

#   - solution_cards  -> "Le migliori soluzioni di monitoraggio" 3-up row
#   - feature_grid    -> the 6-icon "vantaggi" strip
#   - testimonial     -> the CEO pull-quote (name + role, not just a
#                         generic attribution string like QuoteBlock has)
#   - partner_logos   -> the partner/certification logo strip
#   - portfolio_grid  -> "Casi di successo" case-study cards

# Same convention as blocks_additions.py: merge the class defs below into
# blocks.py and add the five tuples to BODY_BLOCKS. No migration needed —
# StreamField stores block type + raw value, not the serialized shape.
# """

# from wagtail import blocks
# from .api_blocks import ImageChooserBlock


# class SolutionCardItemBlock(blocks.StructBlock):
#     icon = ImageChooserBlock(required=False, help_text="Icona SVG/PNG, es. smart-road.svg")
#     title = blocks.CharBlock(max_length=60)
#     description = blocks.TextBlock(max_length=200)
#     link_url = blocks.CharBlock(max_length=200, required=False)
#     link_label = blocks.CharBlock(max_length=40, default="Scopri")

#     class Meta:
#         icon = "grip"
#         label = "Card soluzione"


# class SolutionCardsBlock(blocks.StructBlock):
#     """Free-form marketing tiles, deliberately NOT a PageChooserBlock
#     like ServiceCardsBlock — these point at anchors/sections, not
#     always real pages (e.g. '/strade#soluzioni')."""
#     heading = blocks.CharBlock(max_length=120, required=False)
#     cards = blocks.ListBlock(SolutionCardItemBlock())

#     class Meta:
#         icon = "grip"
#         label = "Card soluzioni"


# class FeatureItemBlock(blocks.StructBlock):
#     icon = ImageChooserBlock(required=False)
#     title = blocks.CharBlock(max_length=60)
#     description = blocks.TextBlock(max_length=200)

#     class Meta:
#         icon = "success"
#         label = "Vantaggio"


# class FeatureGridBlock(blocks.StructBlock):
#     heading = blocks.CharBlock(max_length=160, required=False)
#     subheading = blocks.TextBlock(max_length=250, required=False)
#     features = blocks.ListBlock(FeatureItemBlock())

#     class Meta:
#         icon = "list-ul"
#         label = "Griglia vantaggi"


# class TestimonialBlock(blocks.StructBlock):
#     """Richer than QuoteBlock's plain 'attribution' string — separate
#     name/role fields so the partial can style them independently
#     (e.g. name bold, role in mono/uppercase like the rest of the UI)."""
#     quote = blocks.TextBlock(required=True)
#     name = blocks.CharBlock(max_length=100, required=False)
#     role = blocks.CharBlock(max_length=100, required=False)
#     avatar = ImageChooserBlock(required=False)

#     class Meta:
#         icon = "openquote"
#         label = "Testimonianza"


# class PartnerLogosBlock(blocks.StructBlock):
#     heading = blocks.CharBlock(max_length=120, required=False)
#     logos = blocks.ListBlock(ImageChooserBlock())

#     class Meta:
#         icon = "image"
#         label = "Loghi partner"


# class PortfolioItemBlock(blocks.StructBlock):
#     image = ImageChooserBlock(required=True)
#     title = blocks.CharBlock(max_length=120)
#     client = blocks.CharBlock(max_length=120, required=False)
#     excerpt = blocks.TextBlock(max_length=200, required=False)
#     url = blocks.CharBlock(max_length=200, required=False)

#     class Meta:
#         icon = "doc-full"
#         label = "Caso di successo"


# class PortfolioGridBlock(blocks.StructBlock):
#     heading = blocks.CharBlock(max_length=120, required=False)
#     view_all_url = blocks.CharBlock(max_length=200, required=False)
#     view_all_label = blocks.CharBlock(max_length=40, default="Vedi tutto")
#     items = blocks.ListBlock(PortfolioItemBlock())

#     class Meta:
#         icon = "grip"
#         label = "Griglia casi di successo"



"""
core/blocks_sections.py

Five block types merged into core/blocks.py's BODY_BLOCKS:
  - solution_cards  -> "Le migliori soluzioni di monitoraggio" 3-up row
  - feature_grid    -> the 6-icon "vantaggi" strip
  - testimonial     -> the CEO pull-quote (name + role, not just a
                        generic attribution string like QuoteBlock has)
  - partner_logos   -> the partner/certification logo strip
  - portfolio_grid  -> "Casi di successo" case-study cards

STEP 3 added the `variant` field to TestimonialBlock.
STEP 4 converts every body-shaped TextBlock here (card descriptions,
the feature-grid subheading, the testimonial quote, the portfolio
excerpt) to RichTextBlock(features=INLINE_TEXT_FEATURES) from blocks.py,
so editors can bold/highlight within them - same reasoning and same
frontend caveat as QuoteBlock/CTABlock in blocks.py: old plain content
is unaffected, but the Cms* components for these five blocks need to
render these fields as HTML, not plain text, before anyone actually
uses the new formatting.

Titles/labels/headings stay CharBlock on purpose - single-line fields
where rich text doesn't make sense.
"""

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