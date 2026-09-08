
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
        return [q.strip() for q in self.questions.splitlines() if q.strip()]