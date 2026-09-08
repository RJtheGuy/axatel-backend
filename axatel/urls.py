from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap as wagtail_sitemap
from wagtail.documents import urls as wagtaildocs_urls

from core.api import api_router
from core.theme_views import ActiveThemeView, RestoreThemeView
from core.settings_views import SiteSettingsView
from seo.views import robots_txt

urlpatterns = [
    path("django-admin/", admin.site.urls),

    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),

    # SEO fundamentals
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", wagtail_sitemap, name="sitemap"),

    path("api/v2/themes/active/", ActiveThemeView.as_view(), name="theme_active"),
    path("api/v2/themes/restore/", RestoreThemeView.as_view(), name="theme_restore"),

    path("api/v2/chatbot/", include("chatbot.urls")),
    path("api/v2/site-settings/", SiteSettingsView.as_view(), name="site_settings"),
    path("api/v2/", api_router.urls),


    path("", include(wagtail_urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)