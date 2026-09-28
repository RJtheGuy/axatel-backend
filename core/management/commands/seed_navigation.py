"""
Copy the site menu into the CMS (Impostazioni → Navigazione).

    python manage.py seed_navigation            # add what's missing
    python manage.py seed_navigation --dry-run  # show what would be added

Only ADDS. It never deletes, reorders or renames anything already in the
CMS menu, so it is safe to run again after editors have changed the menu:
  - menu entries, dropdown columns and links that don't exist yet
    (matched by their Italian label) are appended;
  - empty English/French labels are filled in.

Links point to the real CMS page when one exists at that address (so they
follow slug changes), otherwise to the address as a custom URL.
"""
import uuid

from django.core.management.base import BaseCommand
from django.http import Http404
from django.test import RequestFactory
from wagtail.models import Site

from core.navigation_defaults import DEFAULT_MENU
from core.site_settings import NavigationSettings


def _key(label: str) -> str:
    return (label or "").strip().rstrip("?").strip().lower()


def _item(value: dict, block_type: str = "item") -> dict:
    return {"type": block_type, "value": value, "id": str(uuid.uuid4())}


class Command(BaseCommand):
    help = "Add the built-in site menu to Impostazioni → Navigazione (adds only, never overwrites)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show the changes without saving.")

    def handle(self, *args, dry_run=False, **options):
        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        if site is None:
            self.stderr.write("No Wagtail site configured.")
            return
        self.site = site
        self.request = RequestFactory().get("/", HTTP_HOST=site.hostname or "localhost")
        self.changes = []

        nav = NavigationSettings.for_site(site)
        items = list(nav.items.get_prep_value()) if nav.items else []

        for position, default in enumerate(DEFAULT_MENU):
            existing = next((i for i in items if _key(i["value"].get("label")) == _key(default["label"])), None)
            if existing is None:
                # Put it right after the entry that precedes it in the default
                # menu (if the editor has it), otherwise at the end.
                insert_at = len(items)
                for previous in reversed(DEFAULT_MENU[:position]):
                    found = [n for n, i in enumerate(items) if _key(i["value"].get("label")) == _key(previous["label"])]
                    if found:
                        insert_at = found[0] + 1
                        break
                items.insert(insert_at, _item(self._new_entry(default)))
                self.changes.append(f"+ menu entry '{default['label']}'")
                continue
            self._fill_labels(existing["value"], default, f"menu entry '{default['label']}'")
            self._merge_groups(existing["value"], default)

        if not self.changes:
            self.stdout.write(self.style.SUCCESS("Menu already complete - nothing to add."))
            return
        for line in self.changes:
            self.stdout.write(line)
        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run: {len(self.changes)} change(s) NOT saved."))
            return
        nav.items = items
        nav.save()
        self.stdout.write(self.style.SUCCESS(f"Saved {len(self.changes)} change(s) to Impostazioni → Navigazione."))

    # ── helpers ────────────────────────────────────────────────────────
    def _target(self, href: str) -> dict:
        """Link to the CMS page at this address if there is one."""
        if href and href.startswith("/") and not href.startswith("//"):
            parts = [p for p in href.split("/") if p]
            try:
                page, _, _ = self.site.root_page.specific.route(self.request, parts)
                if page.live:
                    return {"page": page.id, "custom_url": ""}
            except Http404:
                pass
        return {"page": None, "custom_url": href or ""}

    def _labels(self, source: dict) -> dict:
        return {"label": source["label"], "label_en": source.get("label_en", ""),
                "label_fr": source.get("label_fr", ""), "visible": True}

    def _new_link(self, link: dict) -> dict:
        return {**self._labels(link), **self._target(link["href"]), "open_in_new_tab": False}

    def _new_group(self, group: dict) -> dict:
        return {**self._labels(group), "links": [_item(self._new_link(l)) for l in group["links"]]}

    def _new_entry(self, entry: dict) -> dict:
        value = {**self._labels(entry), "page": None, "custom_url": "", "groups": []}
        if entry.get("href"):
            value.update(self._target(entry["href"]))
        value["groups"] = [_item(self._new_group(g)) for g in entry.get("groups", [])]
        return value

    def _fill_labels(self, value: dict, default: dict, what: str):
        for lang in ("en", "fr"):
            field = f"label_{lang}"
            if not (value.get(field) or "").strip() and default.get(field):
                value[field] = default[field]
                self.changes.append(f"~ {what}: {lang.upper()} label '{default[field]}'")

    def _merge_groups(self, entry: dict, default: dict):
        groups = entry.setdefault("groups", [])
        for dgroup in default.get("groups", []):
            group = next((g for g in groups if _key(g["value"].get("label")) == _key(dgroup["label"])), None)
            if group is None:
                groups.append(_item(self._new_group(dgroup)))
                self.changes.append(f"+ column '{dgroup['label']}' in '{default['label']}'")
                continue
            self._fill_labels(group["value"], dgroup, f"column '{dgroup['label']}'")
            links = group["value"].setdefault("links", [])
            for index, dlink in enumerate(dgroup["links"]):
                link = next((l for l in links if _key(l["value"].get("label")) == _key(dlink["label"])), None)
                if link is None:
                    # Same place as in the default menu: after the link that
                    # precedes it there, or first if it is first there.
                    insert_at = 0 if index == 0 else len(links)
                    for previous in reversed(dgroup["links"][:index]):
                        found = [n for n, l in enumerate(links) if _key(l["value"].get("label")) == _key(previous["label"])]
                        if found:
                            insert_at = found[0] + 1
                            break
                    links.insert(insert_at, _item(self._new_link(dlink)))
                    self.changes.append(f"+ link '{dlink['label']}' in '{dgroup['label']}'")
                else:
                    self._fill_labels(link["value"], dlink, f"link '{dlink['label']}'")
