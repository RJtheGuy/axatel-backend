

from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting

from .theme_utils import (
    RADIUS_PRESETS,
    SHADOW_PRESETS,
    TYPE_SCALE_RATIOS,
    generate_palette,
)

RADIUS_CHOICES = [(k, k.capitalize()) for k in RADIUS_PRESETS]
SHADOW_CHOICES = [(k, k.capitalize()) for k in SHADOW_PRESETS]
TYPE_SCALE_CHOICES = [(k, k.capitalize()) for k in TYPE_SCALE_RATIOS]

# Fields captured in a snapshot for the one-step undo. Explicit list
# (rather than "every field") so bookkeeping like `logo` or `previous_values`
# itself never gets clobbered by a restore - only what an editor can
# visibly change on the form.
_SNAPSHOT_FIELDS = [
    "primary_color", "background_color", "accent_color", "text_color",
    "heading_font", "body_font", "base_font_size",
    "radius_preset", "shadow_preset", "type_scale_preset",
]


@register_setting(icon="view")
class ThemeSettings(BaseSiteSetting):
    """One row per site, edited like Navigation/Footer/Chatbot under
    Impostazioni. See module docstring for why this replaced the
    earlier multi-theme snippet."""

    primary_color = models.CharField(max_length=7, default="#C52317", verbose_name="Colore primario")
    background_color = models.CharField(max_length=7, default="#020712", verbose_name="Colore sfondo")
    accent_color = models.CharField(max_length=7, default="#EA3F30", verbose_name="Colore accento")
    text_color = models.CharField(max_length=7, default="#F2F8FF", verbose_name="Colore testo")

    heading_font = models.CharField(max_length=120, default="Montserrat, sans-serif", verbose_name="Font titoli")
    body_font = models.CharField(max_length=120, default="Montserrat, sans-serif", verbose_name="Font testo")
    base_font_size = models.PositiveSmallIntegerField(default=16, verbose_name="Dimensione font base (px)")

    radius_preset = models.CharField(max_length=10, choices=RADIUS_CHOICES, default="round", verbose_name="Raggio bordi")
    shadow_preset = models.CharField(max_length=10, choices=SHADOW_CHOICES, default="lifted", verbose_name="Ombra")
    type_scale_preset = models.CharField(max_length=12, choices=TYPE_SCALE_CHOICES, default="standard", verbose_name="Scala tipografica")

    logo = models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
        verbose_name="Logo",
    )

    # One-step undo. Never shown on the panel - only touched by save()
    # below and read by restore_previous(). Deliberately one slot, not
    # a history list: insurance against a mis-click, not version control.
    previous_values = models.JSONField(null=True, blank=True, editable=False)

    panels = [
        MultiFieldPanel([
            FieldPanel("primary_color"),
            FieldPanel("background_color"),
            FieldPanel("accent_color"),
            FieldPanel("text_color"),
        ], heading="Colori"),
        MultiFieldPanel([
            FieldPanel("heading_font"),
            FieldPanel("body_font"),
            FieldPanel("base_font_size"),
            FieldPanel("type_scale_preset"),
        ], heading="Tipografia"),
        MultiFieldPanel([
            FieldPanel("radius_preset"),
            FieldPanel("shadow_preset"),
            FieldPanel("logo"),
        ], heading="Forma"),
    ]

    class Meta:
        verbose_name = "Tema"

    def save(self, *args, **kwargs):
        """Snapshot pre-save values so restore_previous() has something
        to go back to - only when an existing row changes, not on first
        creation, where "previous" is meaningless."""
        if self.pk:
            try:
                current = ThemeSettings.objects.get(pk=self.pk)
                self.previous_values = {f: getattr(current, f) for f in _SNAPSHOT_FIELDS}
            except ThemeSettings.DoesNotExist:
                pass
        super().save(*args, **kwargs)

    def restore_previous(self) -> bool:
        """Swap in the last snapshot, if there is one. Returns False
        with nothing changed if there's no snapshot yet (e.g. right
        after the very first save)."""
        if not self.previous_values:
            return False
        snapshot = self.previous_values
        for field in _SNAPSHOT_FIELDS:
            if field in snapshot:
                setattr(self, field, snapshot[field])
        # Don't let the restore itself become "the previous state" -
        # otherwise Undo/Undo would just ping-pong forever.
        self.previous_values = None
        super(ThemeSettings, self).save(update_fields=_SNAPSHOT_FIELDS + ["previous_values"])
        return True

    @property
    def type_scale(self) -> dict:
        """h1..h6 computed from base_font_size * ratio^n - see the note
        in theme_utils.py."""
        ratio = TYPE_SCALE_RATIOS[self.type_scale_preset]
        base = self.base_font_size
        return {
            "h6": round(base / ratio, 1),
            "h5": round(base, 1),
            "h4": round(base * ratio, 1),
            "h3": round(base * ratio ** 2, 1),
            "h2": round(base * ratio ** 3, 1),
            "h1": round(base * ratio ** 4, 1),
        }

    @property
    def api_representation(self) -> dict:
        """Same shape the frontend has always expected from
        theme_views.DEFAULT_THEME."""
        palette = generate_palette(self.primary_color, self.background_color)
        return {
            "name": "Tema attivo",
            "primary_color": self.primary_color,
            "accent_color": self.accent_color,
            "text_color": self.text_color,
            "background_color": self.background_color,
            **palette,
            "heading_font": self.heading_font,
            "body_font": self.body_font,
            "base_font_size": self.base_font_size,
            "type_scale": self.type_scale,
            "radius": RADIUS_PRESETS[self.radius_preset],
            "shadow": SHADOW_PRESETS[self.shadow_preset],
            "logo_url": self.logo.get_rendition("original").full_url if self.logo else None,
            "can_restore_previous": bool(self.previous_values),
        }