"""
Update 73: the product categories become Marco's list.

The old values ("sistemi", "sensori", "piattaforme", "comunicazione") are no
longer valid choices, and Wagtail refuses to save or publish a page holding
one. This converts them, on the live pages (every language) and in their saved
revisions, so existing products keep working:

  - products from the original seed get a first suggested category (by slug);
  - every other product gets no category ("" = choose it in the CMS).

Values that are already new categories are left alone. Nothing else changes.
The new fields come in the next migration (`manage.py makemigrations products`).
"""
import json

from django.db import migrations

NEW_KEYS = {"lavoratori", "idrogeologico", "ambiente", "strutturale", "predittiva",
            "stradale", "lorawan", "master-slave", "edili"}

SUGGESTED_BY_SLUG = {
    "angel-river": "idrogeologico",
    "geo-angel": "idrogeologico",
    "traffic-alert": "stradale",
    "angel-road-site": "lavoratori",
    "angel-bridge": "strutturale",
    "cerere-pro-aria": "ambiente",
}


def converted(value, slug):
    if value in NEW_KEYS:
        return value
    return SUGGESTED_BY_SLUG.get(slug or "", "")


def forwards(apps, schema_editor):
    ProductPage = apps.get_model("products", "ProductPage")
    for page in ProductPage.objects.exclude(category__in=NEW_KEYS).only("pk", "slug", "category"):
        # update(), not save(): save() would re-validate the old value and fail
        ProductPage.objects.filter(pk=page.pk).update(category=converted(page.category, page.slug))

    try:
        Revision = apps.get_model("wagtailcore", "Revision")
        ContentType = apps.get_model("contenttypes", "ContentType")
    except LookupError:
        return
    ct = ContentType.objects.filter(app_label="products", model="productpage").first()
    if not ct:
        return
    for rev in Revision.objects.filter(content_type=ct).only("pk", "content").iterator():
        content = rev.content
        if isinstance(content, str):            # very old Wagtail stored it as text
            content = json.loads(content)
        if not isinstance(content, dict) or content.get("category") in NEW_KEYS:
            continue
        content["category"] = converted(content.get("category"), content.get("slug"))
        Revision.objects.filter(pk=rev.pk).update(content=content)


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0015_alter_productpage_body"),
        ("wagtailcore", "0070_rename_pagerevision_revision"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        # Going back leaves the converted values: the old choices come back,
        # and the products can be given an old category again in the CMS.
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
