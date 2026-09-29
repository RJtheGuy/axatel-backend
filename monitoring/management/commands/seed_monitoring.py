"""
Move the "Cosa monitoriamo?" topics (aria, fiumi, frane, traffico, …) into
the CMS with the text they have on the site today, so they become editable
and translatable. URL stays /monitoraggio/<slug>/.

    python manage.py seed_monitoring --images /var/www/axatel-frontend/app/assets/immagini
    python manage.py seed_monitoring --dry-run

Run `seed_products` first so the product links are filled in.

Only ADDS: a topic whose slug already exists under Monitoraggio is left
untouched. "Coming soon" topics (alberi, gallerie) are not created: the
site keeps showing its placeholder until someone writes the page in the
CMS. Until a topic exists here, the site shows its built-in version.
"""
import html
import json
import uuid

from django.core.management.base import BaseCommand

from home.models import HomePage
from monitoring.models import MonitoringIndexPage, MonitoringPage
from monitoring.monitoring_defaults import DEFAULT_TOPICS
from products.management.commands.seed_products import DEFAULT_IMAGES, import_image
from products.models import ProductPage


def block(block_type, value):
    return {"type": block_type, "value": value, "id": str(uuid.uuid4())}


class Command(BaseCommand):
    help = "Import the built-in Monitoraggio topics into the CMS (adds only)."

    def add_arguments(self, parser):
        parser.add_argument("--images", default=DEFAULT_IMAGES, help="Folder with the topic pictures.")
        parser.add_argument("--dry-run", action="store_true")

    def body_for(self, data):
        body = []
        feature = data.get("feature")
        if feature:
            slug = data.get("feature_product")
            product = ProductPage.objects.live().filter(slug=slug).first() if slug else None
            body.append(block("product_feature", {
                "label": feature.get("label", ""), "name": feature.get("name", ""),
                "description": feature.get("description", ""),
                "product": product.id if product else None,
                "link_url": feature.get("href", "") or "", "link_label": feature.get("hrefLabel", "") or "",
            }))
        for section in data["sections"]:
            text = "".join(f"<p>{html.escape(p)}</p>" for p in section.get("paragraphs", []))
            body.append(block("text_section", {
                "heading": section["title"], "text": text,
                "highlights": [block("item", h) for h in section.get("highlights") or []],
            }))
        return body

    def handle(self, *args, images=DEFAULT_IMAGES, dry_run=False, **options):
        home = HomePage.objects.filter(locale__language_code="it").first() or HomePage.objects.first()
        if home is None:
            self.stderr.write("No HomePage found.")
            return

        index = MonitoringIndexPage.objects.child_of(home).first()
        if index is None:
            self.stdout.write("+ index page 'Monitoraggio' (/monitoraggio/)")
            if not dry_run:
                index = home.add_child(instance=MonitoringIndexPage(title="Cosa monitoriamo", slug="monitoraggio"))
                index.save_revision().publish()

        created = 0
        for data in DEFAULT_TOPICS:
            if data["status"] != "published":
                self.stdout.write(f"- {data['slug']} is 'coming soon' on the site, not created")
                continue
            if index is not None and MonitoringPage.objects.child_of(index).filter(slug=data["slug"]).exists():
                self.stdout.write(f"= {data['slug']} already in the CMS, left as it is")
                continue
            self.stdout.write(f"+ '{data['title']}' (/monitoraggio/{data['slug']}/)")
            created += 1
            if dry_run:
                continue
            image = data["image"]
            page = MonitoringPage(
                title=data["title"], slug=data["slug"], category=data["group"],
                short_description=data["introduction"][:300],
                cover_image=import_image(images, image, image.rsplit(".", 1)[0]) if image else None,
                body=json.dumps(self.body_for(data)),
            )
            index.add_child(instance=page)
            page.save_revision().publish()

        verb = "would be created" if dry_run else "created"
        self.stdout.write(self.style.SUCCESS(f"{created} topic(s) {verb}."))
