"""
Old WordPress addresses → pages of the new site, as permanent (301)
redirects, so links in Google, e-mails and other sites keep working when
the domain moves here.

Two steps, with a human check in between:

    # 1. Proposal: writes a CSV (open it in Excel) and prints a summary
    python manage.py import_old_redirects --propose
    python manage.py import_old_redirects --propose --urls more-urls.txt   # add addresses
    python manage.py import_old_redirects --propose --sitemap https://www.axatel.it/sitemap_index.xml

    # 2. After checking/correcting the "to" column:
    python manage.py import_old_redirects --apply /tmp/axatel-redirects.csv [--dry-run]

The addresses come from core/data/old_site_urls.txt (the old site's
sitemaps on 2026-10-04); --urls adds a file (one address per line, e.g. the
Google Search Console "Pages" export), --sitemap reads a live sitemap.

Each row gets a confidence: alta (same page), media (related page, check
it), bassa (falls back to a list page or the homepage). Rows whose address
already exists on the new site are marked "stesso indirizzo" and not
imported. --apply never touches redirects that already exist (use
--replace to update them). The result is in Impostazioni → Reindirizzamenti,
where every redirect can still be edited or deleted; the CSV can also be
imported there (Importa: column 1 = from, column 2 = to).
"""
import csv
import re
import urllib.request
from pathlib import Path
from xml.etree import ElementTree

from django.core.management.base import BaseCommand, CommandError

DATA = Path(__file__).resolve().parents[2] / "data" / "old_site_urls.txt"
DEFAULT_OUT = "/tmp/axatel-redirects.csv"

# Addresses served by the frontend itself (not pages in the CMS).
FRONTEND_ROUTES = {
    "/", "/contatti", "/news", "/monitoraggio", "/prodotti", "/casi", "/soluzioni", "/servizi",
    "/azienda/team", "/approfondimenti/academy", "/approfondimenti/faq", "/approfondimenti/glossario",
}

# Old pages whose new home is known: (pattern, target, confidence, note).
RULES = [
    (r"^/(sample-page|vegetables)$", "/", "alta", "pagina di esempio di WordPress"),
    (r"^/(prodotto|negozio|carrello|pagamento|mio-account|catalogo-sensori(-\d+)?)$", "/prodotti", "alta",
     "negozio / catalogo del vecchio sito"),
    (r"^/(categoria-prodotto|tag-prodotto|sensori)(/.*)?$", "/prodotti", "alta", "categoria di prodotti"),
    (r"^/(storie-di-successo|casi-di-successo)$", "/casi", "alta", ""),
    (r"^/conosci-axatel$", "/azienda/chi-siamo", "alta", ""),
    (r"^/diventa-partner$", "/azienda/diventa-partner", "alta", ""),
    (r"^/supervisione-e-controllo$", "/soluzioni/scada", "media", "supervisione e controllo → SCADA"),
    (r"^/ingegneria$", "/soluzioni/progettazione", "media", "servizi di ingegneria → Progettazione"),
    (r"^/sviluppo-elettronico$", "/soluzioni/firmware", "media", "sviluppo elettronico → Firmware"),
    (r"^/iot$", "/soluzioni/lorawan", "media", "IoT → LoRaWAN"),
    (r"^/citta$", "/monitoraggio", "media", "smart city → Cosa monitoriamo"),
    (r"^/strade$", "/monitoraggio/traffico", "media", "strade → Monitoraggio traffico"),
    (r"^/progetto$", "/casi", "bassa", "pagina generica sui progetti"),
    (r"^/author/.*$", "/azienda/chi-siamo", "alta", "pagina autore di WordPress"),
    (r"^/tag/(frana|monitoraggiofrane|colatadetritica|fadalto|cadore|cortina)$", "/monitoraggio/frane", "media", "tag"),
    (r"^/tag/fiumi$", "/monitoraggio/fiumi", "media", "tag"),
    (r"^/tag/(strade|anas)$", "/monitoraggio/traffico", "media", "tag"),
    (r"^/tag/citta$", "/monitoraggio", "media", "tag"),
    (r"^/tag/control-room$", "/soluzioni/control-room", "media", "tag"),
    (r"^/tag/(lorawan|iot|nfc)$", "/soluzioni/lorawan", "media", "tag"),
    (r"^/tag/ingegneria$", "/soluzioni/progettazione", "media", "tag"),
    (r"^/tag/impianti$", "/soluzioni/plc", "media", "tag"),
    (r"^/tag/.*$", "/casi", "bassa", "tag degli articoli"),
    (r"^/(category|categoria)/.*$", "/news", "bassa", "categoria degli articoli"),
    (r"^/(feed|comments/feed)$", "/feed.xml", "alta", "feed RSS"),
]

