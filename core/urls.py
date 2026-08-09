"""
core/urls.py

STEP 1 update: theme endpoints follow the simplified ThemeSettings
(models.py / theme_views.py) - one setting, one optional undo, not a
gallery to list and activate.

Include this in the project's root urls.py under the same /api/v2/
prefix the Wagtail router uses:

    from core.urls import urlpatterns as core_api_urls
    urlpatterns = [
        ...
        path("api/v2/", include(core_api_urls)),
        path("api/v2/", api_router.urls),
        ...
    ]

Resulting endpoints:
    GET  /api/v2/site-settings/
    GET  /api/v2/theme/
    POST /api/v2/theme/restore/
"""

from django.urls import path

from .settings_views import SiteSettingsView
from .theme_views import ActiveThemeView, RestoreThemeView

urlpatterns = [
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("theme/", ActiveThemeView.as_view(), name="theme-active"),
    path("theme/restore/", RestoreThemeView.as_view(), name="theme-restore"),
]