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
    heading = ExpandedRichTextBlock(max_length=120, required=False, features=INLINE_TEXT_FEATURES)
    caption = ExpandedRichTextBlock(max_length=250, required=False, features=INLINE_TEXT_FEATURES)

    class Meta:
        icon = "site"
        label = "Diagramma di rete (animato)"