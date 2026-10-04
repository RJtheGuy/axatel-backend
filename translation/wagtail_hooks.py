from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.widgets import PageListingButton
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from . import views
from .models import TranslationJob, TranslationMemory


@hooks.register("register_admin_urls")
def translation_urls():
    return [path("traduzioni/pagina/<int:page_id>/", views.request_translation, name="translation_request")]


@hooks.register("register_page_header_buttons")
def translate_button(page, user, view_name, next_url=None):
    """"Traduci" in the page's ⋯ menu, for Italian pages only."""
    if getattr(page, "locale", None) and page.locale.language_code == "it" and not page.is_root():
        yield PageListingButton(
            "Traduzione automatica (EN, FR)",
            reverse("translation_request", args=[page.id]),
            icon_name="globe",
            priority=45,
            page=page,
            user=user,
        )


class TranslationJobViewSet(SnippetViewSet):
    model = TranslationJob
    icon = "globe"
    menu_label = "Traduzioni richieste"
    list_display = ["page", "languages", "publish", "status", "requested_by", "created_at", "finished_at"]
    list_filter = ["status"]
    add_to_admin_menu = False


class TranslationMemoryViewSet(SnippetViewSet):
    model = TranslationMemory
    icon = "doc-full"
    menu_label = "Memoria di traduzione"
    list_display = ["source", "target", "language", "edited", "updated_at"]
    list_filter = ["language", "edited"]
    search_fields = ["source", "target"]
    add_to_admin_menu = False


register_snippet(TranslationJobViewSet)
register_snippet(TranslationMemoryViewSet)