# Old product names → the system they are part of now (checked by a person!).
PRODUCT_HINTS = [
    (r"cerere-pro-ai?ri?a?", "cerere-pro-aria"),
    (r"river", "angel-river"),
    (r"bridge", "angel-bridge"),
    (r"clinometro|estensimetr|barra-estensimetrica|paramassi|distacco", "geo-angel"),
    (r"semaforic|lanterna|telecamera-.*traffico", "traffic-alert"),
    (r"guard-rail|segnaletica|sos-angel-road", "angel-road-site"),
]
STOP = {"di", "da", "a", "e", "il", "la", "lo", "per", "con", "in", "del", "della", "lorawan", "sensore",
        "sistema", "fv", "mobile", "2", "3"}


def tokens(slug: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", slug.lower()) if t and t not in STOP}


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def normalise(address: str) -> str:
    address = address.strip()
    address = re.sub(r"^https?://[^/]+", "", address, flags=re.I)
    address = address.split("#")[0].split("?")[0]
    address = re.sub(r"/{2,}", "/", address)
    if not address.startswith("/"):
        address = "/" + address
    return address.rstrip("/") or "/"


def read_sitemap(url: str, seen=None) -> list[str]:
    seen = seen if seen is not None else set()
    if url in seen:
        return []
    seen.add(url)
    request = urllib.request.Request(url, headers={"User-Agent": "Axatel-redirects/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        root = ElementTree.fromstring(response.read())
    found = []
    for loc in root.iter():
        if loc.tag.endswith("loc") and loc.text:
            if loc.text.strip().endswith(".xml"):
                found += read_sitemap(loc.text.strip(), seen)
            else:
                found.append(loc.text.strip())
    return found


class Command(BaseCommand):
    help = "Propose and import redirects from the old WordPress addresses."

    def add_arguments(self, parser):
        parser.add_argument("--propose", action="store_true", help="write the proposal CSV")
        parser.add_argument("--out", default=DEFAULT_OUT)
        parser.add_argument("--urls", action="append", default=[], help="file with more old addresses")
        parser.add_argument("--sitemap", help="read the old addresses from this sitemap (needs internet)")
        parser.add_argument("--no-builtin", action="store_true", help="ignore core/data/old_site_urls.txt")
        parser.add_argument("--apply", metavar="CSV", help="create the redirects of a checked CSV")
        parser.add_argument("--replace", action="store_true", help="with --apply: update existing redirects")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if options["apply"]:
            return self.apply(options["apply"], options["replace"], options["dry_run"])
        if not options["propose"]:
            raise CommandError("Use --propose (write the CSV to check) or --apply FILE.csv")
        return self.propose(options)

    # ── proposal ───────────────────────────────────────────────────────
    def old_addresses(self, options) -> list[str]:
        lines = []
        if not options["no_builtin"]:
            lines += DATA.read_text(encoding="utf-8").splitlines()
        for path in options["urls"]:
            lines += Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
        if options["sitemap"]:
            lines += read_sitemap(options["sitemap"])
        found = []
        for line in lines:
            line = line.strip().split(",")[0].split("\t")[0].strip('"')
            if not line or line.startswith("#") or not re.match(r"^(https?://|/)", line, re.I):
                continue
            path = normalise(line)
            if path not in found:
                found.append(path)
        return found

    def site_pages(self):
        from wagtail.models import Page

        pages = {}
        for page in Page.objects.live().filter(locale__language_code="it", depth__gt=2).specific():
            path = normalise(page.get_url_parts()[2] if page.get_url_parts() else page.url_path)
            pages[path] = page
        return pages

    def documents(self):
        from wagtail.documents import get_document_model

        found = {}
        for document in get_document_model().objects.all():
            if document.file:
                name = Path(document.file.name).stem.lower()
                found[re.sub(r"_[a-z0-9]{7}$", "", name)] = document
        return found

    def propose_one(self, old, pages, documents):
        """→ (target, confidence, note)"""
        if old in pages or old in FRONTEND_ROUTES:
            return old, "stesso indirizzo", "esiste già sul nuovo sito: nessun reindirizzamento"
        if old.startswith("/wp-content/"):
            stem = Path(old).stem.lower()
            stem_clean = re.sub(r"-(\d+x\d+|scaled|\d)$", "", stem)
            for key in (stem, stem_clean):
                if key in documents:
                    return documents[key].url, "alta", f"documento \"{documents[key].title}\""
            best = max(documents.items(), key=lambda kv: similarity(kv[0], stem_clean), default=None)
            if best and similarity(best[0], stem_clean) >= 0.5:
                return best[1].url, "media", f"documento simile \"{best[1].title}\""
            return "", "nessuna", "file del vecchio sito: caricalo in Documenti, poi scrivi qui il suo indirizzo"
        for pattern, target, confidence, note in RULES:
            if re.match(pattern, old):
                return target, confidence, note
        slug = old.rsplit("/", 1)[-1]
        if old.startswith("/prodotto/"):
            products = {path: page for path, page in pages.items() if page.content_type.model == "productpage"}
            best = max(products, key=lambda p: similarity(slug, p.rsplit("/", 1)[-1]), default=None)
            if best and similarity(slug, best.rsplit("/", 1)[-1]) >= 0.6:
                return best, "alta", f"prodotto \"{products[best].title}\""
            for pattern, product_slug in PRODUCT_HINTS:
                if re.search(pattern, slug):
                    target = next((p for p in products if p.endswith("/" + product_slug)), None)
                    if target:
                        return target, "media", f"fa parte di \"{products[target].title}\"? da verificare"
            return "/prodotti", "bassa", "prodotto non più a catalogo: elenco prodotti"
        # Same slug anywhere on the new site (old articles → case studies…)
        same = [path for path in pages if path.rsplit("/", 1)[-1] == slug]
        if len(same) == 1:
            return same[0], "alta", f"stessa pagina \"{pages[same[0]].title}\""
        best = max(pages, key=lambda p: similarity(slug, p.rsplit("/", 1)[-1]), default=None)
        if best and similarity(slug, best.rsplit("/", 1)[-1]) >= 0.5:
            return best, "media", f"pagina simile \"{pages[best].title}\""
        return "/", "bassa", "nessuna pagina corrispondente: homepage"

    def propose(self, options):
        olds = self.old_addresses(options)
        pages = self.site_pages()
        documents = self.documents()
        rows = []
        for old in olds:
            target, confidence, note = self.propose_one(old, pages, documents)
            rows.append({"from": old, "to": target, "confidenza": confidence, "nota": note})
        with open(options["out"], "w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=["from", "to", "confidenza", "nota"])
            writer.writeheader()
            writer.writerows(rows)
        counts = {}
        for row in rows:
            counts[row["confidenza"]] = counts.get(row["confidenza"], 0) + 1
        width = max(len(r["from"]) for r in rows) if rows else 10
        self.stdout.write("To check (media = related page, nessuna = no target yet):")
        for row in rows:
            if row["confidenza"] in ("media", "nessuna"):
                self.stdout.write(f"  {row['confidenza']:<7} {row['from']:<{min(width, 60)}} → {row['to'] or '?'}   {row['nota']}")
        fallback = {}
        for row in rows:
            if row["confidenza"] == "bassa":
                fallback.setdefault(row["to"], []).append(row["from"])
        if fallback:
            self.stdout.write("Sent to a list page (bassa), replace with a better page if there is one:")
            for target, olds in fallback.items():
                self.stdout.write(f"  {len(olds):>3} → {target}   e.g. {', '.join(olds[:3])}")
        self.stdout.write("")
        self.stdout.write("  " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + f"  (totale {len(rows)})")
        self.stdout.write(self.style.SUCCESS(f"Proposal written to {options['out']}"))
        self.stdout.write("Check the 'to' column (above: the rows to look at), then:")
        self.stdout.write(f"  python manage.py import_old_redirects --apply {options['out']} --dry-run")

    # ── apply ──────────────────────────────────────────────────────────
    def apply(self, path, replace, dry_run):
        from wagtail.contrib.redirects.models import Redirect
        from wagtail.models import Page

        pages = self.site_pages()
        created = updated = skipped = 0
        with open(path, newline="", encoding="utf-8-sig") as handle:
            sample = handle.read(2048)
            handle.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t") if sample else csv.excel
            reader = csv.reader(handle, dialect)
            for row in reader:
                if len(row) < 2 or row[0].strip().lower() in ("from", "da", "vecchio indirizzo"):
                    continue
                old, target = normalise(row[0]), row[1].strip()
                status = row[2].strip() if len(row) > 2 else ""
                if not target or status == "stesso indirizzo":
                    skipped += 1
                    continue
                if target.startswith("/"):
                    target = normalise(target)
                if target == old:
                    skipped += 1
                    continue
                page = pages.get(target) if target.startswith("/") else None
                old_path = Redirect.normalise_path(old)
                existing = Redirect.objects.filter(old_path=old_path, site__isnull=True).first()
                if existing and not replace:
                    self.stdout.write(f"  = {old} already redirects (left as it is)")
                    skipped += 1
                    continue
                verb = "update" if existing else "add"
                self.stdout.write(f"  {'+' if not existing else '~'} {old} → {target}" + (" (page)" if page else ""))
                if dry_run:
                    created += not existing
                    updated += bool(existing)
                    continue
                redirect = existing or Redirect(old_path=old_path, site=None)
                redirect.is_permanent = True
                redirect.redirect_page = page if isinstance(page, Page) else None
                redirect.redirect_link = "" if page else target
                redirect.save()
                created += verb == "add"
                updated += verb == "update"
        prefix = "Would add" if dry_run else "Added"
        self.stdout.write(self.style.SUCCESS(f"{prefix} {created}, updated {updated}, skipped {skipped}."))
        if not dry_run:
            self.stdout.write("The site uses them within a minute (Impostazioni → Reindirizzamenti).")
