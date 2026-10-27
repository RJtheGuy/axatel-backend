"""
Old addresses never end on "page not found" (update 57).

When a published page is unpublished or deleted in the CMS (one page, several
at once, or a whole section), a permanent redirect is added from its address
to the nearest published page above it: /prodotti/angel-bpm -> /prodotti.
It appears in Impostazioni -> Reindirizzamenti as an automatic redirect, where
an editor can point it somewhere better (e.g. the product that replaces it).

Nothing to undo when a page comes back: the site never redirects an address
that has a published page in the visitor's language (core/settings_views.py,
RedirectsView), so publishing the page again simply makes it show again.

One redirect row serves every language: the site adds /en or /fr in front of
both addresses, so the target is always the Italian (default language) page.
"""
import logging

from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from wagtail.models import Locale, Page
from wagtail.signals import page_unpublished

logger = logging.getLogger(__name__)


def page_address(page) -> str:
    """'/home-en/prodotti/angel-bpm/' -> '/prodotti/angel-bpm' (language prefix comes from the site)."""
    return "/" + (page.url_path or "").split("/", 2)[-1].rstrip("/")


def _later(page):
    """Remember the address and the pages above it now; add the redirect once
    the CMS action is saved (after a delete, the pages above that were removed
    with it are gone, so the redirect never points to a deleted page)."""
    if page.depth <= 2 or not page.first_published_at:
        return  # a home page, or a draft that was never online
    path = page_address(page)
    if path == "/":
        return
    above = list(Page.objects.filter(
        path__in=[page.path[:i] for i in range(Page.steplen * 2, len(page.path), Page.steplen)]
    ).order_by("-depth").values_list("id", flat=True))
    transaction.on_commit(lambda: add_redirect(path, above))


def add_redirect(path, above_ids):
    from wagtail.contrib.redirects.models import Redirect

    try:
        old_path = Redirect.normalise_path(path)
        if Redirect.objects.filter(old_path=old_path).exists():
            return None  # one made by hand (or earlier) wins
        default = Locale.get_default()
        target = None
        for page_id in above_ids:
            page = Page.objects.filter(id=page_id).first()
            if page is None:
                continue
            if page.locale_id != default.id:
                page = page.get_translation_or_none(default) or page
            if page.live:
                target = page
                break
        if target is None:
            return None
        return Redirect.objects.create(old_path=old_path, site=None, redirect_page=target,
                                       is_permanent=True, automatically_created=True)
    except Exception:  # noqa: BLE001 - never break the editor's action
        logger.exception("Automatic redirect for %s failed", path)
        return None


@receiver(page_unpublished)
def redirect_unpublished(sender, instance, **kwargs):
    _later(instance)


@receiver(pre_delete)
def redirect_deleted(sender, instance, **kwargs):
    # Wagtail always deletes through the base Page model; the rows of the
    # specific page types go with it and are skipped here (one redirect per page).
    if type(instance) is Page:
        _later(instance)
