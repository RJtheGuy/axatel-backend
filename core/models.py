# """
# core/models.py

# A theme is data, not code: a tenant can save several themes and activate
# one at a time - the "screenshot logic" of picking a look, coming back
# later, and switching. Colors/fonts/spacing an editor sets directly;
# everything else (status colors, structural neutrals, the heading size
# scale) is *derived*, so a theme stays internally consistent no matter
# what brand color someone enters.

# CHANGE: the colour defaults were Wagtail-scaffold values - white
# background, green primary, system-ui fonts - which do not match the live
# Axatel design at all. Creating a theme and activating it would have
# flipped the site from near-black to white. They now mirror the static
# :root block in nuxt.config.ts, so a freshly created theme renders the
# site exactly as it already looks and every change an editor makes is
# deliberate rather than a surprise.

# Fonts are a choice list rather than free text: a typo'd font stack fails
# silently to the next entry in the stack, and every option here should be
# a family the frontend actually loads.
# """

# from django.core.exceptions import ValidationError
# from django.db import models
# from wagtail.admin.panels import FieldPanel, MultiFieldPanel
# from wagtail.snippets.models import register_snippet

# from .theme_utils import (
#     RADIUS_PRESETS,
#     SHADOW_PRESETS,
#     TYPE_SCALE_RATIOS,
#     generate_palette,
# )

# # Only families the frontend actually loads. Adding one here means adding
# # the matching @font-face / <link> in the Nuxt app too - otherwise it
# # silently falls back to the next stack entry.
# FONT_CHOICES = [
#     ("Montserrat, sans-serif", "Montserrat"),
#     ("'Inter', sans-serif", "Inter"),
#     ("'Roboto', sans-serif", "Roboto"),
#     ("'IBM Plex Sans', sans-serif", "IBM Plex Sans"),
#     ("Georgia, serif", "Georgia (serif)"),
#     ("'JetBrains Mono', monospace", "JetBrains Mono"),
#     ("system-ui, sans-serif", "System default"),
# ]


# @register_snippet
# class SiteTheme(models.Model):
#     site = models.ForeignKey(
#         "wagtailcore.Site",
#         on_delete=models.CASCADE,
#         related_name="themes",
#         help_text="Which tenant this theme belongs to.",
#     )
#     name = models.CharField(
#         max_length=100, default="Default",
#         help_text="Editor-facing label, e.g. 'Holiday Sale', 'Autumn Campaign'.",
#     )
#     is_active = models.BooleanField(
#         default=False,
#         help_text="Only one theme per site can be active at a time.",
#     )
#     preview_screenshot = models.ForeignKey(
#         "wagtailimages.Image",
#         null=True, blank=True,
#         on_delete=models.SET_NULL, related_name="+",
#         help_text="Optional thumbnail shown in the theme gallery.",
#     )
#     logo = models.ForeignKey(
#         "wagtailimages.Image",
#         null=True, blank=True,
#         on_delete=models.SET_NULL, related_name="+",
#     )

#     # -- Editor-set base colors; everything else derives from these -----
#     # Defaults mirror nuxt.config.ts :root so a new theme is a visual
#     # no-op rather than a jarring palette swap.
#     primary_color = models.CharField(
#         max_length=7, default="#C52317",
#         help_text="Colore principale del brand.",
#     )
#     accent_color = models.CharField(
#         max_length=7, default="#EA3F30",
#         help_text="Colore di accento per link e pulsanti.",
#     )
#     text_color = models.CharField(
#         max_length=7, default="#F2F8FF",
#         help_text="Colore del testo principale.",
#     )
#     background_color = models.CharField(
#         max_length=7, default="#020712",
#         help_text="Sfondo del sito. I colori strutturali si adattano automaticamente.",
#     )

#     # -- Typography -----------------------------------------------------
#     heading_font = models.CharField(
#         max_length=150, choices=FONT_CHOICES, default="Montserrat, sans-serif",
#     )
#     body_font = models.CharField(
#         max_length=150, choices=FONT_CHOICES, default="Montserrat, sans-serif",
#     )
#     base_font_size = models.PositiveSmallIntegerField(
#         default=16, help_text="Base body text size in px. Headings scale from this.",
#     )
#     type_scale = models.CharField(
#         max_length=20,
#         choices=[(k, k.capitalize()) for k in TYPE_SCALE_RATIOS],
#         default="standard",
#     )

#     # -- Spacing / shape presets ---------------------------------------
#     radius_preset = models.CharField(
#         max_length=20,
#         choices=[(k, k.capitalize()) for k in RADIUS_PRESETS],
#         default="round",
#     )
#     shadow_preset = models.CharField(
#         max_length=20,
#         choices=[(k, k.capitalize()) for k in SHADOW_PRESETS],
#         default="lifted",
#     )

