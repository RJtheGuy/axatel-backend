# Shared choice list for every block that gets a "variant" field (Hero,
# Testimonial, Stats).
SECTION_VARIANT_CHOICES = [
    ("default", "Predefinito"),
    ("accent", "Accento"),
    ("muted", "Attenuato"),
]

# Shared feature set for inline body-ish text fields that are NOT the
# main Testo block - quotes, card descriptions, CTA copy. Deliberately
# smaller than the main RichTextBlock's features in blocks.py: no
# headings or lists, since these are short embedded snippets, not
# standalone articles.
INLINE_TEXT_FEATURES = ["bold", "italic", "highlight", "link"]


# ── Rich text that can contain embedded images/docs ──────────────────
# Wagtail's default RichTextBlock.get_api_representation() returns the
# RAW database HTML - image embeds are stored as
# `<embed embedtype="image" id="10" .../>` placeholders, not real <img>
# tags. That's fine for Wagtail's own server-rendered templates (the
# `richtext` filter expands placeholders at render time) but the
# headless API was returning that raw placeholder verbatim. `<embed>`
# is an actual reserved browser tag (historically for plugins) - an
# unrecognized embed renders nothing, so any image inserted into a rich
# text field vanished on the frontend even though it was clearly there
# in the CMS.
#
# expand_db_html() is the exact function Wagtail's own `richtext`
# template filter calls internally - reusing it here at the API layer
# means the frontend receives real, already-resolved <img> tags and
# needs no changes of its own.
import re

from django.conf import settings
from wagtail import blocks
from wagtail.rich_text import expand_db_html


def _absolutize_media_urls(html: str) -> str:

    base = getattr(settings, "WAGTAILADMIN_BASE_URL", None)
    if not base:
        return html
    return re.sub(r'(src|href)="(/media/|/documents/)', rf'\1="{base}\2', html)


class ExpandedRichTextBlock(blocks.RichTextBlock):
    def get_api_representation(self, value, context=None):
        if not value:
            return None
        return _absolutize_media_urls(expand_db_html(value.source))