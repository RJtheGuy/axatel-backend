

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
