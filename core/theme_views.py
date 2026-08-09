# """
# core/theme_views.py

# Three endpoints:
#   GET  /api/v2/themes/                -> all saved themes for this tenant
#   GET  /api/v2/themes/active/         -> the one currently live
#   POST /api/v2/themes/<id>/activate/  -> switch which theme is active

# Kept out of the pages API because a theme is not a page: it is
# tenant-wide state fetched once per app load. The 'activate' action lives
# here rather than only in the Wagtail admin so a future admin dashboard
# outside Wagtail can drive it too.
# """

# from django.shortcuts import get_object_or_404
# from rest_framework.response import Response
# from rest_framework.views import APIView
# from wagtail.models import Site

# from .models import SiteTheme

# # Mirrors the SiteTheme field defaults and the static :root block in
# # nuxt.config.ts. Previously this was the Wagtail-scaffold palette
# # (white background, green primary), so a site with no saved theme would
# # have told the frontend to render white-on-white once useTheme() was
# # wired up.
# DEFAULT_THEME = {
#     "id": None,
#     "name": "Default",
#     "primary_color": "#C52317",
#     "accent_color": "#EA3F30",
#     "text_color": "#F2F8FF",
#     "background_color": "#020712",
#     "success_color": "#2E9B5C",
#     "warning_color": "#E0A736",
#     "danger_color": "#C0392B",
#     "surface_color": "#070F18",
#     "border_color": "#1B2B3D",
#     "muted_color": "#9AB6CF",
#     "heading_font": "Montserrat, sans-serif",
#     "body_font": "Montserrat, sans-serif",
#     "base_font_size": 16,
#     "type_scale": {"h1": 39.1, "h2": 31.3, "h3": 25.0, "h4": 20.0, "h5": 16.0, "h6": 12.8},
#     "radius": "16px",
#     "shadow": "0 8px 24px rgba(0,0,0,0.15)",
#     "logo_url": None,
# }


# class ActiveThemeView(APIView):
#     """What every page load fetches. Falls back to DEFAULT_THEME when no
#     theme has been saved, so a new site renders correctly before anyone
#     has touched branding."""

#     def get(self, request):
#         site = Site.find_for_request(request)
#         theme = SiteTheme.objects.filter(site=site, is_active=True).first()
#         if theme is None:
#             return Response(DEFAULT_THEME)
#         return Response(theme.api_representation)


# class ThemeGalleryView(APIView):
#     """Powers the 'saved looks' gallery - every theme for this tenant,
#     active or not, so an admin UI can show thumbnails and let an editor
#     pick one without going through the Wagtail admin."""

#     def get(self, request):
#         site = Site.find_for_request(request)
#         themes = SiteTheme.objects.filter(site=site).order_by("-is_active", "name")
#         return Response([t.api_representation | {"is_active": t.is_active} for t in themes])


# class ActivateThemeView(APIView):
#     """Switch which theme is live. Deactivates the previously active one
#     in the same transaction, so the unique constraint (one active theme
#     per site) is never momentarily violated."""

#     def post(self, request, theme_id):
#         theme = get_object_or_404(SiteTheme, pk=theme_id)
#         from django.db import transaction

#         with transaction.atomic():
#             SiteTheme.objects.filter(site=theme.site, is_active=True).update(is_active=False)
#             theme.is_active = True
#             theme.save(update_fields=["is_active"])

#         return Response(theme.api_representation | {"is_active": True})



"""
core/theme_views.py

Matches the simplified ThemeSettings in models.py (one setting per
site, not a gallery of snippets) - but keeps the URL SHAPE that already
existed and that verify.sh and the frontend already depend on:

    GET  /api/v2/themes/active/     -> current theme (unchanged path)
    POST /api/v2/themes/restore/    -> undo the last save, if there is one (new)

ThemeGalleryView and ActivateThemeView are gone - there is no longer a
list of themes to browse or activate by id, just the one active setting
- but the /themes/active/ path itself is untouched on purpose, since
renaming an endpoint other things already call is a breaking change
that has nothing to do with simplifying storage.
"""

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