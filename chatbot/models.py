"""
chatbot/models.py

ChatbotEntry: makes the chatbot's actual knowledge - the Q&A pairs that
used to be the hardcoded KNOWLEDGE_BASE list in engine.py - editable
from the CMS instead of requiring a developer to edit Python and
redeploy. ChatbotSettings (core/site_settings.py) already covers the
widget's presentation (title, welcome message, placeholder, suggested
chips); this covers what it actually knows how to answer.

A Wagtail Snippet, not a Page: entries have no URL and no place in the
page tree - closer in shape to the theme system before it was
simplified to a single settings row. Unlike the theme, there ARE meant
to be many of these (the original KNOWLEDGE_BASE had ~20 entries), so
this stays a real list of rows rather than folding into one settings
object.

`questions` is a plain multi-line text field - one phrasing per line -
rather than a StreamField of CharBlocks. A list of short strings
doesn't need StreamField's block-editing machinery; "type one question
per line, one per language if you want both" is a simpler instruction
for a non-technical editor than "add a block, type, repeat."

`answer` stays plain text on purpose, not rich text: chatbot/views.py
sends it straight into the chat widget as a JSON string
(`{"response": answer}`), not rendered as HTML - rich text here would
mean either stripping tags before sending or teaching the chat widget
to render HTML, neither of which the current widget does.
"""

from django.db import models
from django.db.models import Q
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class ChatbotEntry(models.Model):
    questions = models.TextField(
        verbose_name="Domande",
        help_text="Una domanda o un modo di chiederla per riga. Più righe "
                   "aumentano le probabilità che il chatbot la riconosca "
                   "(es. una versione in italiano e una in inglese).",
    )
    answer = models.TextField(
        verbose_name="Risposta",
        help_text="La risposta che il chatbot invia quando riconosce una "
                   "di queste domande. Solo testo semplice, senza formattazione.",
    )
    is_fallback = models.BooleanField(
        default=False,
        verbose_name="Risposta di riserva",
        help_text="Attiva SOLO su una voce: la risposta usata quando nessuna "
                   "domanda corrisponde abbastanza bene alle altre voci. "
                   "Se provi ad attivarla su una seconda voce, il salvataggio "
                   "darà errore - disattivala prima sull'altra.",
    )
    # Read by ChatbotEngine to detect edits without a restart - see the
    # comment above ChatbotEngine._ensure_loaded() in engine.py.
    updated_at = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel("questions"),
        FieldPanel("answer"),
        FieldPanel("is_fallback"),
    ]

    class Meta:
        verbose_name = "Voce chatbot"
        verbose_name_plural = "Voci chatbot"
        constraints = [
            models.UniqueConstraint(
                fields=["is_fallback"],
                condition=Q(is_fallback=True),
                name="unique_chatbot_fallback",
            ),
        ]

    def __str__(self):
        stripped = self.questions.strip()
        first_line = stripped.splitlines()[0] if stripped else "(nessuna domanda)"
        return f"{'[FALLBACK] ' if self.is_fallback else ''}{first_line}"

    @property
    def questions_list(self) -> list[str]:
        """One entry per non-empty line - what ChatbotEngine actually
        indexes. Blank lines (easy to leave in a Textarea) are dropped
        rather than becoming an empty-string "question" that could
        never realistically match anything."""
        return [q.strip() for q in self.questions.splitlines() if q.strip()]