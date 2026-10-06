"""
Bring the pictures (and the "Conosci Axatel" text) of the old WordPress site
www.axatel.it into the new CMS, without touching anything already uploaded.

Run it on the server (it can reach www.axatel.it; nothing else is needed, no
migration). Every step is opt-in; without options it only reports.

    manage.py import_old_site_images
        Report: each success story and product of the new site, whether it
        has a picture, the old page it matches and that page's picture;
        plus the text of the old "Conosci Axatel" page.

    manage.py import_old_site_images --download
        Also saves the pictures in media/old-site/ and a zip of them, to
        download in the browser at /media/old-site/old-site-images.zip
        (then upload by hand in Immagini). Remove it afterwards with
        --clean-download.

    manage.py import_old_site_images --import
        Adds the pictures to the CMS image library, collection
        "Sito precedente", titled after the page they belong to. Pages are
        not changed: pick the picture in each page's "Immagine di copertina".
        A picture already in the library (same file) is not added twice.

    manage.py import_old_site_images --attach
        As --import, and also sets the picture as "Immagine di copertina" on
        the pages that have NO picture yet, and publishes that change.
        Pages with a picture, or with unpublished changes (a draft someone
        is working on), are left alone and listed.

    Documents (PDF datasheets, catalogues…): the report lists every file of
    the old site (its media library, else the files linked from its pages).
    --download puts them in the zip too; --import / --attach copy them into
    Documenti (collection "Sito precedente"). For every picture and document
    copied, a redirect is added from its old address (/wp-content/uploads/…)
    to the copy, so links to the old files keep working after the domain
    moves to the new site (unless a redirect for that address exists).

    manage.py import_old_site_images --chi-siamo-draft
        Puts the text and pictures of the old "Conosci Axatel" page into a
        DRAFT of Azienda → Chi siamo. The live page does not change until
        someone opens the draft in the CMS, reviews it and publishes it.

    --only casi|prodotti|chi-siamo|documenti   limit to one part (repeatable)
    --min-score 0.35                 how similar titles must be to match
    --base https://www.axatel.it     the old site
"""
from __future__ import annotations

import html
import io
import json
import re
import shutil
import time
import unicodedata
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand

UA = "Mozilla/5.0 (compatible; axatel-cms-import/1.0)"
DOC_EXT = re.compile(r"\.(pdf|docx?|xlsx?|pptx?|zip|rar|dwg|odt|ods)$", re.I)
SKIP_PAGES = re.compile(r"/(tag|author|carrello|pagamento|mio-account|negozio|sample-page|vegetables)/", re.I)
COLLECTION = "Sito precedente"
STOP = set("""
il lo la i gli le un uno una di a da in con su per tra fra del della dei degli delle al alla ai agli alle
dal dalla dai nel nella nei negli nelle sul sulla sui e ed o che non come piu più anche nuovo nuova nuove
the and for with from per axatel caso casi successo storia storie progetto sistema sistemi
""".split())
# Parts of an old page that are not content.
# Matched against each class name / id on its own, so page builders' content
# wrappers ("elementor-widget-text-editor") are kept.
NOISE = re.compile(r"^(cookie.*|cmplz.*|.*consent.*|.*gdpr.*|menu.*|.*-menu|nav|navbar|.*-nav|site-header|site-footer|"
                   r"header|footer|breadcrumbs?|sidebar|widget-area|share.*|social.*|newsletter.*|popup.*|modal.*|"
                   r"comments?|related.*|search.*|elementor-location-header|elementor-location-footer)$", re.I)


