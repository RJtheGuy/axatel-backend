from django.http import Http404
from rest_framework.response import Response
from wagtail.models import Locale, Site

from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet


class CustomPagesAPIViewSet(PagesAPIViewSet):
    meta_fields = PagesAPIViewSet.meta_fields + [
        "seo_title",
        "search_description",
        # Same value on a page and all its translations: lets the frontend
        # match an English page to its Italian original.
        "translation_key",
    ]

    def get_queryset(self):
        """Listings default to the site's main language (Italian).

        With translations enabled, a listing without ?locale would mix
        Italian, English and French pages. Callers that don't ask for a
        language keep getting exactly what they got before: Italian only.
        Detail views (/pages/<id>/) are not filtered.
        """
        queryset = super().get_queryset()
        params = self.request.GET
        if self.action == "listing_view" and "locale" not in params and "translation_of" not in params:
            queryset = queryset.filter(locale=Locale.get_default())
        return queryset

    def find_object(self, queryset, request):
        """?html_path=/x/y/&locale=en resolves the path inside the English
        copy of the site (same slugs as Italian). Without ?locale, Wagtail's
        default lookup from the Italian home page is used."""
        language = request.GET.get("locale")
        site = Site.find_for_request(request)
        if "html_path" in request.GET and language and site is not None:
            try:
                locale = Locale.objects.get(language_code=language)
            except Locale.DoesNotExist:
                return None
            root = site.root_page.specific.get_translation_or_none(locale)
            if root is None:
                return None
            components = [c for c in request.GET["html_path"].split("/") if c]
            try:
                page, _, _ = root.specific.route(request, components)
            except Http404:
                return None
            return page if queryset.filter(id=page.id).exists() else None
        return super().find_object(queryset, request)

    def find_view(self, request):
        """
        Same lookup Wagtail's default find_view does, but returns the
        page JSON directly instead of a 302 redirect to /pages/<id>/.
        """
        queryset = self.get_queryset()
        obj = self.find_object(queryset, request)
        if obj is None:
            raise Http404("not found")

        self.kwargs["pk"] = obj.pk
        serializer = self.get_serializer(obj)
        return Response(serializer.data)


api_router = WagtailAPIRouter("wagtailapi")
api_router.register_endpoint("pages", CustomPagesAPIViewSet)
api_router.register_endpoint("images", ImagesAPIViewSet)
api_router.register_endpoint("documents", DocumentsAPIViewSet)