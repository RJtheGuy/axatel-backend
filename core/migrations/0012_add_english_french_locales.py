"""Create the English and French locales used by page translations.

Only adds rows. The existing Italian locale and every existing page are
untouched. Reversing removes the two locales only if nothing uses them.
"""
from django.db import migrations

NEW_LANGUAGES = ["en", "fr"]


def add_locales(apps, schema_editor):
    Locale = apps.get_model("wagtailcore", "Locale")
    for code in NEW_LANGUAGES:
        Locale.objects.get_or_create(language_code=code)


def remove_locales(apps, schema_editor):
    Locale = apps.get_model("wagtailcore", "Locale")
    Page = apps.get_model("wagtailcore", "Page")
    for locale in Locale.objects.filter(language_code__in=NEW_LANGUAGES):
        if not Page.objects.filter(locale=locale).exists():
            locale.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0011_menu_label_translations"),
        ("wagtailcore", "0054_initial_locale"),
    ]

    operations = [migrations.RunPython(add_locales, remove_locales)]
