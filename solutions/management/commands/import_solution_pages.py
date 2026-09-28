"""
Move the 12 "Come lo realizziamo?" pages (angel-bpm, analitici, sensori, …)
into the CMS with the text they have on the site today, so they become
editable and translatable. URL stays /soluzioni/<slug>/.

    python manage.py import_solution_pages --images /var/www/axatel-frontend/app/assets/immagini
    python manage.py import_solution_pages --dry-run

Run `seed_products` first so the product links are filled in.

Only ADDS: a page whose slug already exists under Soluzioni is left
untouched. Until a page exists here, the site keeps showing its built-in
version, so nothing disappears during the move.
"""
import html
import json
import uuid

from django.core.management.base import BaseCommand

from home.models import HomePage
from products.management.commands.seed_products import DEFAULT_IMAGES, import_image
from products.models import ProductPage
from solutions.models import SolutionPage, SolutionsIndexPage
from solutions.solution_defaults import DEFAULT_SOLUTIONS


def block(block_type, value):
    return {"type": block_type, "value": value, "id": str(uuid.uuid4())}


class Command(BaseCommand):
    help = "Import the built-in Soluzioni pages into the CMS (adds only)."

    def add_arguments(self, parser):
        parser.add_argument("--images", default=DEFAULT_IMAGES, help="Folder with the page pictures.")
        parser.add_argument("--dry-run", action="store_true")

    def product(self, slug):
        return ProductPage.objects.live().filter(slug=slug).first() if slug else None

    def body_for(self, data):
        body = []
        feature = data.get("feature")
        if feature:
            product = self.product(data.get("feature_product"))
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
        devices = [p for p in (self.product(s) for s in data.get("devices", [])) if p]
        if devices:
            body.append(block("device_cards", {
                "heading": "Dispositivi", "products": [block("item", p.id) for p in devices],
            }))
        cta = data.get("cta")
        if cta:
            body.append(block("cta", {
                "heading": html.escape(cta["text"]), "body": "",
                "button_label": html.escape(cta["label"]), "button_url": cta["href"], "style": "primary",
            }))
        return body

    def handle(self, *args, images=DEFAULT_IMAGES, dry_run=False, **options):
        home = HomePage.objects.filter(locale__language_code="it").first() or HomePage.objects.first()
        if home is None:
            self.stderr.write("No HomePage found.")
            return

        index = SolutionsIndexPage.objects.child_of(home).first()
        if index is None:
            self.stdout.write("+ index page 'Soluzioni' (/soluzioni/)")
            if not dry_run:
                index = home.add_child(instance=SolutionsIndexPage(title="Soluzioni", slug="soluzioni"))
                index.save_revision().publish()

        created = 0
        for data in DEFAULT_SOLUTIONS:
            if index is not None and SolutionPage.objects.child_of(index).filter(slug=data["slug"]).exists():
                self.stdout.write(f"= {data['slug']} already in the CMS, left as it is")
                continue
            self.stdout.write(f"+ '{data['title']}' (/soluzioni/{data['slug']}/)")
            created += 1
            if dry_run:
                continue
            page = SolutionPage(
                title=data["title"], slug=data["slug"], group=data["group"], eyebrow=data["eyebrow"],
                short_description=data["introduction"],
                cover_image=import_image(images, data["image"], data["image"].rsplit(".", 1)[0]) if data["image"] else None,
                body=json.dumps(self.body_for(data)),
            )
            index.add_child(instance=page)
            page.save_revision().publish()

        verb = "would be created" if dry_run else "created"
        self.stdout.write(self.style.SUCCESS(f"{created} page(s) {verb}."))
