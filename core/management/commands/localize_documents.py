"""
Bring the PDFs that the site still links on the old WordPress site
(www.axatel.it/wp-content/uploads/...pdf) into the CMS, so the new site no
longer depends on axatel.it.

    python manage.py localize_documents --dry-run
    python manage.py localize_documents
    python manage.py localize_documents --from-folder /tmp/pdf   # if the server cannot download

For every such PDF it:
  1. adds the file to Documenti (once; a document with the same title is reused),
  2. product pages: puts it in "Scheda tecnica (PDF)" and empties the external link,
  3. "Prodotto in evidenza" boxes: turns the old "Link alternativo" into a
     button in "Pulsanti" that opens the PDF from your own server,
then publishes the page again. A page with a draft waiting is left alone and
listed, so nobody's unpublished work goes online by surprise: publish or
discard the draft, then run the command again.

At the end it lists any other link to axatel.it still in pages (e-mail
addresses are not links and are left as they are), to fix by hand.
"""
import json
import os
import re
import urllib.request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from wagtail.documents import get_document_model
from wagtail.models import Page

PDF_URL = re.compile(r"https?://(?:www\.)?axatel\.it/wp-content/uploads/[^\s\"'<>]+?\.pdf", re.I)
ANY_URL = re.compile(r"https?://(?:www\.)?axatel\.it[^\s\"'<>]*", re.I)


def _pdf_url(value):
    value = (value or "").strip()
    return value if PDF_URL.fullmatch(value) else ""


class Command(BaseCommand):
    help = "Copy the PDFs linked on www.axatel.it into Documenti and point the pages to them."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Only show what would change.")
        parser.add_argument("--from-folder", default="", help="Folder with the PDFs already downloaded (same file names).")

    # -- documents ---------------------------------------------------------
    def document_for(self, url, folder, dry_run):
        Document = get_document_model()
        filename = url.rsplit("/", 1)[-1]
        title = os.path.splitext(filename)[0]
        if url in self.cache:
            return self.cache[url]
        doc = Document.objects.filter(title=title).first()
        if doc:
            self.stdout.write(f"= Documenti: '{title}' already there")
        elif dry_run:
            self.stdout.write(f"+ Documenti: '{title}' (from {url})")
            doc = "new"
        else:
            data = self.read(url, filename, folder)
            if data is None:
                self.cache[url] = None
                return None
            doc = Document(title=title)
            doc.file.save(filename, ContentFile(data), save=False)
            if hasattr(doc, "_set_document_file_metadata"):
                doc._set_document_file_metadata()
            doc.save()
            self.stdout.write(f"+ Documenti: '{title}' ({len(data) // 1024} KB)")
        self.cache[url] = doc
        return doc

    def read(self, url, filename, folder):
        data = None
        if folder:
            path = os.path.join(folder, filename)
            if os.path.exists(path):
                with open(path, "rb") as handle:
                    data = handle.read()
        if data is None:
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (axatel localize_documents)"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = response.read()
            except Exception as error:  # noqa: BLE001 - report and carry on with the others
                self.stderr.write(f"! could not download {url}: {error}. Put {filename} in a folder and use --from-folder.")
                self.problems += 1
                return None
        if not data.startswith(b"%PDF"):
            self.stderr.write(f"! {filename} is not a PDF file, skipped.")
            self.problems += 1
            return None
        return data

    # -- pages -------------------------------------------------------------
    def fix_body(self, page, folder, dry_run):
        """Turn 'Link alternativo' PDF links of Prodotto in evidenza boxes into buttons."""
        body = getattr(page, "body", None)
        if body is None or not hasattr(body, "raw_data"):
            return False, []
        raw = json.loads(json.dumps(list(body.raw_data)))
        changes = []
        for block in raw:
            if block.get("type") != "product_feature":
                continue
            value = block.get("value") or {}
            url = _pdf_url(value.get("link_url"))
            if not url:
                continue
            doc = self.document_for(url, folder, dry_run)
            if doc is None:
                continue
            label = (value.get("link_label") or "").strip() or "Scheda tecnica"
            changes.append(f"'{value.get('name', '')}': link → button '{label}'")
            if dry_run:
                continue
            button = {"label": label, "page": None, "document": doc.id, "url": "", "style": "secondary"}
            value["buttons"] = [{"type": "item", "value": button, "id": os.urandom(16).hex()}] + list(value.get("buttons") or [])
            value["link_url"] = ""
            value["link_label"] = ""
        if changes and not dry_run:
            page.body = raw
        return bool(changes), changes

    def fix_datasheet(self, page, folder, dry_run):
        url = _pdf_url(getattr(page, "datasheet_url", ""))
        if not url or getattr(page, "datasheet_id", None):
            return False, []
        doc = self.document_for(url, folder, dry_run)
        if doc is None:
            return False, []
        if not dry_run:
            page.datasheet = doc
            page.datasheet_url = ""
        return True, ["datasheet → Documenti"]

    def handle(self, *args, dry_run=False, from_folder="", **options):
        self.cache = {}
        self.problems = 0
        updated = 0
        waiting = []

        for page in Page.objects.all().specific().order_by("path"):
            if not (hasattr(page, "body") or hasattr(page, "datasheet_url")):
                continue
            source = page
            if page.has_unpublished_changes and page.live:
                # Check the draft too: if it also needs fixing, let a person decide.
                draft = page.get_latest_revision_as_object()
                if PDF_URL.search(self.page_text(page)) or PDF_URL.search(self.page_text(draft)):
                    waiting.append(page)
                continue
            if not page.live:
                source = page.get_latest_revision_as_object() if page.get_latest_revision() else page

            changed_body, notes = self.fix_body(source, from_folder, dry_run)
            changed_sheet, more = self.fix_datasheet(source, from_folder, dry_run)
            if not (changed_body or changed_sheet):
                continue
            where = page.url or page.title
            self.stdout.write(f"~ {where} [{page.locale.language_code}]: " + "; ".join(notes + more))
            updated += 1
            if dry_run:
                continue
            revision = source.save_revision(log_action=True)
            if page.live:
                revision.publish()

        for page in waiting:
            self.stdout.write(self.style.WARNING(
                f"! {page.url or page.title}: has a draft waiting. Publish or discard it in the CMS, then run this again."
            ))

        leftovers = []
        for page in Page.objects.live().specific().order_by("path"):
            found = sorted(set(ANY_URL.findall(self.page_text(page))))
            if found:
                leftovers.append((page, found))
        if leftovers and not dry_run:
            self.stdout.write("Still linking axatel.it (a PDF that failed above: run again with --from-folder; anything else: change it in the CMS if it should point here):")
            for page, found in leftovers:
                self.stdout.write(f"  {page.url or page.title}: " + ", ".join(found[:4]))

        verb = "would be updated" if dry_run else "updated"
        style = self.style.WARNING if self.problems else self.style.SUCCESS
        self.stdout.write(style(f"{updated} page(s) {verb}, {self.problems} problem(s)."))

    @staticmethod
    def page_text(page):
        parts = []
        for name in ("body", "specs"):
            value = getattr(page, name, None)
            if hasattr(value, "raw_data"):
                parts.append(json.dumps(list(value.raw_data)))
        parts.append(getattr(page, "datasheet_url", "") or "")
        return " ".join(parts)
