"""
Import WordPress XML export into Wagtail pages.

USAGE:
  # 1. Export from WordPress: WP Admin → Tools → Export → All content → Download
  # 2. Dry run first (nothing written to DB):
       python manage.py import_wordpress wordpress.xml --dry-run
  # 3. Real import:
       python manage.py import_wordpress wordpress.xml

WHAT IT IMPORTS:
  - WordPress 'post'  → BlogPost  (under the BlogIndexPage)
  - WordPress 'page'  → FlexPage  (under the HomePage)

WHAT IT PRESERVES:
  - Title
  - Slug  (= your URL — critical for SEO)
  - Body content (as a paragraph block inside StreamField)
  - Excerpt (→ intro / meta description)
  - Published / draft status
"""

import xml.etree.ElementTree as ET
from html import unescape

from django.core.management.base import BaseCommand, CommandError

from home.models import FlexPage, HomePage
from blog.models import BlogIndexPage, BlogPost
from services.models import ServicesIndexPage


WP_NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp":      "http://wordpress.org/export/1.2/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}


def make_paragraph_streamfield(html_content):
    """
    Wrap raw HTML in a paragraph block for the StreamField JSON structure.
    Wagtail StreamField stores blocks as JSON; this is the minimal valid format.
    """
    import json, uuid
    return json.dumps([{
        "type": "paragraph",
        "id": str(uuid.uuid4()),
        "value": html_content,
    }])


class Command(BaseCommand):
    help = "Import pages and posts from a WordPress XML export"

    def add_arguments(self, parser):
        parser.add_argument("xml_file", type=str)
        parser.add_argument("--dry-run", action="store_true",
                            help="Preview what would be imported without writing anything")

    def handle(self, *args, **options):
        xml_path = options["xml_file"]
        dry_run  = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing will be saved\n"))

        # Parse XML
        try:
            tree = ET.parse(xml_path)
        except FileNotFoundError:
            raise CommandError(f"File not found: {xml_path}")
        except ET.ParseError as e:
            raise CommandError(f"XML parse error: {e}")

        items = tree.getroot().find("channel").findall("item")
        self.stdout.write(f"Found {len(items)} items in export\n")

        home_page  = HomePage.objects.first()
        blog_index = BlogIndexPage.objects.first()

        if not home_page:
            raise CommandError(
                "No HomePage found. Run migrations and set up a Wagtail site first."
            )

        imported = skipped = 0

        for item in items:
            post_type = item.findtext("wp:post_type", namespaces=WP_NS)
            status    = item.findtext("wp:status",    namespaces=WP_NS)

            # Only import published pages/posts (add "draft" here if you want drafts)
            if post_type not in ("post", "page") or status not in ("publish", "draft"):
                skipped += 1
                continue

            title   = item.findtext("title", "") or "Untitled"
            slug    = item.findtext("wp:post_name", namespaces=WP_NS) or ""
            content = unescape(item.findtext("content:encoded", namespaces=WP_NS) or "")
            excerpt = unescape(item.findtext("excerpt:encoded", namespaces=WP_NS) or "")
            is_live = (status == "publish")

            if dry_run:
                self.stdout.write(f"  [{post_type:5s}] {title[:60]!r}  slug={slug!r}  live={is_live}")
                imported += 1
                continue

            # ── WordPress post → BlogPost ──────────────────────────────────────
            if post_type == "post":
                if not blog_index:
                    self.stdout.write(self.style.WARNING(
                        f"  SKIP '{title}' — no BlogIndexPage in DB"
                    ))
                    skipped += 1
                    continue
                if BlogPost.objects.filter(slug=slug).exists():
                    self.stdout.write(f"  EXISTS (post): {slug}")
                    skipped += 1
                    continue

                post = BlogPost(
                    title=title,
                    slug=slug,
                    intro=excerpt[:400],
                    body=make_paragraph_streamfield(content),
                    live=is_live,
                )
                blog_index.add_child(instance=post)
                self.stdout.write(self.style.SUCCESS(f"  ✓ Post: {title}"))
                imported += 1

            # ── WordPress page → FlexPage ──────────────────────────────────────
            elif post_type == "page":
                if FlexPage.objects.filter(slug=slug).exists():
                    self.stdout.write(f"  EXISTS (page): {slug}")
                    skipped += 1
                    continue

                page = FlexPage(
                    title=title,
                    slug=slug,
                    body=make_paragraph_streamfield(content),
                    live=is_live,
                )
                home_page.add_child(instance=page)
                self.stdout.write(self.style.SUCCESS(f"  ✓ Page: {title}"))
                imported += 1

        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"DRY RUN complete. Would import: {imported}  Would skip: {skipped}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Import complete. Imported: {imported}  Skipped: {skipped}"
            ))
