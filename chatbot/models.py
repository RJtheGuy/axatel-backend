from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


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
    page = models.ForeignKey(
        "wagtailcore.Page", null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        verbose_name="Pagina collegata",
        help_text="Facoltativa. Sotto la risposta compare \"Scopri di più\" verso questa pagina, e "
                  "\"Dimmi di più\" continua con il testo della pagina.",
    )
    follow_ups = models.TextField(
        blank=True, verbose_name="Domande successive proposte",
        help_text="Facoltative, una per riga (al massimo 3): compaiono come pulsanti sotto la risposta, "
                  "e il chatbot risponde come se il visitatore le avesse scritte. Es. \"Quanto costa?\"",
    )
    active = models.BooleanField(
        default=True, verbose_name="Attiva",
        help_text="Spegni per non usare più questa risposta senza cancellarla.",
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
        FieldPanel("answer_en"),
        FieldPanel("answer_fr"),
        MultiFieldPanel([FieldPanel("page"), FieldPanel("follow_ups")], heading="Dopo la risposta"),
        FieldPanel("active"),
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

    @property
    def follow_up_list(self) -> list[str]:
        return [q.strip() for q in (self.follow_ups or "").splitlines() if q.strip()][:3]

    def answer_in(self, language: str) -> str:
        """The answer in the visitor's language, Italian when not translated."""
        if language in ("en", "fr"):
            translated = (getattr(self, f"answer_{language}", "") or "").strip()
            if translated:
                return translated
        return self.answer


class ChatbotQuestion(models.Model):
    """What visitors asked and how the bot decided, to see what is missing
    from the answers (Chatbot → Domande ricevute). Only the question text
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
    kind = models.CharField(max_length=20, blank=True, choices=[
        ("entry", "Voce chatbot"), ("page", "Pagina del sito"), ("passage", "Testo di una pagina"),
        ("context", "Seguito della conversazione"), ("more", "Dimmi di più"), ("clarify", "Domanda di chiarimento"),
        ("fallback", "Nessuna risposta"), ("greeting", "Saluto"), ("thanks", "Ringraziamento"),
        ("unclear", "Domanda non chiara"),
    ], verbose_name="Come ha risposto")
    answer_key = models.CharField(max_length=60, blank=True, verbose_name="Chiave risposta")
    in_context = models.BooleanField(default=False, verbose_name="Durante una conversazione",
                                     help_text="Sì = c'era già una domanda prima, il chatbot ne ha tenuto conto.")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Quando")

    class Meta:
        verbose_name = "Domanda ricevuta"
        verbose_name_plural = "Domande ricevute"
        ordering = ["-created_at"]

    def __str__(self):
        return self.question[:80]

    def create_answer(self):
        """ "Crea risposta" in the list: a new Voce chatbot with this question."""
        from urllib.parse import quote

        from django.urls import reverse
        from django.utils.html import format_html

        if self.answered and self.kind != "clarify":
            return ""
        url = reverse("wagtailsnippets_chatbot_chatbotentry:add") + "?domanda=" + quote(self.question)
        return format_html('<a class="button button-small button-secondary" href="{}">Crea risposta</a>', url)

    create_answer.short_description = "Azione"

    def how(self):
        if self.kind:
            label = self.get_kind_display()
            return f"{label} (in conversazione)" if self.in_context and self.kind not in ("more", "context") else label
        return self.source or ("Voce chatbot" if self.entry_id else "")

    how.short_description = "Come ha risposto"


class ChatbotHint(models.Model):
    """Chatbot → Suggerimenti: the bubble's text and questions
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


class ChatbotVector(models.Model):
    """The language model's numbers for one text (question or page passage),
    kept so that a restart does not have to compute them all again.
    Technical: not shown in the CMS, rebuilt automatically when missing."""

    key = models.CharField(max_length=40, unique=True)  # sha1 of model name + text
    vector = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Vettore chatbot"
