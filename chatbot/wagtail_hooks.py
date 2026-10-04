from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import ChatbotQuestion


class ChatbotQuestionViewSet(SnippetViewSet):
    """What visitors asked. Filter "Risposto: No" to see the questions the
    bot could not answer, then add them to a Voce chatbot."""

    model = ChatbotQuestion
    icon = "help"
    menu_label = "Domande al chatbot"
    list_display = ["question", "language", "answered", "entry", "source", "score", "created_at"]
    list_filter = ["answered", "language"]
    search_fields = ["question"]
    add_to_admin_menu = False


register_snippet(ChatbotQuestionViewSet)
