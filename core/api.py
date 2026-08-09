"""
core/api.py
"""

from django.http import Http404
from rest_framework.response import Response

from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.documents.api.v2.views import DocumentsAPIViewSet


class CustomPagesAPIViewSet(PagesAPIViewSet):
    meta_fields = PagesAPIViewSet.meta_fields + [
        "seo_title",
        "search_description",
    ]

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