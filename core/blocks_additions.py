# """
# core/blocks_additions.py

# Two new blocks to add to core/blocks.py — append the class definitions
# below to that file, and add both entries to BODY_BLOCKS. Kept in a
# separate file here only so the diff against your existing blocks.py is
# easy to review; merge these in rather than importing this file.
# """

# from wagtail import blocks


# class StatItemBlock(blocks.StructBlock):
#     """One number in a StatsBlock. Value is a plain int — the '+' or
#     '%' is a separate suffix field so the frontend can animate the
#     number counting up without parsing text apart first."""
#     value = blocks.IntegerBlock(help_text="Numero puro, es. 500 (niente + o testo)")
#     suffix = blocks.CharBlock(max_length=10, required=False, default="+")
#     label = blocks.CharBlock(max_length=80)

#     class Meta:
#         icon = "success"
#         label = "Statistica"


# class StatsBlock(blocks.StructBlock):
#     """A row of animated counters (e.g. '500+ sensori installati').
#     Numbers count up from 0 when scrolled into view — see
#     initStatCounters() in app.js. Deliberately just data here; all
#     animation logic lives in JS so this block stays simple to edit."""
#     heading = blocks.CharBlock(max_length=120, required=False)
#     stats = blocks.ListBlock(StatItemBlock())

#     class Meta:
#         icon = "order"
#         label = "Statistiche animate"


# class NetworkDiagramBlock(blocks.StructBlock):
#     """Animated sensor -> gateway -> control room flow diagram — visual
#     shorthand for what Axatel's IoT monitoring stack actually does,
#     reusing the same canvas-particle technique as the hero's star
#     formation (see initNetworkDiagrams() in app.js). Content-wise this
#     block is intentionally thin: heading + caption. The diagram itself
#     is fixed/generic rather than per-instance configurable, since its
#     value is as a consistent visual motif, not a customizable chart."""
#     heading = blocks.CharBlock(max_length=120, required=False)
#     caption = blocks.CharBlock(max_length=250, required=False)

#     class Meta:
#         icon = "site"
#         label = "Diagramma di rete (animato)"


"""
core/blocks_additions.py

Two blocks merged into core/blocks.py's BODY_BLOCKS: StatsBlock and
NetworkDiagramBlock.

STEP 3 of the theme rollout adds a `variant` field to StatsBlock, same
choice list and reasoning as HeroBlock in blocks.py - additive, existing
stats sections keep today's look via the field default.
"""

from wagtail import blocks

from .blocks_shared import INLINE_TEXT_FEATURES, ExpandedRichTextBlock


class StatItemBlock(blocks.StructBlock):
    """One number in a StatsBlock. Value is a plain int - the '+' or
    '%' is a separate suffix field so the frontend can animate the
    number counting up without parsing text apart first."""
    value = blocks.IntegerBlock(help_text="Numero puro, es. 500 (niente + o testo)")  # feeds the JS counter animation - stays plain
    suffix = blocks.CharBlock(max_length=10, required=False, default="+")  # concatenated onto the animated number - stays plain
    label = ExpandedRichTextBlock(max_length=80, features=INLINE_TEXT_FEATURES)

    class Meta:
        icon = "success"
        label = "Statistica"


class StatsBlock(blocks.StructBlock):
    """A row of animated counters (e.g. '500+ sensori installati').
    Numbers count up from 0 when scrolled into view - see
    initStatCounters() in app.js. Deliberately just data here; all
    animation logic lives in JS so this block stays simple to edit."""
    heading = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)
    stats = blocks.ListBlock(StatItemBlock())
    variant = blocks.ChoiceBlock(
        choices=[("default", "Predefinito"), ("accent", "Accento"), ("muted", "Attenuato")],
        default="default", required=False,
        help_text="Stile della sezione - usa i colori del tema attivo.",
    )

    class Meta:
        icon = "order"
        label = "Statistiche animate"


class NetworkDiagramBlock(blocks.StructBlock):
    """Animated sensor -> gateway -> control room flow diagram - visual
    shorthand for what Axatel's IoT monitoring stack actually does,
    reusing the same canvas-particle technique as the hero's star
    formation (see initNetworkDiagrams() in app.js). Content-wise this
    block is intentionally thin: heading + caption. The diagram itself
    is fixed/generic rather than per-instance configurable, since its
    value is as a consistent visual motif, not a customizable chart."""
    heading = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)
    caption = ExpandedRichTextBlock(max_length=250, required=False, features=INLINE_TEXT_FEATURES)

    class Meta:
        icon = "site"
        label = "Diagramma di rete (animato)"