from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import ChatbotHint, ChatbotQuestion


class ChatbotQuestionViewSet(SnippetViewSet):
    """What visitors asked. Filter "Risposto: No" to see the questions the
    bot could not answer, then add them to a Voce chatbot."""

    model = ChatbotQuestion
    icon = "help"
    menu_label = "Domande al chatbot"
    list_display = ["question", "language", "answered", "from_hint", "entry", "source", "score", "created_at"]
    list_filter = ["answered", "from_hint", "language"]
    search_fields = ["question"]
    add_to_admin_menu = False


register_snippet(ChatbotQuestionViewSet)


class ChatbotHintViewSet(SnippetViewSet):
    """Snippets → Suggerimenti del chatbot: bubble text and questions for
    one page. Pages without an entry get them from their own content."""

    model = ChatbotHint
    icon = "help"
    menu_label = "Suggerimenti del chatbot"
    list_display = ["path", "text_it", "active"]
    list_filter = ["active"]
    search_fields = ["path", "text_it"]
    add_to_admin_menu = False


register_snippet(ChatbotHintViewSet)
