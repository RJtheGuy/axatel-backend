from rest_framework.fields import Field
from wagtail.documents.blocks import DocumentChooserBlock as BaseDocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock as BaseImageChooserBlock
from wagtail.blocks import PageChooserBlock as BasePageChooserBlock
from wagtail.rich_text import expand_db_html
from core.blocks_shared import _absolutize_media_urls

class ImageChooserBlock(BaseImageChooserBlock):
    def get_api_representation(self, value, context=None):
        if not value:
            return None
        rendition = value.get_rendition("original")
        return {
            "id": value.id,
            "title": value.title,
            "url": rendition.full_url,
            "alt": getattr(value, "default_alt_text", None) or value.title,
            "width": rendition.width,
            "height": rendition.height,
        }


class DocumentChooserBlock(BaseDocumentChooserBlock):
    def get_api_representation(self, value, context=None):
        if not value:
            return None
        return {
            "id": value.id,
            "title": value.title,
            "url": value.full_url,
        }

class PageChooserBlock(BasePageChooserBlock):

    def get_api_representation(self, value, context=None):
        if not value:
            return None
        return {
            "id": value.id,
            "title": value.title,
            "url": value.url,
        }

class ImageAPIField(Field):

    def to_representation(self, value):
        if not value:
            return None
        rendition = value.get_rendition("original")
        return {
            "id": value.id,
            "title": value.title,
            "url": rendition.full_url,
            "alt": getattr(value, "default_alt_text", None) or value.title,
            "width": rendition.width,
            "height": rendition.height,
        }


class TagListField(Field):
    def to_representation(self, value):
        return [tag.name for tag in value.all()]

class RichTextAPIField(Field):
    def to_representation(self, value):
        if not value:
            return ""
        return _absolutize_media_urls(expand_db_html(value))