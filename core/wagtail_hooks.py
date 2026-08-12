"""
adds "Evidenzia" (highlight) as a Draftail
inline style, alongside the built-in bold/italic. It's the mechanism
that answers "some text bold, some not, in the same paragraph" for
color instead of weight - an editor selects a phrase and applies it,
same gesture as bold.

Deliberately NOT a color picker. It wraps the selection in one fixed
class (`u-accent`), which maps to `var(--color-accent)` in CSS - the
same theme variable ThemeSettings.api_representation feeds the
frontend. That's the point: an editor can never pick a color that isn't
already part of the theme, and if the theme's accent color changes
later, every highlighted phrase across the whole site updates with it
automatically. No per-instance hex ever gets stored in page content.

"""

from wagtail import hooks
from wagtail.admin.rich_text.converters.html_to_contentstate import InlineStyleElementHandler
from wagtail.admin.rich_text.editors.draftail.features import InlineStyleFeature


@hooks.register("register_rich_text_features")
def register_highlight_feature(features):
    feature_name = "highlight"

    features.register_editor_plugin(
        "draftail",
        feature_name,
        InlineStyleFeature({
            "type": "HIGHLIGHT",
            "label": "H",
            "description": "Evidenzia (colore accento)",
            # Renders inline in the Draftail editor itself so an editor
            "style": {"color": "#EA3F30"},
        }),
    )

    features.register_converter_rule("contentstate", feature_name, {
        "from_database_format": {
            "span[class=u-accent]": InlineStyleElementHandler("HIGHLIGHT"),
        },
        "to_database_format": {
            "style_map": {"HIGHLIGHT": {"element": "span", "props": {"class": "u-accent"}}},
        },
    })

    # NOT added to default_features on purpose - only blocks/fields that
    # explicitly list "highlight" in their `features` get it, same as
    # every other feature in this project (see RichTextBlock.Meta.features
    # in blocks.py). Keeps the toolbar from growing unasked-for on
    # fields no one requested it for.