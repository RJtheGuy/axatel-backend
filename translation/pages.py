"""
Translate a whole Wagtail page (Italian) into its English / French version.

Every text the editors can see is translated: title, Google title and
description, text fields, every block (rich text keeps its links and bold),
and child items such as glossary terms. Images, links, page and product
choices, numbers and addresses are copied as they are. The page keeps the
same address (slug) as the Italian one.

The result is saved as a DRAFT of the English/French page: someone checks
it and presses Pubblica. Nothing is published automatically.
"""
import json
import re

from django.db import models
from wagtail import blocks
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Locale, Page

from . import text as T

# Field and block names that hold addresses, codes or settings, not prose.
SKIP_NAME = re.compile(
    r"(url|slug|link|code|icon|email|phone|tel|color|colour|anchor|style|class|key|path|embed|font|preset|"
    r"network|form_type|variant|alignment|layout|ratio|size|target|schema|mode)", re.I)
PAGE_TEXT_FIELDS = {"title", "seo_title", "search_description"}


class Collector:
    """First pass: what will be asked to the model (for one batch)."""

    def __init__(self):
        self.texts: list[str] = []

    def __call__(self, text: str) -> str:
        self.texts.append(text)
        return text


def _translate_string(value: str, fn, rich: bool) -> str:
    if not isinstance(value, str) or not T.needs_translation(value):
        return value
    if rich or T.looks_like_html(value):
        return T.html_replace(value, fn)
    return fn(value.strip()) if value.strip() == value else value.replace(value.strip(), fn(value.strip()))


def walk_block(block, raw, fn, name=""):
    """Translate a block's raw (JSON) value, following the block definition."""
    if raw is None:
        return raw
    if isinstance(block, blocks.StreamBlock):
        out = []
        for item in raw or []:
            if isinstance(item, dict) and item.get("type") in block.child_blocks:
                child = block.child_blocks[item["type"]]
                out.append({**item, "value": walk_block(child, item.get("value"), fn, item["type"])})
            else:
                out.append(item)
        return out
    if isinstance(block, blocks.StructBlock):
        if not isinstance(raw, dict):
            return raw
        return {k: (walk_block(block.child_blocks[k], v, fn, k) if k in block.child_blocks else v) for k, v in raw.items()}
    if isinstance(block, blocks.ListBlock):
        out = []
        for item in raw or []:
            if isinstance(item, dict) and item.get("type") == "item" and "value" in item:
                out.append({**item, "value": walk_block(block.child_block, item["value"], fn, name)})
            else:
                out.append(walk_block(block.child_block, item, fn, name))
        return out
    if SKIP_NAME.search(name or ""):
        return raw
    if isinstance(block, blocks.RichTextBlock):
        return _translate_string(raw, fn, rich=True)
    if isinstance(block, (blocks.CharBlock, blocks.TextBlock)):
        return _translate_string(raw, fn, rich=False)
    return raw


def _text_fields(page):
    """(name, kind) of the page's translatable fields."""
    for field in page._meta.concrete_fields:
        name = field.name
        if field.model is Page or field.model.__name__ == "Page":
            if name in PAGE_TEXT_FIELDS:
                yield name, "text"
            continue
        if isinstance(field, StreamField):
            yield name, "stream"
        elif isinstance(field, RichTextField):
            yield name, "rich"
        elif isinstance(field, (models.CharField, models.TextField)):
            if (field.choices or not field.editable or SKIP_NAME.search(name)
                    or isinstance(field, (models.URLField, models.EmailField, models.SlugField))):
                continue
            yield name, "text"


def _child_relations(page):
    """ParentalKey children (e.g. glossary terms), as (accessor, model)."""
    from modelcluster.fields import ParentalKey
    for rel in page._meta.related_objects:
        if isinstance(rel.remote_field, ParentalKey) and rel.related_model is not None:
            yield rel.get_accessor_name(), rel.related_model, rel.remote_field.name


def translate_content(source, target, fn):
    """Copy every translatable value from source to target through fn."""
    for name, kind in _text_fields(source):
        value = getattr(source, name)
        if kind == "stream":
            field = source._meta.get_field(name)
            raw = json.loads(json.dumps(list(value.raw_data))) if value else []
            setattr(target, name, walk_block(field.stream_block, raw, fn))
        elif kind == "rich":
            setattr(target, name, _translate_string(value or "", fn, rich=True))
        else:
            setattr(target, name, _translate_string(value or "", fn, rich=False))
    target.draft_title = target.title

    for accessor, model, parent_field in _child_relations(source):
        children = []
        for child in getattr(source, accessor).all():
            data = {}
            for field in model._meta.concrete_fields:
                if field.primary_key or field.name == parent_field:
                    continue
                if isinstance(field, models.ForeignKey):
                    data[field.attname] = getattr(child, field.attname)
                    continue
                value = getattr(child, field.name)
                if (isinstance(field, (models.CharField, models.TextField)) and not field.choices
                        and not SKIP_NAME.search(field.name)
                        and not isinstance(field, (models.URLField, models.EmailField, models.SlugField))):
                    value = _translate_string(value or "", fn, rich=False)
                if field.name == "locale_id" or field.name == "locale":
                    continue
                data[field.name] = value
            children.append(model(**data))
        setattr(target, accessor, children)


def segments_for(page) -> list[str]:
    """Everything the model would be asked for this page (for counting)."""
    collector = Collector()
    translate_content(page.specific, _Sink(page.specific), collector)
    return collector.texts


class _Sink:
    """Throw-away target for the collecting pass."""

    def __init__(self, source):
        self._source = source

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)


def translate_page(page, language: str, translator, user=None, dry_run=False) -> str:
    """Create or update the draft translation of an Italian page. Returns a
    one-line report."""
    from wagtail.actions.convert_alias import ConvertAliasPageAction

    source = page.specific
    if source.locale.language_code != "it":
        return f"skipped: '{source.title}' is not an Italian page"
    if not source.live and source.get_latest_revision():
        source = source.get_latest_revision_as_object()
    locale = Locale.objects.filter(language_code=language).first()
    if locale is None:
        return f"skipped: language '{language}' is not set up in the CMS (Impostazioni → Lingue)"

    asked = segments_for(source)
    if dry_run:
        chars = sum(len(t) for t in asked)
        return f"would translate {len(asked)} text(s), {chars} characters"

    translator.translate(asked)  # one batch, fills the cache

    target = page.get_translation_or_none(locale)
    created = False
    if target is None:
        target = source.copy_for_translation(locale, copy_parents=True)
        created = True
    elif target.alias_of_id:
        ConvertAliasPageAction(target.specific, user=user).execute(skip_permission_checks=True)
        target = Page.objects.get(pk=target.pk)
    target = target.specific
    if not created and target.live and target.has_unpublished_changes:
        return f"skipped [{language}]: '{target.title}' has a draft waiting — publish or discard it first"

    translate_content(source, target, translator.one)
    revision = target.save_revision(user=user, log_action=True)
    state = "new draft page" if created else "draft saved"
    return f"[{language}] '{revision.as_object().title}' — {state}, review it and press Pubblica"
