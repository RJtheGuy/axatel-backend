"""
core/settings_views.py

Exposes wagtail.contrib.settings models over the API.

Settings are not pages, so they are not part of the Wagtail pages API.
The frontend needs them on every page load (navbar, footer, chat
widget), so they get one endpoint returning all of them together -
one request rather than three.

    GET /api/v2/site-settings/
"""

from rest_framework.response import Response
from rest_framework.views import APIView
from wagtail.models import Site

from .site_settings import ChatbotSettings, FooterSettings, NavigationSettings


def _stream_raw_values(stream) -> list:
    """StreamField of a PLAIN block type (CharBlock etc.) -> list of the
    raw values.

    _stream_to_list below assumes each block value is a StructBlock and
    calls dict() on it; that raises for a CharBlock, whose value is just
    a string.
    """
    if not stream:
        return []
    return [block.value for block in stream]


def _stream_to_list(stream) -> list:
    """StreamField -> plain list of the block values.

    The frontend does not need the {type, value, id} envelope for these
    simple single-block-type streams - it just wants the items.
    """
    if not stream:
        return []
    return [dict(block.value) for block in stream]


class SiteSettingsView(APIView):
    """Everything the shell of the site needs, in one call.

    Falls back to sensible defaults when a settings object has never
    been saved, so a fresh install renders rather than erroring.
    """

    def get(self, request):
        site = Site.find_for_request(request)

        nav = NavigationSettings.for_site(site)
        footer = FooterSettings.for_site(site)
        chatbot = ChatbotSettings.for_site(site)

        return Response({
            "navigation": {
                "links": _stream_to_list(nav.links),
                "cta": {
                    "visible": nav.cta_visible,
                    "label": nav.cta_label,
                    "url": nav.cta_url,
                },
            },
            "footer": {
                "contacts": _stream_to_list(footer.contacts),
                "vat_label": footer.vat_label,
                "vat_value": footer.vat_value,
                "tax_label": footer.tax_label,
                "tax_value": footer.tax_value,
            },
            "chatbot": {
                "enabled": chatbot.enabled,
                "title": chatbot.title,
                "welcome_message": chatbot.welcome_message,
                "placeholder": chatbot.placeholder,
                "suggestions": _stream_raw_values(chatbot.suggestions),
            },
        })