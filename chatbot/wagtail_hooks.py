"""
The "Chatbot" menu of the CMS:

  Voci chatbot          answers written by hand (they win over the site's)
  Domande ricevute      what visitors asked and how the bot answered;
                        "Crea risposta" turns a question into a Voce chatbot
  Suggerimenti          the bubble's text and questions for one page
  Prova il chatbot      ask questions as a visitor, with the reasons behind
                        each answer, and the most asked unanswered questions
  Impostazioni          Impostazioni → Chatbot
"""
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import CreateView, SnippetViewSet, SnippetViewSetGroup

from .models import ChatbotEntry, ChatbotHint, ChatbotQuestion


class ChatbotEntryCreateView(CreateView):
    """ "Crea risposta" from Domande ricevute: the question is already filled in."""

    def get_initial_form_instance(self):
        instance = super().get_initial_form_instance() or self.model()
        question = (self.request.GET.get("domanda") or "").strip()[:300]
        if question and not instance.questions:
            instance.questions = question
        return instance


class ChatbotEntryViewSet(SnippetViewSet):
    model = ChatbotEntry
    icon = "comment"
    menu_label = "Voci chatbot"
    add_view_class = ChatbotEntryCreateView
    list_display = ["__str__", "active", "page", "updated_at"]
    list_filter = ["active", "is_fallback"]
    search_fields = ["questions", "answer"]


class ChatbotQuestionViewSet(SnippetViewSet):
    """What visitors asked. Filter "Risposto: No" to see the questions the
    bot could not answer, then "Crea risposta"."""

    model = ChatbotQuestion
    icon = "help"
    menu_label = "Domande ricevute"
    list_display = ["question", "how", "answered", "language", "source", "score", "created_at", "create_answer"]
    list_filter = ["answered", "kind", "in_context", "from_hint", "language"]
    search_fields = ["question"]


class ChatbotHintViewSet(SnippetViewSet):
    """Bubble text and questions for one page. Pages without an entry get
    them from their own content."""

    model = ChatbotHint
    icon = "help"
    menu_label = "Suggerimenti"
    list_display = ["path", "text_it", "active"]
    list_filter = ["active"]
    search_fields = ["path", "text_it"]


class ChatbotGroup(SnippetViewSetGroup):
    menu_label = "Chatbot"
    menu_icon = "comment"
    menu_order = 260
    items = (ChatbotEntryViewSet, ChatbotQuestionViewSet, ChatbotHintViewSet)

    def get_submenu_items(self):
        items = super().get_submenu_items()
        items.append(MenuItem("Prova il chatbot", reverse("chatbot_admin_test"), icon_name="search", order=900))
        items.append(MenuItem("Impostazioni", reverse("wagtailsettings:edit", args=["core", "chatbotsettings"]),
                              icon_name="cog", order=910))
        return items


register_snippet(ChatbotGroup)


@hooks.register("register_admin_urls")
def chatbot_admin_urls():
    from .admin_views import test_view

    return [path("chatbot/prova/", test_view, name="chatbot_admin_test")]
