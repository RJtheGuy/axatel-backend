from django.urls import path

from .settings_views import SiteSettingsView
from .theme_views import ActiveThemeView, RestoreThemeView
from .contact_views import ContactSubmitView

urlpatterns = [
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("theme/", ActiveThemeView.as_view(), name="theme-active"),
    path("themes/active/", ActiveThemeView.as_view(), name="theme-active-plural"),
    path("theme/restore/", RestoreThemeView.as_view(), name="theme-restore"),
    path("contact/", ContactSubmitView.as_view(), name="contact-submit"),
]