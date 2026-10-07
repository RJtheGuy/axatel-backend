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


# ── Extra text styles: a fixed set of colors and fonts ───────────────────
# Same mechanism as "highlight" above: each style is saved as
# <span class="u-..."> and the frontend gives that class its look
# (see rich-text-styles.css). A fixed set on purpose: editors pick from
# the site's own colors and fonts instead of any color/font, so text
# stays readable and consistent with the theme.
#
# To use one of these in a field, add its feature name (the first value
# of each row) to that field's `features` list.
#
#   (feature name, Draftail type, button label, description,
#    look inside the editor, CSS class on the site)
TEXT_STYLE_FEATURES = [
    ("color-primary", "COLOR_PRIMARY", "Pr", "Colore primario (rosso)",
     {"color": "#C52317"}, "u-primary"),
    ("color-muted", "COLOR_MUTED", "Mu", "Colore attenuato (grigio-blu)",
     {"color": "#667F97"}, "u-muted"),
    ("color-dark", "COLOR_DARK", "Sc", "Colore scuro (blu notte, per sfondi chiari)",
     {"color": "#0B355B"}, "u-dark"),
    ("font-heading", "FONT_HEADING", "Tit", "Font dei titoli, leggero",
     {"fontFamily": "Montserrat, sans-serif", "fontWeight": "300"}, "u-heading-font"),
    ("font-mono", "FONT_MONO", "</>", "Font a spaziatura fissa (tecnico)",
     {"fontFamily": "monospace"}, "u-mono"),
    ("size-large", "SIZE_LARGE", "A+", "Testo più grande",
     {"fontSize": "1.25em"}, "u-large"),
]


@hooks.register("register_rich_text_features")
def register_text_style_features(features):
    for name, style_type, label, description, preview, css_class in TEXT_STYLE_FEATURES:
        features.register_editor_plugin(
            "draftail",
            name,
            InlineStyleFeature({
                "type": style_type,
                "label": label,
                "description": description,
                "style": preview,
            }),
        )
        features.register_converter_rule("contentstate", name, {
            "from_database_format": {
                f"span[class={css_class}]": InlineStyleElementHandler(style_type),
            },
            "to_database_format": {
                "style_map": {style_type: {"element": "span", "props": {"class": css_class}}},
            },
        })



# ── Rapporti → Controllo contenuti (core/content_audit.py) ───────────────
from django.shortcuts import render  # noqa: E402
from django.urls import path, reverse  # noqa: E402
from wagtail.admin.menu import MenuItem  # noqa: E402


def content_audit_view(request):
    from .content_audit import GROUPS, run_audit, summary

    findings = run_audit()
    sections = [(key, label, help_text, [f for f in findings if f.group == key])
                for key, label, help_text in GROUPS]
    return render(request, "core/content_audit.html", {
        "groups": summary(findings),
        "sections": [s for s in sections if s[3]],
        "total": len(findings),
    })


@hooks.register("register_admin_urls")
def content_audit_urls():
    return [path("controllo-contenuti/", content_audit_view, name="content_audit")]


@hooks.register("register_reports_menu_item")
def content_audit_menu():
    return MenuItem("Controllo contenuti", reverse("content_audit"), icon_name="tasks", order=50)
