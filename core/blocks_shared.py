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


def document_file_url(document) -> str:
    """Direct address of an uploaded document (PDF) under /media/, made
    absolute with SITE_URL like images are. The file is served by the web
    server itself, so it works whatever the frontend routes."""
    if not document or not getattr(document, "file", None):
        return ""
    url = document.file.url
    base = getattr(settings, "WAGTAILADMIN_BASE_URL", "") or ""
    if url.startswith("/") and base:
        url = base.rstrip("/") + url
    return url


class ExpandedRichTextBlock(blocks.RichTextBlock):
    def get_api_representation(self, value, context=None):
        if not value:
            return None
        return _absolutize_media_urls(expand_db_html(value.source))