#     panels = [
#         MultiFieldPanel([
#             FieldPanel("name"),
#             FieldPanel("is_active"),
#             FieldPanel("preview_screenshot"),
#             FieldPanel("logo"),
#         ], heading="Generale"),
#         MultiFieldPanel([
#             FieldPanel("primary_color"),
#             FieldPanel("accent_color"),
#             FieldPanel("text_color"),
#             FieldPanel("background_color"),
#         ], heading="Colori"),
#         MultiFieldPanel([
#             FieldPanel("heading_font"),
#             FieldPanel("body_font"),
#             FieldPanel("base_font_size"),
#             FieldPanel("type_scale"),
#         ], heading="Tipografia"),
#         MultiFieldPanel([
#             FieldPanel("radius_preset"),
#             FieldPanel("shadow_preset"),
#         ], heading="Forme e ombre"),
#     ]

#     def clean(self):
#         if self.is_active:
#             conflict = SiteTheme.objects.filter(
#                 site=self.site, is_active=True
#             ).exclude(pk=self.pk)
#             if conflict.exists():
#                 # Deliberately a validation error, not a silent
#                 # auto-deactivate-the-other-one: an editor activating a
#                 # theme should see explicitly that it replaces the
#                 # current one, via the admin's "activate" action
#                 # (theme_views.ActivateThemeView) rather than a form
#                 # save doing it implicitly.
#                 raise ValidationError(
#                     "Another theme is already active for this site. "
#                     "Use 'Activate' from the theme list instead."
#                 )

#     def type_scale_sizes(self) -> dict:
#         """h1..h6 px sizes computed from base_font_size * ratio^n.
#         Not stored, so changing the ratio or base size recomputes every
#         heading size automatically with no migration."""
#         ratio = TYPE_SCALE_RATIOS[self.type_scale]
#         return {
#             f"h{6 - i}": round(self.base_font_size * (ratio ** (i + 1)), 1)
#             for i in range(6)
#         }

#     @property
#     def api_representation(self) -> dict:
#         """Single place that assembles editor-set + derived values."""
#         derived = generate_palette(self.primary_color, self.background_color)
#         return {
#             "id": self.pk,
#             "name": self.name,
#             "primary_color": self.primary_color,
#             "accent_color": self.accent_color,
#             "text_color": self.text_color,
#             "background_color": self.background_color,
#             **derived,
#             "heading_font": self.heading_font,
#             "body_font": self.body_font,
#             "base_font_size": self.base_font_size,
#             "type_scale": self.type_scale_sizes(),
#             "radius": RADIUS_PRESETS[self.radius_preset],
#             "shadow": SHADOW_PRESETS[self.shadow_preset],
#             "logo_url": self.logo.file.url if self.logo else None,
#         }

#     def __str__(self):
#         marker = " (active)" if self.is_active else ""
#         return f"{self.name} - {self.site}{marker}"

#     class Meta:
#         verbose_name = "Tema del sito"
#         constraints = [
#             models.UniqueConstraint(
#                 fields=["site"],
#                 condition=models.Q(is_active=True),
#                 name="one_active_theme_per_site",
#             ),
#         ]


# # Imported for the side effect: @register_setting only fires when the
# # module is imported, and nothing else imports site_settings. Without
# # this the Impostazioni panels never appear in the admin and
# # makemigrations reports "no changes detected".
# from .site_settings import (          # noqa: E402,F401
#     ChatbotSettings,
#     FooterSettings,
#     NavigationSettings,
# )


"""
core/models.py

ThemeSettings: site-wide theme (colors, fonts, shape) that a marketing
editor changes from the CMS, without touching CSS or code.

STEP 1 of the theme rollout replaces the earlier SiteTheme *snippet* (a
gallery of multiple saved themes with an activate/deactivate step) with
a single *setting*, following the exact same pattern as
NavigationSettings / FooterSettings / ChatbotSettings in
site_settings.py. Reasoning: Axatel runs one live look at a time, not a
library of interchangeable themes, so "one place, one form, Save = live"
is a better fit than a list-and-activate flow - one less concept for a
non-technical editor to learn.

The one thing the old gallery genuinely offered that this must not lose
is a safety net against a bad edit. Instead of keeping N saved themes
around for that, this keeps exactly ONE snapshot - the values right
before the last save - in `previous_values`, restorable with one call.
That's the smallest mechanism that solves "I didn't mean to do that,"
without asking anyone to manage a list.

Nothing downstream of this ever stores a color itself. `api_representation`
below is the one source of truth reaching the frontend; blocks and rich
text reference `var(--color-accent)` etc. by class name (see
core/wagtail_hooks.py). Change the setting once, every piece of content
that used "accent" updates with it.
"""

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