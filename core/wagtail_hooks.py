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

