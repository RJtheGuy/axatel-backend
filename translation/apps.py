from django.apps import AppConfig


class TranslationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "translation"
    verbose_name = "Traduzioni automatiche"

    def ready(self):
        from wagtail.signals import page_published

        from .signals import queue_translation

        page_published.connect(queue_translation, dispatch_uid="translation-auto-queue")
