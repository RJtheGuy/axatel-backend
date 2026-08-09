"""
core/blocks_shared.py

Constants shared between blocks.py and blocks_sections.py. Lives in its
own module, imported by both, on purpose: blocks.py already imports
FROM blocks_sections.py (for SolutionCardsBlock, TestimonialBlock, etc.),
so if blocks_sections.py also imported these constants directly from
blocks.py, the two files would import each other - a circular import
that fails at Django startup with "partially initialized module".
A third, dependency-free module breaks that cycle.
"""

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
    """
    expand_db_html() resolves image/document embeds using each file's
    MEDIA_URL-relative path (e.g. src="/media/images/foo.png") - correct
    when the site serving pages is the same origin serving media, wrong
    here since the Nuxt frontend runs on a different origin
    (localhost:3000 in dev) than Django (localhost:8001 / the real
    domain in production). A relative src resolves against the
    FRONTEND's own origin, which doesn't serve /media/ at all - and
    worse, Nuxt's catch-all page route then treats that path as an
    unmatched page slug and 404s the whole page, not just the image.

    Same fix ImageAPIField in api_blocks.py already applies via
    `rendition.full_url` instead of `.url` - this does the equivalent
    for embeds resolved through expand_db_html(), which has no
    absolute-URL option of its own to pass in.

    WAGTAILADMIN_BASE_URL is the standard Wagtail setting for exactly
    this (also what full_url uses internally) - if it isn't set,
    embedded media/document URLs are left relative rather than
    guessing, so a misconfiguration is visible (broken image) instead
    of silently pointing at the wrong host.
    """
    base = getattr(settings, "WAGTAILADMIN_BASE_URL", None)
    if not base:
        return html
    return re.sub(r'(src|href)="(/media/|/documents/)', rf'\1="{base}\2', html)


class ExpandedRichTextBlock(blocks.RichTextBlock):
    def get_api_representation(self, value, context=None):
        if not value:
            return None
        return _absolutize_media_urls(expand_db_html(value.source))