def plain(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", plain(text)) if len(w) >= 3 and w not in STOP}


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return 2 * len(ta & tb) / (len(ta) + len(tb))


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", value or "")).strip()


class Command(BaseCommand):
    help = "Report, download or import the pictures of the old axatel.it (see the module docstring)."

    def add_arguments(self, parser):
        parser.add_argument("--base", default="https://www.axatel.it")
        parser.add_argument("--only", action="append", choices=["casi", "prodotti", "chi-siamo", "documenti"])
        parser.add_argument("--min-score", type=float, default=0.35)
        parser.add_argument("--download", action="store_true")
        parser.add_argument("--clean-download", action="store_true")
        parser.add_argument("--import", dest="do_import", action="store_true")
        parser.add_argument("--attach", action="store_true")
        parser.add_argument("--chi-siamo-draft", action="store_true")

    # -- network -------------------------------------------------------------
    def fetch(self, url, binary=False):
        try:
            with urlopen(Request(url, headers={"User-Agent": UA}), timeout=25) as response:
                data = response.read()
                time.sleep(0.2)  # be gentle with the old site
                return data if binary else data.decode(response.headers.get_content_charset() or "utf-8", "replace")
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            self.stdout.write(self.style.WARNING(f"  ! {url}: {error}"))
            return None

    def wp_json(self, path):
        """All pages of a WordPress REST list, or [] when the API is closed."""
        items, page = [], 1
        while page <= 20:
            sep = "&" if "?" in path else "?"
            raw = self.fetch(f"{self.base}/wp-json/{path}{sep}per_page=100&page={page}")
            if not raw:
                break
            try:
                data = json.loads(raw)
            except ValueError:
                break
            if not isinstance(data, list) or not data:
                break
            items += data
            if len(data) < 100:
                break
            page += 1
        return items

    def page_meta(self, url):
        raw = self.fetch(url)
        if not raw:
            return None
        soup = BeautifulSoup(raw, "html.parser")
        meta = lambda prop: (soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop}) or {}).get("content", "")
        title = meta("og:title") or (soup.h1.get_text(" ", strip=True) if soup.h1 else "") or (soup.title.string if soup.title else "")
        title = re.sub(r"\s*[-|–]\s*Axatel.*$", "", title or "").strip()
        return {"title": title, "url": url, "image": meta("og:image"), "soup": soup}

    # -- the old site --------------------------------------------------------
    def old_cases(self):
        if self._cases is not None:
            return self._cases
        self._cases = self._old_cases()
        return self._cases

    def old_products(self):
        if self._products is not None:
            return self._products
        self._products = self._old_products()
        return self._products

    def _old_cases(self):
        posts = self.wp_json("wp/v2/posts?_embed=wp:featuredmedia")
        if posts:
            out = []
            for post in posts:
                media = (post.get("_embedded") or {}).get("wp:featuredmedia") or [{}]
                out.append({"title": strip_tags(post.get("title", {}).get("rendered", "")),
                            "url": post.get("link", ""), "image": (media[0] or {}).get("source_url", "")})
            self.stdout.write(f"  old site: {len(out)} articles (WordPress API)")
            return out
        # API closed: the links on the success-stories page, then each page's og:image.
        links = []
        for path in ("/casi-di-successo/", "/storie-di-successo/"):
            for n in range(1, 6):
                raw = self.fetch(f"{self.base}{path}" + (f"page/{n}/" if n > 1 else ""))
                if not raw:
                    break
                soup = BeautifulSoup(raw, "html.parser")
                for a in soup.find_all("a", href=True):
                    href = urljoin(self.base, a["href"]).split("#")[0]
                    parsed = urlparse(href)
                    if parsed.netloc.replace("www.", "") != urlparse(self.base).netloc.replace("www.", ""):
                        continue
                    if any(part in parsed.path for part in ("/tag/", "/categoria", "/prodotto", "/page/", "/wp-", "/author/")):
                        continue
                    if parsed.path.strip("/") and parsed.path.count("/") == 2 and href not in links:
                        links.append(href)
        known = {line.strip() for line in self.old_site_paths()}
        out = []
        for href in links:
            if urlparse(href).path in known:
                continue  # a menu page, not an article
            meta = self.page_meta(href)
            if meta and meta["image"]:
                out.append({k: meta[k] for k in ("title", "url", "image")})
        self.stdout.write(f"  old site: {len(out)} articles (from the success-stories page)")
        return out

    def _old_products(self):
        products = self.wp_json("wc/store/v1/products") or self.wp_json("wc/store/products")
        if products:
            out = [{"title": strip_tags(p.get("name", "")), "url": p.get("permalink", ""),
                    "image": ((p.get("images") or [{}])[0] or {}).get("src", "")} for p in products]
            self.stdout.write(f"  old site: {len(out)} products (shop API)")
            return out
        out = []
        for path in self.old_site_paths():
            if path.startswith("/prodotto/") and path.count("/") > 2:
                meta = self.page_meta(self.base + path)
                if meta:
                    out.append({k: meta[k] for k in ("title", "url", "image")})
        self.stdout.write(f"  old site: {len(out)} products (product pages)")
        return out

    @staticmethod
    def old_site_paths():
        path = Path(settings.BASE_DIR) / "core" / "data" / "old_site_urls.txt"
        if not path.exists():
            return []
        return [line.strip() for line in path.read_text().splitlines() if line.strip().startswith("/")]

    def old_chi_siamo(self):
        meta = self.page_meta(f"{self.base}/conosci-axatel/")
        if not meta:
            return None
        soup = meta["soup"]
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form", "svg", "iframe"]):
            tag.decompose()
        for tag in soup.find_all(True):
            if tag.attrs is None:
                continue  # removed with its parent
            names = list(tag.get("class", []) or []) + ([tag.get("id")] if tag.get("id") else [])
            if any(NOISE.match(name) for name in names):
                tag.decompose()
        root = soup.find("main") or soup.find("article") or soup.body or soup
        blocks, seen = [], set()
        for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "img"]):
            if el.name == "img":
                src = el.get("data-src") or el.get("src") or ""
                if src and not src.startswith("data:") and not re.search(r"logo|icon|placeholder", src, re.I):
                    src = urljoin(self.base, src)
                    if src not in seen:
                        seen.add(src)
                        blocks.append(("img", src))
                continue
            if el.find(["p", "li", "h2", "h3", "h4"]):
                continue  # the inner element is taken instead
            text = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
            if len(text) < 2 or text in seen:
                continue
            seen.add(text)
            blocks.append((el.name, text))
        return {"title": meta["title"], "url": meta["url"], "image": meta["image"], "blocks": blocks}

    def old_documents(self):
        files = {}
        for item in self.wp_json("wp/v2/media?media_type=application"):
            url = item.get("source_url", "")
            if DOC_EXT.search(urlparse(url).path):
                files[url] = strip_tags((item.get("title") or {}).get("rendered", "")) or self.file_name(url)
        if files:
            self.stdout.write(f"  old site: {len(files)} documents (media library)")
        else:
            # Media library closed: the files linked from the old pages.
            pages = [self.base + p for p in self.old_site_paths() if not SKIP_PAGES.search(p)]
            pages += [o["url"] for o in self.old_cases() + self.old_products() if o.get("url")]
            self.stdout.write(f"  reading {len(dict.fromkeys(pages))} old pages for linked documents…")
            for page_url in dict.fromkeys(pages):
                raw = self.fetch(page_url)
                if not raw:
                    continue
                for a in BeautifulSoup(raw, "html.parser").find_all("a", href=True):
                    href = urljoin(page_url, a["href"]).split("#")[0]
                    if self.same_site(href) and DOC_EXT.search(urlparse(href).path):
                        files.setdefault(href, a.get_text(" ", strip=True)[:120] or self.file_name(href))
            self.stdout.write(f"  old site: {len(files)} documents (linked from its pages)")
        return [{"title": title, "url": url} for url, title in files.items()]

    def same_site(self, url):
        return urlparse(url).netloc.replace("www.", "") == urlparse(self.base).netloc.replace("www.", "")

    @staticmethod
    def file_name(url):
        return unquote(Path(urlparse(url).path).name) or "file"

    def library_document(self, url, title):
        from wagtail.documents import get_document_model
        from wagtail.utils.file import hash_filelike

        data = self.picture(url)
        if not data:
            return None
        Document = get_document_model()
        existing = Document.objects.filter(file_hash=hash_filelike(io.BytesIO(data))).first()
        if existing:
            return existing
        document = Document(title=(title or self.file_name(url))[:255], collection=self.collection())
        document.file = ContentFile(data, name=self.file_name(url))
        document._set_document_file_metadata()  # size and fingerprint, as the CMS upload form does
        document.save()
        self.imported_documents += 1
        return document

    def collection(self):
        from wagtail.models import Collection

        if self._collection is None:
            root = Collection.get_first_root_node()
            self._collection = root.get_children().filter(name=COLLECTION).first() or root.add_child(name=COLLECTION)
        return self._collection

    def redirect(self, old_url, target):
        """Old file address → its copy, unless that address already has a redirect."""
        from wagtail.contrib.redirects.models import Redirect

        if not old_url or not target or not self.same_site(old_url):
            return
        old_path = Redirect.normalise_path(urlparse(old_url).path)
        if not Redirect.objects.filter(old_path=old_path).exists():
            Redirect.objects.create(old_path=old_path, redirect_link=target, is_permanent=True)
            self.redirects += 1

    # -- matching ------------------------------------------------------------
    def match(self, new_pages, old_items, extra=lambda p: ""):
        pairs = []
        for page in new_pages:
            for index, old in enumerate(old_items):
                slug_words = urlparse(old["url"]).path.replace("-", " ").replace("/", " ")
                score = max(similarity(f"{page.title} {extra(page)}", old["title"]),
                            similarity(f"{page.title} {page.slug.replace('-', ' ')}", f"{old['title']} {slug_words}"))
                pairs.append((score, page.pk, index))
        pairs.sort(reverse=True)
        used_pages, used_old, result = set(), set(), {}
        for score, page_id, index in pairs:
            if score < self.min_score or page_id in used_pages or index in used_old:
                continue
            if not old_items[index].get("image"):
                continue
            used_pages.add(page_id)
            used_old.add(index)
            result[page_id] = (old_items[index], score)
        return result

    # -- pictures ------------------------------------------------------------
    def picture(self, url):
        if url not in self._pictures:
            self._pictures[url] = self.fetch(url, binary=True)
        return self._pictures[url]

    def filename(self, page, url):
        ext = Path(urlparse(url).path).suffix.lower() or ".jpg"
        return f"{page.slug}{ext if ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif') else '.jpg'}"

    def library_image(self, page, url, title):
        from wagtail.images import get_image_model

        data = self.picture(url)
        if not data:
            return None
        Image = get_image_model()
        from wagtail.utils.file import hash_filelike

        # Same fingerprint as Wagtail's own uploads: a picture already in the
        # library (uploaded by hand or by an earlier run) is reused.
        existing = Image.objects.filter(file_hash=hash_filelike(io.BytesIO(data))).first()
        if existing:
            self.redirect(url, existing.file.url)
            return existing
        image = Image(title=title[:255], collection=self.collection())
        image.file = ImageFile(io.BytesIO(data), name=self.filename(page, url))
        image._set_image_file_metadata()  # size and fingerprint, as the CMS upload form does
        image.save()
        self.imported += 1
        self.redirect(url, image.file.url)
        return image

    # -- main ----------------------------------------------------------------
    def handle(self, *args, **opts):
        self.base = opts["base"].rstrip("/")
        self.min_score = opts["min_score"]
        self._pictures, self._collection, self.imported = {}, None, 0
        self._cases = self._products = None
        self.imported_documents = self.redirects = 0
        download_dir = Path(settings.MEDIA_ROOT) / "old-site"
        if opts["clean_download"]:
            shutil.rmtree(download_dir, ignore_errors=True)
            self.stdout.write("Removed media/old-site/.")
            return
        do_import = opts["do_import"] or opts["attach"]
        parts = opts["only"] or ["casi", "prodotti", "chi-siamo", "documenti"]
        downloads = []  # (zip name, url)

        from casi.models import CasoSuccessoPage
        from home.models import InfoPage
        from products.models import ProductPage

        for part, model, loader, extra in (
            ("casi", CasoSuccessoPage, self.old_cases, lambda p: getattr(p, "client", "")),
            ("prodotti", ProductPage, self.old_products, lambda p: ""),
        ):
            if part not in parts:
                continue
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{'Casi di successo' if part == 'casi' else 'Prodotti'}"))
            pages = list(model.objects.filter(locale__language_code="it").specific().order_by("title"))
            old_items = loader()
            matches = self.match(pages, old_items, extra)
            for page in pages:
                has = bool(page.cover_image_id)
                found = matches.get(page.pk)
                line = f"  {'✓' if has else '✗'} {page.title[:55]:55}"
                if not found:
                    self.stdout.write(f"{line}  — no match on the old site")
                    continue
                old, score = found
                self.stdout.write(f"{line}  ← {old['title'][:50]} ({score:.2f})\n      {old['image']}")
                downloads.append((f"{part}/{self.filename(page, old['image'])}", old["image"]))
                if do_import:
                    image = self.library_image(page, old["image"], f"{page.title} (sito precedente)")
                    if image is None:
                        continue
                    if opts["attach"] and not has:
                        if page.has_unpublished_changes:
                            self.stdout.write(self.style.WARNING("      not set: this page has unpublished changes; pick the picture by hand"))
                            continue
                        page.cover_image = image
                        page.save_revision(log_action=True).publish()
                        self.stdout.write(self.style.SUCCESS("      set as Immagine di copertina and published"))
            if old_items:
                unmatched = [o for i, o in enumerate(old_items) if o.get("image") and o not in [m[0] for m in matches.values()]]
                if unmatched:
                    self.stdout.write(f"  Old {part} not matched to a new page ({len(unmatched)}): "
                                      + "; ".join(o["title"][:40] for o in unmatched[:15]) + (" …" if len(unmatched) > 15 else ""))

        if "chi-siamo" in parts:
            self.stdout.write(self.style.MIGRATE_HEADING("\nChi siamo (old: /conosci-axatel/)"))
            old = self.old_chi_siamo()
            if not old:
                self.stdout.write("  The old page could not be read.")
            else:
                texts = [b for b in old["blocks"] if b[0] != "img"]
                pictures = [b[1] for b in old["blocks"] if b[0] == "img"]
                self.stdout.write(f"  {len(texts)} text blocks, {len(pictures)} pictures. Text:")
                for kind, value in texts[:60]:
                    self.stdout.write(f"    {'#' if kind.startswith('h') else '•' if kind == 'li' else ' '} {value[:160]}")
                page = InfoPage.objects.filter(locale__language_code="it", slug="chi-siamo").first()
                for n, src in enumerate(pictures, 1):
                    downloads.append((f"chi-siamo/{n:02d}{Path(urlparse(src).path).suffix or '.jpg'}", src))
                if opts["chi_siamo_draft"]:
                    self.chi_siamo_draft(page, old, pictures)
                elif do_import and page is not None:
                    for n, src in enumerate(pictures, 1):
                        self.library_image(page, src, f"Chi siamo {n} (sito precedente)")

        if "documenti" in parts:
            self.stdout.write(self.style.MIGRATE_HEADING("\nDocumenti (PDF and other files)"))
            documents = self.old_documents()
            for doc in documents[:40]:
                self.stdout.write(f"    {doc['title'][:60]:60}  {self.file_name(doc['url'])}")
            if len(documents) > 40:
                self.stdout.write(f"    … and {len(documents) - 40} more")
            for doc in documents:
                downloads.append((f"documenti/{self.file_name(doc['url'])}", doc["url"]))
                if do_import:
                    document = self.library_document(doc["url"], doc["title"])
                    if document is not None:
                        self.redirect(doc["url"], document.file.url)

        if opts["download"] and downloads:
            download_dir.mkdir(parents=True, exist_ok=True)
            zip_path = download_dir / "old-site-images.zip"
            with zipfile.ZipFile(zip_path, "w") as archive:
                names = set()
                for name, url in downloads:
                    if name in names:
                        stem, ext = Path(name).with_suffix(""), Path(name).suffix
                        name = f"{stem}-{len(names)}{ext}"
                    names.add(name)
                    data = self.picture(url)
                    if data:
                        (download_dir / name).parent.mkdir(parents=True, exist_ok=True)
                        (download_dir / name).write_bytes(data)
                        archive.writestr(name, data)
            self.stdout.write(self.style.SUCCESS(
                f"\nSaved {len(downloads)} files. Download: /media/old-site/old-site-images.zip "
                "(remove later with --clean-download)."))
        if do_import:
            self.stdout.write(self.style.SUCCESS(
                f"\nAdded {self.imported} new pictures to Immagini and {self.imported_documents} new documents to "
                f"Documenti (collection \"{COLLECTION}\"); {self.redirects} redirects from the old file addresses."))
        if not (opts["download"] or do_import or opts["chi_siamo_draft"]):
            self.stdout.write("\nNothing was changed (report only). Options: --download, --import, --attach, --chi-siamo-draft.")

    def chi_siamo_draft(self, page, old, pictures):
        from wagtail.rich_text import RichText

        if page is None:
            self.stdout.write(self.style.WARNING("  No Chi siamo page in Italian: run import_info_pages first."))
            return
        if page.has_unpublished_changes:
            self.stdout.write(self.style.WARNING("  Chi siamo already has an unpublished draft: not overwritten. "
                                                 "Publish or discard it in the CMS, then run this again."))
            return
        body, chunk = [], []

        def flush():
            if chunk:
                body.append(("rich_text", RichText("".join(chunk))))
                chunk.clear()

        list_open = False
        for kind, value in old["blocks"]:
            if kind == "img":
                if list_open:
                    chunk.append("</ul>")
                    list_open = False
                flush()
                image = self.library_image(page, value, f"Chi siamo (sito precedente) {len(body) + 1}")
                if image:
                    body.append(("image", {"image": image, "caption": ""}))
                continue
            if kind == "h1":
                continue  # the page title
            if kind == "li":
                if not list_open:
                    chunk.append("<ul>")
                    list_open = True
                chunk.append(f"<li>{html.escape(value)}</li>")
                continue
            if list_open:
                chunk.append("</ul>")
                list_open = False
            tag = {"h2": "h2", "h3": "h3", "h4": "h3"}.get(kind, "p")
            chunk.append(f"<{tag}>{html.escape(value)}</{tag}>")
        if list_open:
            chunk.append("</ul>")
        flush()
        if not body:
            self.stdout.write(self.style.WARNING("  Nothing readable on the old page: draft not created."))
            return
        page.body = body
        if not page.cover_image_id and old.get("image"):
            page.cover_image = self.library_image(page, old["image"], "Chi siamo (sito precedente)")
        page.save_revision(log_action=True)
        self.stdout.write(self.style.SUCCESS(
            "  Draft created: Pagine → Azienda → Chi siamo → Anteprima, then Pubblica (or discard the draft). "
            "The live page has not changed."))
