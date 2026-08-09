"""
core/theme_utils.py

Derives a full semantic color palette from the two colors an editor
actually picks (primary, background). Editors choose a brand color; they
don't hand-pick "success green" or "border gray" — those are computed so
every theme stays internally consistent and accessible, regardless of
what brand color someone enters.

Semantic status colors (success/warning/danger) are NOT hue-shifted from
the brand color — users expect green=success, amber=warning, red=danger
regardless of brand. Only their saturation/lightness are nudged to sit
comfortably with the rest of the palette. Surface/border/muted, which are
neutral/structural rather than semantic, ARE derived from the background
color's lightness so they always sit correctly against it.
"""

import colorsys


def _hex_to_hls(hex_color: str) -> tuple[float, float, float]:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def _hls_to_hex(h: float, l: float, s: float) -> str:
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, l)), s)
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


def generate_palette(primary_color: str, background_color: str) -> dict:
    """Given the two colors an editor actually chooses, derive the rest
    of the semantic palette. Returns hex strings ready to serialize."""
    bg_h, bg_l, bg_s = _hex_to_hls(background_color)
    is_dark_bg = bg_l < 0.5

    return {
        # Fixed semantic hues (green/amber/red), lightness nudged to sit
        # well against whichever background this theme uses.
        "success_color": _hls_to_hex(0.36, 0.35 if is_dark_bg else 0.42, 0.55),
        "warning_color": _hls_to_hex(0.11, 0.45 if is_dark_bg else 0.55, 0.85),
        "danger_color": _hls_to_hex(0.0, 0.40 if is_dark_bg else 0.50, 0.65),
        # Structural neutrals, derived from the background's own
        # lightness so they always read correctly against it.
        "surface_color": _hls_to_hex(bg_h, bg_l + (0.06 if is_dark_bg else -0.03), bg_s),
        "border_color": _hls_to_hex(bg_h, bg_l + (0.15 if is_dark_bg else -0.10), bg_s),
        "muted_color": _hls_to_hex(bg_h, bg_l + (0.35 if is_dark_bg else -0.30), max(bg_s - 0.1, 0)),
    }


# Named presets an editor picks from — deliberately not raw px inputs,
# so a non-technical editor chooses a *feel* ("soft") rather than typing
# numbers. Frontend maps these keys to actual CSS values in one place
# (frontend/src/theme/presets.js), keeping the vocabulary here as the
# single source of truth for what preset names exist.
RADIUS_PRESETS = {"flat": "0px", "soft": "8px", "sharp": "2px", "round": "16px"}
SHADOW_PRESETS = {
    "none": "none",
    "soft": "0 2px 8px rgba(0,0,0,0.08)",
    "sharp": "0 1px 2px rgba(0,0,0,0.25)",
    "lifted": "0 8px 24px rgba(0,0,0,0.15)",
}

# Modular type scale ratios, named for editors rather than exposing raw
# multipliers. h1..h6 sizes are computed from base_font_size * ratio^n
# at read time (see SiteTheme.type_scale below) rather than stored, so
# changing the ratio recomputes every heading size automatically.
TYPE_SCALE_RATIOS = {
    "compact": 1.125,
    "standard": 1.25,
    "expressive": 1.333,
    "dramatic": 1.5,
}