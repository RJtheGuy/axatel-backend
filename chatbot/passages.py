"""
The text of the published pages, cut into short passages, so the chatbot
can answer with what a page actually says and not only with its short
description ("Che sensori usate per le frane?", "Quanto dura la batteria
di Angel River?").

A passage is a paragraph or two under the same heading (at most ~600
characters), from:
  - the page's own text fields (introduction, description, tagline…),
  - the content blocks (text, sections, columns, steps, measures, stats,
    product features…), read generically so new block types are included,
  - the technical specifications of a product.

Blocks that only point elsewhere (cards of other pages, calls to action,
contact form, pictures, videos, logos) are skipped, and so are sentences
repeated on many pages (boilerplate).

Every passage belongs to the Italian page it comes from (translations are
mapped to it), so "tell me more" after an English answer continues with the
same page. Read-only and cheap (database only): the engine embeds the
passages and keeps the vectors in the database (ChatbotVector).
"""
from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass

LANGS = ("it", "en", "fr")

# Kinds of page that the chatbot answers about (site_knowledge.py), and the
# fields that hold their text, in reading order.
PAGE_MODELS = {
    "monitoring.MonitoringPage": ("short_description",),
    "solutions.SolutionPage": ("short_description",),
    "products.ProductPage": ("tagline",),
    "casi.CasoSuccessoPage": ("description", "body"),
    "services.ServicePage": ("short_description",),
    "home.InfoPage": ("introduction",),
}
STREAM_FIELDS = ("intro", "body", "specs")

# Blocks that show other pages, buttons or media: not this page's own words.
SKIP_BLOCKS = {
    "cta", "contact_form", "spacer", "image", "video_embed", "download", "partner_logos",
    "page_cards", "case_cards", "device_cards", "service_cards", "solution_cards",
    "portfolio_grid", "network_diagram", "testimonial", "faq",
}
# Keys inside blocks that never hold readable text.
SKIP_KEYS = {
    "url", "link", "links", "href", "image", "images", "photo", "video", "icon", "style", "variant",
    "layout", "color", "colour", "background", "anchor", "id", "page", "pages", "embed", "alt",
    "size", "align", "alignment", "theme", "document", "file", "logo", "logos", "source", "width",
    "height", "position", "target", "button", "buttons", "button_text", "button_label", "cta",
    "cta_text", "cta_label", "slug", "value_type", "show", "visible", "options", "block_options",
}
HEADING_KEYS = {"heading", "title", "eyebrow", "label", "name", "subtitle", "kicker", "caption"}

MAX_CHARS = 600
TARGET_CHARS = 320
MIN_CHARS = 40


@dataclass
class Passage:
    id: str          # short stable id (text hash), sent back by the chat as "already shown"
    page_id: int     # the Italian page
    language: str
    order: int       # position in the page
    heading: str
    text: str

    @property
    def search_text(self) -> str:
        """What is embedded: the heading gives the paragraph its subject."""
        return f"{self.heading}. {self.text}" if self.heading else self.text


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(str(text or "")))
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _from_html(value: str, out: list):
    """Rich text: headings and paragraphs / list items, in order."""
    for match in re.finditer(r"<(h[1-6]|p|li)\b[^>]*>(.*?)</\1>", value, flags=re.S | re.I):
        text = _clean(match.group(2))
        if text:
            tag = match.group(1).lower()
            out.append(("h" if tag.startswith("h") else "li" if tag == "li" else "p", text))
    if not out and _clean(value):
        out.append(("p", _clean(value)))


def _looks_like_text(value: str) -> bool:
    value = value.strip()
    if not value or value.startswith(("http://", "https://", "/", "#", "mailto:", "tel:")):
        return False
    return bool(re.search(r"[^\W\d_]{3,}", value))


def _walk(value, key, out: list):
    if isinstance(value, dict):
        block_type = value.get("type") if "value" in value else None
        if block_type is not None:
            if block_type in SKIP_BLOCKS:
                return
            _walk(value["value"], block_type, out)
            return
        # A product specification: "Connettività: LoRaWAN".
        if set(value) >= {"label", "value"} and all(isinstance(value[k], str) for k in ("label", "value")):
            label, text = _clean(value["label"]), _clean(value["value"])
            if label and text:
                out.append(("spec", f"{label}: {text}"))
            return
        for name, item in value.items():
            if name in SKIP_KEYS or name.endswith(("_url", "_link", "_image", "_id")):
                continue
            _walk(item, name, out)
    elif isinstance(value, list):
        for item in value:
            _walk(item, key, out)
    elif isinstance(value, str):
        if not _looks_like_text(value):
            return
        if "<" in value and ">" in value:
            _from_html(value, out)
        elif key in HEADING_KEYS and len(value) <= 120:
            out.append(("h", _clean(value)))
        elif len(value) >= MIN_CHARS or key in ("text", "description", "body", "content", "value"):
            out.append(("p", _clean(value)))


