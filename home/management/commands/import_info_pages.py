"""
Move the Azienda pages (Chi siamo, Bilancio di sostenibilità, Invia il CV,
Diventa partner) and the Glossario into the CMS with the text they have on
the site today, so they become editable and translatable. URLs stay the
same: /azienda/<slug>/ and /approfondimenti/glossario/.

    python manage.py import_info_pages --images /var/www/axatel-frontend/app/assets/immagini
    python manage.py import_info_pages --dry-run

Only ADDS: a section or page whose slug already exists is left untouched.
Academy and News stay "coming soon" (News now lives at /news). The FAQ is
created as a DRAFT with questions answered from text already on the site:
review it in the CMS and press Pubblica to put it online. Until a page exists here, the site shows its
built-in version, so nothing disappears during the move.
"""
import html
import json
import uuid

from django.core.management.base import BaseCommand

from home.info_defaults import FAQ_DRAFT, GLOSSARY, PAGES, SECTIONS
from home.models import GlossaryPage, GlossaryTerm, HomePage, InfoIndexPage, InfoPage
from products.management.commands.seed_products import DEFAULT_IMAGES, import_image


def block(block_type, value):
    return {"type": block_type, "value": value, "id": str(uuid.uuid4())}


def body_for(data):
    body = []
    feature = data.get("feature")
    if feature:
        body.append(block("product_feature", {
            "label": feature.get("label", ""), "name": feature.get("name", ""),
            "description": feature.get("description", ""), "product": None,
            "link_url": feature.get("href", "") or "", "link_label": feature.get("hrefLabel", "") or "",
        }))
    for section in data.get("sections", []):
        text = "".join(f"<p>{html.escape(p)}</p>" for p in section.get("paragraphs", []))
        body.append(block("text_section", {
            "heading": section["title"], "text": text,
            "highlights": [block("item", h) for h in section.get("highlights") or []],
        }))
    cta = data.get("cta")
    if cta:
        body.append(block("cta", {
            "heading": html.escape(cta["text"]), "body": "",
            "button_label": html.escape(cta["label"]), "button_url": cta["href"], "style": "primary",
        }))
    return body


class Command(BaseCommand):
    help = "Import the built-in Azienda pages and the Glossario into the CMS (adds only)."

    def add_arguments(self, parser):
        parser.add_argument("--images", default=DEFAULT_IMAGES, help="Folder with the page pictures.")
        parser.add_argument("--dry-run", action="store_true")

    def section(self, home, slug, title, dry_run):
        index = InfoIndexPage.objects.child_of(home).filter(slug=slug).first()
        if index is None:
            self.stdout.write(f"+ section '{title}' (/{slug}/)")
            if not dry_run:
                index = home.add_child(instance=InfoIndexPage(title=title, slug=slug))
                index.save_revision().publish()
        return index

    def handle(self, *args, images=DEFAULT_IMAGES, dry_run=False, **options):
        home = HomePage.objects.filter(locale__language_code="it").first() or HomePage.objects.first()
        if home is None:
            self.stderr.write("No HomePage found.")
            return

        sections = {s["slug"]: self.section(home, s["slug"], s["title"], dry_run) for s in SECTIONS}
        created = 0

        for section_slug, pages in PAGES.items():
            index = sections.get(section_slug)
            for data in pages:
                where = f"/{section_slug}/{data['slug']}/"
                if data["status"] != "published":
                    self.stdout.write(f"- {where} is 'coming soon' on the site, not created")
                    continue
                if index is not None and index.get_children().filter(slug=data["slug"]).exists():
                    self.stdout.write(f"= {where} already in the CMS, left as it is")
                    continue
                self.stdout.write(f"+ '{data['title']}' ({where})")
                created += 1
                if dry_run:
                    continue
                image = data.get("image") or ""
                page = InfoPage(
                    title=data["title"], slug=data["slug"], eyebrow=data.get("eyebrow", ""),
                    introduction=data.get("introduction", "")[:400],
                    cover_image=import_image(images, image, data.get("image_alt") or data["title"]) if image else None,
                    body=json.dumps(body_for(data)),
                )
                index.add_child(instance=page)
                page.save_revision().publish()

        index = sections.get("approfondimenti")
        where = f"/approfondimenti/{GLOSSARY['slug']}/"
        if index is not None and index.get_children().filter(slug=GLOSSARY["slug"]).exists():
            self.stdout.write(f"= {where} already in the CMS, left as it is")
        else:
            self.stdout.write(f"+ '{GLOSSARY['title']}' ({where}, {len(GLOSSARY['terms'])} terms)")
            created += 1
            if not dry_run:
                page = GlossaryPage(
                    title=GLOSSARY["title"], slug=GLOSSARY["slug"],
                    eyebrow=GLOSSARY["eyebrow"], introduction=GLOSSARY["introduction"],
                )
                page.terms = [
                    GlossaryTerm(term=t["term"], definition=t["definition"], aliases=", ".join(t.get("aliases") or []), sort_order=i)
                    for i, t in enumerate(GLOSSARY["terms"])
                ]
                index.add_child(instance=page)
                page.save_revision().publish()

        # A starter FAQ, saved as a draft: it goes live only when someone
        # reviews it in the CMS and presses Pubblica.
        where = f"/approfondimenti/{FAQ_DRAFT['slug']}/"
        if index is not None and index.get_children().filter(slug=FAQ_DRAFT["slug"]).exists():
            self.stdout.write(f"= {where} already in the CMS, left as it is")
        else:
            self.stdout.write(f"+ 'FAQ' ({where}) as a DRAFT with {len(FAQ_DRAFT['items'])} questions: review it, then Pubblica")
            created += 1
            if not dry_run:
                faq = block("faq", {
                    "heading": "Domande frequenti",
                    "items": [{"question": q, "answer": f"<p>{html.escape(a)}</p>"} for q, a in FAQ_DRAFT["items"]],
                })
                page = InfoPage(
                    title=FAQ_DRAFT["title"], slug=FAQ_DRAFT["slug"], eyebrow=FAQ_DRAFT["eyebrow"],
                    introduction=FAQ_DRAFT["introduction"], body=json.dumps([faq]), live=False,
                )
                index.add_child(instance=page)
                page.save_revision()

        verb = "would be created" if dry_run else "created"
        self.stdout.write(self.style.SUCCESS(f"{created} page(s) {verb}."))
