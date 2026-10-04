"""
Apply the requested site corrections (Correzioni_sito.pdf) to the content
that is already in the CMS. Run once; running it again changes nothing.

    python manage.py apply_site_corrections --dry-run
    python manage.py apply_site_corrections

1. "Diventa partner" and "Invia il CV": the form opens right on the page.
   The "Parliamone / contattaci" box that sent visitors to /contatti is
   replaced by a "Modulo di contatto" block (for the CV with an attachment
   field). To switch it off later: remove the block in the CMS.
2. Footer "Seguici": LinkedIn and Facebook (Impostazioni → Footer → Seguici).
3. "Gallerie" becomes "Tunnel" at /monitoraggio/tunnel: the CMS page (if
   any) gets the new title and address, the menu entry is renamed, and the
   old address redirects (Impostazioni → Reindirizzamenti).

Pages with an unpublished draft waiting are listed and left alone, so no
one's draft goes online by surprise.
"""
import copy
import json
import uuid

from django.core.management.base import BaseCommand
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site

from core.site_settings import FooterSettings, NavigationSettings
from home.models import InfoPage
from monitoring.models import MonitoringPage

FORMS = {
    "diventa-partner": {
        "form_type": "partner", "show_attachment": False,
        "heading": {"it": "Proponi una collaborazione", "en": "Propose a partnership", "fr": "Proposez un partenariat"},
    },
    "invia-il-cv": {
        "form_type": "candidate", "show_attachment": True,
        "heading": {"it": "Invia la tua candidatura", "en": "Send your application", "fr": "Envoyez votre candidature"},
    },
}

SOCIAL = [
    ("linkedin", "https://www.linkedin.com/company/axatel/"),
    ("facebook", "https://www.facebook.com/profile.php?id=61587985567497"),
]

TUNNEL_LABELS = {"label": "Tunnel", "label_en": "Tunnels", "label_fr": "Tunnels"}


def _strip_tags(text):
    import re
    return re.sub(r"<[^>]+>", "", text or "").strip()


