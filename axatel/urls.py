

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
    # Django admin (hidden path for security)
    path("django-admin/", admin.site.urls),

    # Wagtail CMS admin — marketing agent logs in here
    path("cms/", include(wagtailadmin_urls)),

    # Wagtail documents (PDFs, downloads)
    path("documents/", include(wagtaildocs_urls)),

    # SEO fundamentals
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", wagtail_sitemap, name="sitemap"),

    # Theme endpoints MUST come before the api_router include below.
    # WagtailAPIRouter registers a catch-all under its prefix, so mounted
    # after "api/v2/" these paths would never be reached.
    #
    # Only two theme routes now — the theme is a single site-wide setting,
    # not a gallery of saved themes to list/activate by id, so
    # theme_gallery and theme_activate are gone. theme_active keeps its
    # original path (nothing else about the frontend contract changed).
    # theme_restore is new: one-step undo of the last theme save.
    path("api/v2/themes/active/", ActiveThemeView.as_view(), name="theme_active"),
    path("api/v2/themes/restore/", RestoreThemeView.as_view(), name="theme_restore"),

    path("api/v2/chatbot/", include("chatbot.urls")),
    path("api/v2/site-settings/", SiteSettingsView.as_view(), name="site_settings"),
    path("api/v2/", api_router.urls),


    path("", include(wagtail_urls)),
]

# Django does not serve MEDIA_URL on its own, and WhiteNoise handles
# /static/ only. Without this, every uploaded image 404s — including in
# the Wagtail admin's own image library.
#
# DEV ONLY: static() is a no-op when DEBUG is False, and is single
# threaded with no caching. In production the reverse proxy (nginx et al)
# serves /media/, or django-storages hands it to S3.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)