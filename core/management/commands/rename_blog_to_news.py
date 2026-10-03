"""
One-off tidy-up of the CMS menu (Impostazioni → Navigazione) after the blog
became "News" at /news:

  - the "Blog" link is renamed News / News / Actualités and points to /news;
  - the old "News" placeholder link (/approfondimenti/news) is switched off
    with its "Visibile" switch (not deleted: switch it back on in the CMS
    if you ever need it).

    python manage.py rename_blog_to_news --dry-run
    python manage.py rename_blog_to_news

Safe to run more than once: a second run finds nothing to change. The old
addresses /blog/... and /approfondimenti/news keep working: the site
redirects them to /news.
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from core.site_settings import NavigationSettings

OLD_BLOG = {"/blog", "/blog/"}
OLD_NEWS = {"/approfondimenti/news", "/approfondimenti/news/"}


def _href(value: dict) -> str:
    page_id = value.get("page")
    if page_id:
        page = Page.objects.filter(pk=page_id).first()
        if page is not None:
            # Path of the page as the site shows it, e.g. "/blog/".
            parts = page.get_url_parts()
            return parts[2] if parts else ""
    return (value.get("custom_url") or "").strip()


class Command(BaseCommand):
    help = "Rename the Blog menu link to News (/news) and hide the old News placeholder link."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show the changes without saving.")

    def handle(self, *args, dry_run=False, **options):
        for site in Site.objects.all():
            nav = NavigationSettings.for_site(site)
            items = list(nav.items.get_prep_value()) if nav.items else []
            changes = []

            for item in items:
                for group in item["value"].get("groups", []):
                    for link in group["value"].get("links", []):
                        value = link["value"]
                        href = _href(value)
                        label = (value.get("label") or "").strip().lower()
                        if href in OLD_BLOG or (label == "blog" and not href.startswith("http")):
                            value.update({"label": "News", "label_en": "News", "label_fr": "Actualités",
                                          "page": None, "custom_url": "/news"})
                            changes.append(f"~ '{group['value'].get('label')}': Blog → News (/news)")
                        elif href in OLD_NEWS and value.get("visible", True) is not False:
                            value["visible"] = False
                            changes.append(f"~ '{group['value'].get('label')}': old News link ({href}) hidden")

            if not changes:
                self.stdout.write(self.style.SUCCESS(f"{site}: menu already up to date."))
                continue
            for line in changes:
                self.stdout.write(line)
            if dry_run:
                self.stdout.write(self.style.WARNING(f"Dry run: {len(changes)} change(s) NOT saved."))
                continue
            nav.items = items
            nav.save()
            self.stdout.write(self.style.SUCCESS(f"{site}: saved {len(changes)} change(s)."))
