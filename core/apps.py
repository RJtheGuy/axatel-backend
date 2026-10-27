from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        # Automatic redirects when a published page is unpublished or deleted (update 57).
        from . import auto_redirects  # noqa: F401
