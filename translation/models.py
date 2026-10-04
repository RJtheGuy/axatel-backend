from django.conf import settings
from django.db import models
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet

LANGUAGES = [("en", "Inglese"), ("fr", "Francese")]


class TranslationMemory(models.Model):
    """Every text the model has translated, with its translation. Re-runs only
    translate what changed. A row marked "Corretta a mano" always wins, so a
    correction made once is reused everywhere the same text appears."""

    source_hash = models.CharField(max_length=64, db_index=True, editable=False)
    language = models.CharField(max_length=5, choices=LANGUAGES, verbose_name="Lingua")
    source = models.TextField(verbose_name="Testo italiano")
    target = models.TextField(verbose_name="Traduzione")
    engine = models.CharField(max_length=80, blank=True, editable=False, verbose_name="Modello")
    edited = models.BooleanField(
        default=False, verbose_name="Corretta a mano",
        help_text="Spunta dopo aver corretto la traduzione: verrà usata sempre, anche nelle prossime traduzioni.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    panels = [FieldPanel("source", read_only=True), FieldPanel("target"), FieldPanel("edited")]

    class Meta:
        verbose_name = "Memoria di traduzione"
        verbose_name_plural = "Memoria di traduzione"
        constraints = [models.UniqueConstraint(fields=["source_hash", "language"], name="unique_tm_entry")]

    def __str__(self):
        return f"[{self.language}] {self.source[:60]}"


@register_snippet
class ProtectedTerm(models.Model):
    """Words the model must never translate (product and brand names)."""

    term = models.CharField(max_length=80, unique=True, verbose_name="Termine",
                            help_text="Esattamente come è scritto, es. 'Angel River', 'LoRaWAN'.")

    panels = [FieldPanel("term")]

    class Meta:
        verbose_name = "Termine da non tradurre"
        verbose_name_plural = "Termini da non tradurre"
        ordering = ["term"]

    def __str__(self):
        return self.term


class TranslationJob(models.Model):
    """A page waiting to be translated: created by the "Traduci" button in the
    CMS, done within a minute by `manage.py run_translation_jobs` (cron)."""

    STATUS = [("queued", "In coda"), ("running", "In corso"), ("done", "Fatta"), ("failed", "Errore")]

    page = models.ForeignKey("wagtailcore.Page", on_delete=models.CASCADE, related_name="+", verbose_name="Pagina")
    languages = models.CharField(max_length=20, default="en,fr", verbose_name="Lingue")
    status = models.CharField(max_length=10, choices=STATUS, default="queued", verbose_name="Stato")
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="+", verbose_name="Richiesta da")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Richiesta il")
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Finita il")
    message = models.TextField(blank=True, verbose_name="Esito")

    class Meta:
        verbose_name = "Traduzione richiesta"
        verbose_name_plural = "Traduzioni richieste"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.page.title} → {self.languages} ({self.get_status_display()})"
