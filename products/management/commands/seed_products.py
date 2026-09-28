"""
Create the product pages already presented on the site (Angel BPM, Angel
River, Geo Angel, Traffic Alert, Angel Road Site, Angel Bridge, Cerere
Pro Aria) under a "Prodotti" index page at /prodotti/.

    python manage.py seed_products --images /var/www/axatel-frontend/app/assets/immagini
    python manage.py seed_products --dry-run

Only ADDS: a product whose slug already exists is left untouched.
"""
import json
import os
import uuid

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from wagtail.images import get_image_model

from casi.models import CasoSuccessoPage
from home.models import HomePage
from products.models import ProductIndexPage, ProductPage
from products.product_defaults import DEFAULT_PRODUCTS

DEFAULT_IMAGES = "/var/www/axatel-frontend/app/assets/immagini"


def import_image(folder, filename, title):
    """Reuse an image with the same title, or upload it from the folder."""
    if not filename:
        return None
    Image = get_image_model()
    existing = Image.objects.filter(title=title).first()
    if existing:
        return existing
    path = os.path.join(folder, filename)
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as handle:
        return Image.objects.create(title=title, file=ImageFile(handle, name=filename))


class Command(BaseCommand):
    help = "Add the site's products to the CMS under /prodotti/ (adds only)."

    def add_arguments(self, parser):
        parser.add_argument("--images", default=DEFAULT_IMAGES, help="Folder with the product pictures.")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, images=DEFAULT_IMAGES, dry_run=False, **options):
        home = HomePage.objects.filter(locale__language_code="it").first() or HomePage.objects.first()
        if home is None:
            self.stderr.write("No HomePage found.")
            return

        index = ProductIndexPage.objects.child_of(home).first()
        if index is None:
            self.stdout.write("+ index page 'Prodotti' (/prodotti/)")
            if not dry_run:
                index = home.add_child(instance=ProductIndexPage(
                    title="Prodotti", slug="prodotti",
                    intro="Sistemi, sensori e piattaforme Axatel per il monitoraggio di infrastrutture, territorio e ambiente.",
                ))
                index.save_revision().publish()

        created = 0
        for data in DEFAULT_PRODUCTS:
            if index is not None and ProductPage.objects.child_of(index).filter(slug=data["slug"]).exists():
                self.stdout.write(f"= {data['slug']} already exists, left as it is")
                continue
            self.stdout.write(f"+ product '{data['title']}' (/prodotti/{data['slug']}/)")
            created += 1
            if dry_run:
                continue
            cases = [p for p in (CasoSuccessoPage.objects.live().filter(slug=s).first() for s in data["cases"]) if p]
            body = []
            if cases:
                body.append({
                    "type": "case_cards", "id": str(uuid.uuid4()),
                    "value": {"heading": "Casi di successo", "cases": [c.id for c in cases]},
                })
            page = ProductPage(
                title=data["title"], slug=data["slug"], category=data["category"],
                tagline=data["tagline"], datasheet_url=data["datasheet_url"],
                cover_image=import_image(images, data["image"], data["title"]),
                specs=json.dumps([
                    {"type": "spec", "id": str(uuid.uuid4()), "value": {"label": label, "value": value}}
                    for label, value in data["specs"]
                ]),
                body=json.dumps(body),
            )
            index.add_child(instance=page)
            page.save_revision().publish()

        verb = "would be created" if dry_run else "created"
        self.stdout.write(self.style.SUCCESS(f"{created} product(s) {verb}."))