class Command(BaseCommand):
    help = "Apply the requested corrections to the CMS content (forms on partner/CV pages, socials, Tunnel)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, dry_run=False, **options):
        self.dry_run = dry_run
        self.changes = 0
        self.contact_forms()
        self.social_links()
        self.tunnel()
        verb = "would change" if dry_run else "changed"
        self.stdout.write(self.style.SUCCESS(f"{self.changes} item(s) {verb}."))

    # -- helpers -----------------------------------------------------------
    def save_page(self, page, live_page):
        """Save a revision; publish it when the page is live."""
        revision = page.save_revision(log_action=True)
        if live_page.live:
            revision.publish()

    def editable(self, page):
        """The object to edit, or None when a draft is waiting."""
        if page.live and page.has_unpublished_changes:
            self.stdout.write(self.style.WARNING(
                f"! {page.url or page.title}: has a draft waiting. Publish or discard it, then run this again."
            ))
            return None
        if not page.live and page.get_latest_revision():
            return page.get_latest_revision_as_object()
        return page

    # -- 1. forms ----------------------------------------------------------
    def contact_forms(self):
        for slug, spec in FORMS.items():
            for page in InfoPage.objects.filter(slug=slug).select_related("locale"):
                language = page.locale.language_code
                where = f"{page.url or page.slug} [{language}]"
                source = self.editable(page)
                if source is None:
                    continue
                raw = json.loads(json.dumps(list(source.body.raw_data)))
                if any(block.get("type") == "contact_form" for block in raw):
                    self.stdout.write(f"= {where}: form already on the page")
                    continue
                cta_index = next(
                    (i for i, block in enumerate(raw)
                     if block.get("type") == "cta" and str((block.get("value") or {}).get("button_url", "")).startswith("/contatti")),
                    None,
                )
                intro = _strip_tags((raw[cta_index]["value"] or {}).get("heading", "")) if cta_index is not None else ""
                form = {
                    "type": "contact_form",
                    "id": str(uuid.uuid4()),
                    "value": {
                        "heading": spec["heading"].get(language, spec["heading"]["it"]),
                        "intro": intro,
                        "form_type": spec["form_type"],
                        "show_company": True,
                        "show_phone": True,
                        "show_message": True,
                        "show_attachment": spec["show_attachment"],
                        "submit_label": "",
                        "success_message": "",
                    },
                }
                if cta_index is not None:
                    raw[cta_index] = form
                    self.stdout.write(f"~ {where}: 'contact us' box replaced by the form")
                else:
                    raw.append(form)
                    self.stdout.write(f"~ {where}: form added at the end")
                self.changes += 1
                if not self.dry_run:
                    source.body = raw
                    self.save_page(source, page)

    # -- 2. socials --------------------------------------------------------
    def social_links(self):
        for site in Site.objects.all():
            footer = FooterSettings.for_site(site)
            have = {block.value.get("network") for block in footer.social or []}
            missing = [(network, url) for network, url in SOCIAL if network not in have]
            if not missing:
                self.stdout.write(f"= footer ({site.hostname}): LinkedIn and Facebook already there")
                continue
            for network, url in missing:
                self.stdout.write(f"+ footer ({site.hostname}): {network} → {url}")
                self.changes += 1
            if not self.dry_run:
                raw = json.loads(json.dumps(list(footer.social.raw_data))) if footer.social else []
                for network, url in missing:
                    raw.append({"type": "social", "id": str(uuid.uuid4()),
                                "value": {"network": network, "url": url, "label": "", "visible": True}})
                footer.social = raw
                footer.save()

    # -- 3. Tunnel ---------------------------------------------------------
    def tunnel(self):
        target_path = "/monitoraggio/tunnel"
        if MonitoringPage.objects.filter(slug="tunnel").exists():
            self.stdout.write("= Tunnel page already exists")
        for page in MonitoringPage.objects.filter(slug="gallerie").select_related("locale"):
            if MonitoringPage.objects.filter(slug="tunnel", locale=page.locale).exists():
                continue
            source = self.editable(page)
            if source is None:
                continue
            new_title = source.title.replace("Gallerie", "Tunnel").replace("gallerie", "tunnel")
            if new_title == source.title:
                new_title = "Monitoraggio tunnel"
            self.stdout.write(f"~ {page.url or page.slug} [{page.locale.language_code}]: '{source.title}' → '{new_title}', address → tunnel")
            self.changes += 1
            if not self.dry_run:
                source.title = new_title
                source.slug = "tunnel"
                if getattr(source, "category", "") == "Gallerie":
                    source.category = "Tunnel"
                self.save_page(source, page)

        old_path = Redirect.normalise_path("/monitoraggio/gallerie/")
        if Redirect.objects.filter(old_path=old_path).exists():
            self.stdout.write("= redirect /monitoraggio/gallerie already there")
        else:
            self.stdout.write(f"+ redirect /monitoraggio/gallerie → {target_path}")
            self.changes += 1
            if not self.dry_run:
                tunnel_page = MonitoringPage.objects.filter(slug="tunnel", locale__language_code="it").first()
                Redirect.objects.create(
                    old_path=old_path, is_permanent=True,
                    redirect_page=tunnel_page if tunnel_page else None,
                    redirect_link="" if tunnel_page else target_path,
                )

        for site in Site.objects.all():
            nav = NavigationSettings.for_site(site)
            raw = json.loads(json.dumps(list(nav.items.raw_data)))
            renamed = []

            def fix(value):
                url = (value.get("custom_url") or "").rstrip("/")
                page_id = value.get("page")
                points = url.endswith("/monitoraggio/gallerie")
                if page_id:
                    linked = Page.objects.filter(id=page_id).first()
                    points = points or bool(linked and linked.slug in ("gallerie", "tunnel"))
                if not points and (value.get("label") or "").strip().lower() != "gallerie":
                    return
                if value.get("label") == "Tunnel" and not url.endswith("/gallerie"):
                    return
                old = value.get("label")
                value.update(TUNNEL_LABELS)
                if url.endswith("/monitoraggio/gallerie"):
                    value["custom_url"] = target_path
                renamed.append(old)

            for item in raw:
                value = item.get("value") or {}
                for group in value.get("groups") or []:
                    gvalue = group.get("value", group)
                    for link in gvalue.get("links") or []:
                        fix(link.get("value", link))
            for old in renamed:
                self.stdout.write(f"~ menu ({site.hostname}): '{old}' → 'Tunnel' ({target_path})")
                self.changes += 1
            if renamed and not self.dry_run:
                nav.items = raw
                nav.save()
