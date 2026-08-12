from rest_framework.response import Response
from rest_framework.views import APIView
from wagtail.models import Site

from .models import ThemeSettings

DEFAULT_THEME = {
    "name": "Default",
    "primary_color": "#C52317",
    "accent_color": "#EA3F30",
    "text_color": "#F2F8FF",
    "background_color": "#020712",
    "success_color": "#2E9B5C",
    "warning_color": "#E0A736",
    "danger_color": "#C0392B",
    "surface_color": "#070F18",
    "border_color": "#1B2B3D",
    "muted_color": "#9AB6CF",
    "heading_font": "Montserrat, sans-serif",
    "body_font": "Montserrat, sans-serif",
    "base_font_size": 16,
    "type_scale": {"h1": 39.1, "h2": 31.3, "h3": 25.0, "h4": 20.0, "h5": 16.0, "h6": 12.8},
    "radius": "16px",
    "shadow": "0 8px 24px rgba(0,0,0,0.15)",
    "logo_url": None,
    "can_restore_previous": False,
}


class ActiveThemeView(APIView):
    """What every page load fetches. Same path as before: /themes/active/."""

    def get(self, request):
        site = Site.find_for_request(request)
        theme = ThemeSettings.for_site(site)
        return Response(theme.api_representation if theme else DEFAULT_THEME)


class RestoreThemeView(APIView):
    """Undo the last theme save. New endpoint - nothing existing depends
    on this path, so it's free to name however's clearest."""

    def post(self, request):
        site = Site.find_for_request(request)
        theme = ThemeSettings.for_site(site)
        restored = theme.restore_previous()
        return Response({
            "restored": restored,
            "theme": theme.api_representation,
        })