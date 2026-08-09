"""
Seed the success cases from the old hardcoded index.vue array.

    python manage.py seed_casi

Idempotent: matches existing pages by slug and updates them in place
rather than creating duplicates, so it's safe to re-run. Pass --dry-run
to see what it would do without writing.

Creates the CasiIndexPage parent automatically if it doesn't exist yet.

Pages are created as DRAFTS unless --publish is passed. Drafts are not
returned by the Wagtail API, so the frontend will keep showing its
fallback content until they're published.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from casi.casi_data import CASI
from casi.models import CasiIndexPage, CasoSuccessoPage


class Command(BaseCommand):
    help = "Seed casi di successo from casi/casi_data.py"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show what would happen without writing to the database.",
        )
        parser.add_argument(
            "--publish", action="store_true",
            help="Publish immediately instead of leaving pages as drafts.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        publish = options["publish"]

        index = self._get_or_create_index(dry_run)

        created = updated = 0

        for entry in CASI:
            slug = entry.get("slug") or slugify(entry["title"])

            # On a dry run the index may not exist yet, so there is
            # nothing to look under — report everything as a create.
            existing = (
                CasoSuccessoPage.objects.child_of(index).filter(slug=slug).first()
                if index is not None else None
            )

            if dry_run:
                self.stdout.write(f"  [{'UPDATE' if existing else 'CREATE'}] {slug}")
                continue

            with transaction.atomic():
                if existing:
                    page = existing
                    self._apply(page, entry)
                    page.save()
                    updated += 1
                    verb, style = "updated", self.style.WARNING
                else:
                    page = CasoSuccessoPage(title=entry["title"], slug=slug, live=False)
                    self._apply(page, entry)
                    index.add_child(instance=page)
                    created += 1
                    verb, style = "created", self.style.SUCCESS

                # Tags need the page to have a PK first.
                # NOTE: taggit's set() takes ONE iterable, not *args.
                if entry.get("tags"):
                    page.tags.set(entry["tags"])
                    page.save()

                revision = page.save_revision()
                if publish:
                    revision.publish()

                self.stdout.write(style(f"  {verb}  {slug}"))

        if dry_run:
            self.stdout.write(self.style.NOTICE("\nDry run — nothing written."))
            return

        state = "published" if publish else "drafts"
        self.stdout.write(self.style.SUCCESS(
            f"\nDone: {created} created, {updated} updated ({state}).\n"
            f"Cover images are NOT set — upload them in the Wagtail admin "
            f"and attach to each case (paths listed in casi/casi_data.py)."
        ))

    def _get_or_create_index(self, dry_run):
        index = CasiIndexPage.objects.first()
        if index:
            return index

        # Needs a HomePage to hang off, per CasiIndexPage.parent_page_types
        from home.models import HomePage
        home = HomePage.objects.first()
        if home is None:
            raise CommandError(
                "No HomePage found. Create the site's home page in the "
                "Wagtail admin before seeding."
            )

        if dry_run:
            self.stdout.write("  [CREATE] CasiIndexPage 'Casi di successo' (/casi/)")
            return None

        index = CasiIndexPage(title="Casi di successo", slug="casi", live=True)
        home.add_child(instance=index)
        index.save_revision().publish()
        self.stdout.write(self.style.SUCCESS("  created  CasiIndexPage at /casi/"))
        return index

    @staticmethod
    def _apply(page, entry):
        page.title = entry["title"]
        page.client = entry.get("client", "")
        page.category = entry.get("category", "")
        page.description = entry.get("description", "")
        page.body = entry.get("body", "")