def _split_long(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    parts, current = [], ""
    for sentence in re.split(r"(?<=[.!?;])\s+", text):
        if current and len(current) + len(sentence) + 1 > MAX_CHARS:
            parts.append(current)
            current = ""
        current = f"{current} {sentence}".strip()
        while len(current) > MAX_CHARS:  # one huge sentence
            parts.append(current[:MAX_CHARS].rsplit(" ", 1)[0])
            current = current[len(parts[-1]):].strip()
    if current:
        parts.append(current)
    return parts


def items_of(page) -> list:
    """(kind, text) in reading order: kind is h (heading), p (paragraph) or spec."""
    out: list = []
    fields = PAGE_MODELS.get(f"{page._meta.app_label}.{page.__class__.__name__}", ())
    for name in fields:
        value = getattr(page, name, "")
        if isinstance(value, str) and value.strip():
            if "<" in value and ">" in value:
                _from_html(value, out)
            else:
                out.append(("p", _clean(value)))
    for name in STREAM_FIELDS:
        stream = getattr(page, name, None)
        raw = getattr(stream, "raw_data", None)
        if raw is not None:
            before = len(out)
            _walk(list(raw), name, out)
            if name == "specs" and len(out) > before:
                out.insert(before, ("h", "Specifiche tecniche"))
    return out


def passages_of(page, page_id: int, language: str) -> list[Passage]:
    """The page's text as passages of about one or two paragraphs."""
    passages: list[tuple[str, str]] = []
    heading, buffer, specs = "", [], []

    def flush_text():
        text = " ".join(buffer).strip()
        buffer.clear()
        passages.extend((heading, part) for part in _split_long(text) if len(part) >= MIN_CHARS)

    def flush_specs():
        chunk = []
        for spec in specs + [None]:
            if spec is None or (chunk and len("; ".join(chunk + [spec])) > MAX_CHARS):
                if chunk:
                    passages.append((heading, "; ".join(chunk) + "."))
                chunk = []
            if spec is not None:
                chunk.append(spec)
        specs.clear()

    bullets: list[str] = []

    def flush_bullets():
        # Short list items read as one sentence: "Movimenti del terreno, reti
        # paramassi, automazioni di emergenza."; long ones as paragraphs.
        if bullets:
            if sum(len(b) for b in bullets) / len(bullets) <= 60:
                joined = ", ".join([bullets[0]] + [b[:1].lower() + b[1:] if not b[:2].isupper() else b for b in bullets[1:]])
                buffer.append(joined.rstrip(".;:") + ".")
            else:
                buffer.extend(bullets)
            bullets.clear()

    for kind, text in items_of(page):
        if kind == "li":
            bullets.append(text.rstrip(";,"))
            continue
        flush_bullets()
        if kind == "h":
            flush_text()
            flush_specs()
            heading = "" if text.lower() == (page.title or "").strip().lower() else text
        elif kind == "spec":
            specs.append(text)
        else:
            buffer.append(text)
            if sum(len(b) for b in buffer) >= TARGET_CHARS:
                flush_text()
    flush_bullets()
    flush_text()
    flush_specs()

    result, seen = [], set()
    for order, (head, text) in enumerate(passages):
        if text.lower() in seen:
            continue
        seen.add(text.lower())
        digest = hashlib.sha1(f"{page_id}|{language}|{text}".encode()).hexdigest()[:10]
        result.append(Passage(digest, page_id, language, order, head, text))
    return result


def _italian_original(page, cache: dict):
    """The Italian page a translation belongs to (itself when Italian)."""
    from wagtail.models import Page

    if page.locale.language_code == "it":
        return page.pk
    key = page.translation_key
    if key not in cache:
        cache[key] = Page.objects.filter(translation_key=key, locale__language_code="it").values_list("pk", flat=True).first()
    return cache[key]


def build() -> list[Passage]:
    """Every passage of every published page the chatbot answers about."""
    from django.apps import apps

    passages: list[Passage] = []
    originals: dict = {}
    for label in PAGE_MODELS:
        try:
            model = apps.get_model(label)
        except LookupError:
            continue
        pages = model.objects.live().filter(locale__language_code__in=LANGS).select_related("locale").order_by("path")
        for page in pages:
            if getattr(page, "alias_of_id", None):
                continue
            original = _italian_original(page, originals)
            if original is None:
                continue
            passages += passages_of(page, original, page.locale.language_code)

    # A sentence found on three or more pages is boilerplate, not an answer.
    pages_by_text: dict = {}
    for passage in passages:
        pages_by_text.setdefault(passage.text.lower(), set()).add(passage.page_id)
    return [p for p in passages if len(pages_by_text[p.text.lower()]) < 3]


def signature():
    """Same as site_knowledge.signature(): changes on publish / unpublish."""
    from .site_knowledge import signature as site_signature

    return site_signature()
