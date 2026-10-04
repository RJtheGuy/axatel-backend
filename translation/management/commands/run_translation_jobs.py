"""
Do the translations requested with the "Traduci" button in the CMS.
Run every minute by cron (deploy/translation.cron):

    python manage.py run_translation_jobs

Loads each model once per run, translates the waiting pages into draft
English/French versions and records the outcome on the request
(Impostazioni → Traduzioni richieste).
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from translation.engine import Translator
from translation.models import TranslationJob
from translation.pages import translate_page


class Command(BaseCommand):
    help = "Process waiting translation requests."

    def handle(self, *args, **options):
        jobs = list(TranslationJob.objects.filter(status="queued").select_related("page", "requested_by").order_by("created_at")[:20])
        if not jobs:
            return
        translators: dict[str, Translator] = {}
        for job in jobs:
            job.status = "running"
            job.save(update_fields=["status"])
            lines = []
            try:
                for language in [l for l in job.languages.split(",") if l]:
                    if language not in translators:
                        translators[language] = Translator(language)
                    lines.append(translate_page(job.page, language, translators[language], user=job.requested_by, publish=job.publish))
                job.status = "done"
            except Exception as error:  # noqa: BLE001 - recorded on the job for the editors
                lines.append(f"error: {error}")
                job.status = "failed"
            job.message = "\n".join(lines)
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "message", "finished_at"])
            self.stdout.write(f"{job.page.title}: {job.status}\n  " + "\n  ".join(lines))
