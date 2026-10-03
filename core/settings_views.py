
from rest_framework.response import Response
from rest_framework.views import APIView
from wagtail.models import Site

from .site_settings import ChatbotSettings, FooterSettings, NavigationSettings, TeamSettings


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


def _stream_via_api_repr(stream, context=None) -> list:

    if not stream:
        return []
    return [
        block.block.get_api_representation(block.value, context=context)
        for block in stream
    ]


SUPPORTED_LANGUAGES = {"it", "en", "fr"}


class SiteSettingsView(APIView):

    def get(self, request):
        site = Site.find_for_request(request)
        language = request.GET.get("locale", "it")
        if language not in SUPPORTED_LANGUAGES:
            language = "it"
        context = {"locale": language}

        nav = NavigationSettings.for_site(site)
        footer = FooterSettings.for_site(site)
        chatbot = ChatbotSettings.for_site(site)

        return Response({
            "navigation": {
                # Entries switched off with "Visibile" are left out.
                "items": [item for item in _stream_via_api_repr(nav.items, context) if item.get("visible", True)],
                "cta": {
                    "visible": nav.cta_visible,
                    "label": (getattr(nav, f"cta_label_{language}", "") or "").strip() or nav.cta_label,
                    # True when an English/French label wasn't entered and the
                    # Italian one is sent instead; the site then uses its own
                    # translation of "Parla con un esperto".
                    "label_is_fallback": language != "it" and not (getattr(nav, f"cta_label_{language}", "") or "").strip(),
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

class TeamView(APIView):
    """People for /azienda/team (Impostazioni → Team), visible ones only,
    in the editors' order, with role, description and department in the
    requested language (Italian when no translation was entered), and
    "reportsTo": the id of the person they report to, or null at the top."""

    def get(self, request):
        site = Site.find_for_request(request)
        language = request.GET.get("locale", "it")
        if language not in SUPPORTED_LANGUAGES:
            language = "it"
        team = TeamSettings.for_site(site)
        everyone = {
            m.pk: m
            for m in team.members.select_related("photo").prefetch_related("also_reports_to").order_by("sort_order")
        }

        def visible_from(member, boss_id):
            """Nearest visible person from boss_id up the chain (a hidden
            manager is skipped, so their team stays attached to the tree).
            Loops entered by mistake in the CMS end at the top."""
            seen = {member.pk}
            boss = everyone.get(boss_id)
            while boss is not None and boss.pk not in seen:
                if boss.visible:
                    return boss.pk
                seen.add(boss.pk)
                boss = everyone.get(boss.reports_to_id)
            return None

        def manager_of(member):
            return visible_from(member, member.reports_to_id)

        def also_managers_of(member, main):
            ids = []
            for other in member.also_reports_to.all():
                boss = visible_from(member, other.pk)
                if boss and boss != main and boss != member.pk and boss not in ids:
                    ids.append(boss)
            return ids

        members = []
        for member in everyone.values():
            if not member.visible:
                continue
            photo = None
            if member.photo:
                rendition = member.photo.get_rendition("fill-400x400-c50")
                photo = {
                    "url": rendition.full_url,
                    "alt": member.name,
                    "width": rendition.width,
                    "height": rendition.height,
                }
            members.append({
                "id": member.pk,
                "name": member.name,
                "role": member.translated("role", language),
                "bio": member.translated("bio", language),
                "photo": photo,
                "reportsTo": manager_of(member),
                "alsoReportsTo": also_managers_of(member, manager_of(member)),
                "department": member.translated("department", language),
            })
        return Response({"members": members, "labelMode": team.label_mode})
