from django.core.exceptions import ValidationError
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
    answer_en = models.TextField(
        blank=True, verbose_name="Risposta (EN)",
        help_text="Per chi visita il sito in inglese. Vuoto = risposta in italiano. "
                  "`manage.py translate_settings` la riempie con il modello di traduzione: rileggila.",
    )
    answer_fr = models.TextField(blank=True, verbose_name="Risposta (FR)")
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
        FieldPanel("answer_en"),
        FieldPanel("answer_fr"),
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

    def clean(self):
        super().clean()

        if not self.questions or not self.questions.strip():
            raise ValidationError({"questions": "Inserisci almeno una domanda valida."})

        if not self.answer or not self.answer.strip():
            raise ValidationError({"answer": "Inserisci una risposta valida."})

        if self.is_fallback:
            existing = ChatbotEntry.objects.filter(is_fallback=True).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    {"is_fallback": "Esiste già una risposta di riserva. Disattiva quella attuale prima di crearne un'altra."}
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        stripped = self.questions.strip()
        first_line = stripped.splitlines()[0] if stripped else "(nessuna domanda)"
        return f"{'[FALLBACK] ' if self.is_fallback else ''}{first_line}"

    @property
    def questions_list(self) -> list[str]:
        return [q.strip() for q in self.questions.splitlines() if q.strip()]
    def answer_in(self, language: str) -> str:
        """The answer in the visitor's language, Italian when not translated."""
        if language in ("en", "fr"):
            translated = (getattr(self, f"answer_{language}", "") or "").strip()
            if translated:
                return translated
        return self.answer


class ChatbotQuestion(models.Model):
    """What visitors asked and how the bot decided, to see what is missing
    from the answers (Snippets → Domande al chatbot). Only the question text
    is kept (no name, address or IP), for 180 days."""

    question = models.CharField(max_length=300, verbose_name="Domanda")
    language = models.CharField(max_length=5, default="it", verbose_name="Lingua")
    entry = models.ForeignKey(ChatbotEntry, null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="+", verbose_name="Risposta usata")
    source = models.CharField(max_length=200, blank=True, verbose_name="Risposta dal sito",
                              help_text="Pagina da cui è presa la risposta, quando non è una Voce chatbot.")
    score = models.FloatField(default=0, verbose_name="Somiglianza")
    margin = models.FloatField(default=0, verbose_name="Distacco dalla seconda")
    from_hint = models.BooleanField(default=False, verbose_name="Dalla nuvoletta",
                                    help_text="Domanda scelta nella nuvoletta di suggerimento della pagina.")
    answered = models.BooleanField(default=False, verbose_name="Risposto",
                                   help_text="No = è stata data la risposta di riserva.")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Quando")

    class Meta:
        verbose_name = "Domanda al chatbot"
        verbose_name_plural = "Domande al chatbot"
        ordering = ["-created_at"]

    def __str__(self):
        return self.question[:80]


class ChatbotHint(models.Model):
    """Snippets → Suggerimenti del chatbot: the bubble's text and questions
    for one page, instead of the ones made automatically from the page."""

    path = models.CharField(
        max_length=200, unique=True, verbose_name="Indirizzo della pagina",
        help_text="Come appare nel sito in italiano, es. /monitoraggio/frane (vale anche per /en e /fr).",
    )
    active = models.BooleanField(default=True, verbose_name="Attivo")
    text_it = models.CharField(max_length=160, verbose_name="Testo (IT)")
    text_en = models.CharField(max_length=160, blank=True, verbose_name="Testo (EN)")
    text_fr = models.CharField(max_length=160, blank=True, verbose_name="Testo (FR)")
    questions_it = models.TextField(
        blank=True, verbose_name="Domande proposte (IT)",
        help_text="Una per riga, al massimo 3. Scrivile come le scriverebbe un visitatore: il chatbot "
                  "risponde come se le avesse digitate. Vuoto = le domande automatiche della pagina.",
    )
    questions_en = models.TextField(blank=True, verbose_name="Domande proposte (EN)")
    questions_fr = models.TextField(blank=True, verbose_name="Domande proposte (FR)")

    panels = [
        FieldPanel("path"), FieldPanel("active"),
        FieldPanel("text_it"), FieldPanel("questions_it"),
        FieldPanel("text_en"), FieldPanel("questions_en"),
        FieldPanel("text_fr"), FieldPanel("questions_fr"),
    ]

    class Meta:
        verbose_name = "Suggerimento del chatbot"
        verbose_name_plural = "Suggerimenti del chatbot"
        ordering = ["path"]

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = "/" + self.path.strip().strip("/") if self.path.strip("/ ") else "/"
        super().save(*args, **kwargs)

    def text_in(self, language: str) -> str:
        return (getattr(self, f"text_{language}", "") or "").strip() or self.text_it

    def questions_in(self, language: str) -> list:
        raw = (getattr(self, f"questions_{language}", "") or "").strip() or (
            self.questions_it if language == "it" else "")
        return [line.strip() for line in raw.splitlines() if line.strip()][:3]
