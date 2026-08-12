from django.urls import path

from .settings_views import SiteSettingsView
from .theme_views import ActiveThemeView, RestoreThemeView

urlpatterns = [
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("theme/", ActiveThemeView.as_view(), name="theme-active"),
    path("theme/restore/", RestoreThemeView.as_view(), name="theme-restore"),
]