"""
Impostazioni → Traduzione automatica: when an Italian page is published,
queue its English/French translation (done within a minute by the cron job
run_translation_jobs, outside the web server).
"""
import logging

logger = logging.getLogger(__name__)


def queue_translation(sender, instance, revision=None, **kwargs):
    from .models import TranslationJob, TranslationSettings

    try:
        page = instance
        if getattr(page, "locale", None) is None or page.locale.language_code != "it" or page.depth <= 1:
            return
        site = page.get_site()
        if site is None:
            return
        config = TranslationSettings.for_site(site)
        if not config.auto_translate:
            return
        if TranslationJob.objects.filter(page_id=page.id, status__in=["queued", "running"]).exists():
            return
        user = getattr(revision, "user", None) if revision is not None else None
        TranslationJob.objects.create(page_id=page.id, languages="en,fr", requested_by=user,
                                      publish=config.auto_publish)
    except Exception:  # never block a publish because of the translation queue
        logger.exception("Could not queue the automatic translation")
