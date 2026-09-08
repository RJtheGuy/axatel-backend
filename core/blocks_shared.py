SECTION_VARIANT_CHOICES = [
    ("default", "Predefinito"),
    ("accent", "Accento"),
    ("muted", "Attenuato"),
]


INLINE_TEXT_FEATURES = ["bold", "italic", "highlight", "link"]



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