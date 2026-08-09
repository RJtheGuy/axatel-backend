from rest_framework.fields import Field
from wagtail.documents.blocks import DocumentChooserBlock as BaseDocumentChooserBlock
from wagtail.images.blocks import ImageChooserBlock as BaseImageChooserBlock
from wagtail.blocks import PageChooserBlock as BasePageChooserBlock


# ── StreamField block representations ────────────────────────────────
# Used inside StreamField bodies (hero.background_image, image.image, …)

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
    """
    Wagtail's default PageChooserBlock.get_api_representation() returns
    a bare integer page ID - useless to a headless frontend without a
    second request per page (or N+1 requests for a ListBlock of them,
    as in ServiceCardsBlock.services). Returns real page data instead,
    same shape/reasoning as ImageChooserBlock/DocumentChooserBlock
    above: one consistent shape a Vue component can render directly.

    Uses `.url` (relative, site-root-relative), NOT `.full_url` - the
    OPPOSITE choice from Image/DocumentChooserBlock above, on purpose.
    Those are fetched directly by the browser as separate HTTP requests
    and need the absolute Django host or they resolve against the
    wrong origin (see the note in core/blocks_shared.py about embedded
    rich-text images). A page reference is different: it's consumed by
    NuxtLink for client-side routing WITHIN the Nuxt app, which expects
    a relative path matching its own [...slug].vue catch-all route. An
    absolute URL here would make NuxtLink treat every service card as
    an external link, forcing a full page reload instead of an SPA
    navigation - correct-looking but quietly worse UX, not a crash, so
    easy to ship without noticing.

    Only core Page fields (id, title, url) - no assumption about what
    fields the chosen page type (e.g. services.ServicePage) actually
    has beyond what every Page guarantees.
    """
    def get_api_representation(self, value, context=None):
        if not value:
            return None
        return {
            "id": value.id,
            "title": value.title,
            "url": value.url,
        }


# ── Model-field serializers ──────────────────────────────────────────
# For plain model fields exposed via APIField(), NOT StreamField blocks.
# Wagtail's defaults for these produce a different shape than the block
# representations above; keeping them identical means one Vue component
# handles an image whether it came from a StreamField block or a
# ForeignKey on the page model.

class ImageAPIField(Field):
    """
    Serializes a ForeignKey('wagtailimages.Image') to the same shape as
    ImageChooserBlock.get_api_representation above.

    Usage:
        api_fields = [APIField("cover_image", serializer=ImageAPIField())]
    """

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
    """
    Flattens a ClusterTaggableManager to a plain list of tag names.
    Without this, DRF cannot serialize the manager and the field either
    errors or leaks internal taggit structure.

    Usage:
        api_fields = [APIField("tags", serializer=TagListField())]
    """

    def to_representation(self, value):
        return [tag.name for tag in value.all()]