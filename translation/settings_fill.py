"""
Fill the English/French fields of the site settings that are still empty:
menu labels (Impostazioni → Navigazione), the header button, the team's
roles, descriptions and departments, and the chatbot answers. Fields someone already filled in are
never changed.
"""
import json

from wagtail.models import Site


def _fill(obj, base, language, translator, notes, where):
    """obj[base_language] = translation of obj[base] when empty (dict or model)."""
    get = obj.get if isinstance(obj, dict) else (lambda k, d=None: getattr(obj, k, d))
    source = (get(base) or "").strip()
    key = f"{base}_{language}"
    if not source or (get(key) or "").strip():
        return False
    value = translator.one(source)
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)
    notes.append(f"{where}: '{source}' → '{value}'")
    return True


def fill_settings(language, translator, dry_run=False):
    from core.site_settings import NavigationSettings, TeamSettings

    notes: list[str] = []
    for site in Site.objects.all():
        nav = NavigationSettings.for_site(site)
        raw = json.loads(json.dumps(list(nav.items.raw_data)))
        changed = False
        for item in raw:
            value = item.get("value") or {}
            changed |= _fill(value, "label", language, translator, notes, "menu")
            for group in value.get("groups") or []:
                gvalue = group.get("value", group)
                changed |= _fill(gvalue, "label", language, translator, notes, "menu group")
                for link in gvalue.get("links") or []:
                    changed |= _fill(link.get("value", link), "label", language, translator, notes, "menu link")
        changed |= _fill(nav, "cta_label", language, translator, notes, "header button")
        if changed and not dry_run:
            nav.items = raw
            nav.save()

        team = TeamSettings.for_site(site)
        for member in team.members.all():
            touched = False
            for base in ("role", "bio", "department"):
                touched |= _fill(member, base, language, translator, notes, f"team · {member.name}")
            if touched and not dry_run:
                member.save()

    # Chatbot answers (Snippets → Voci chatbot)
    from chatbot.models import ChatbotEntry
    for entry in ChatbotEntry.objects.all():
        if _fill(entry, "answer", language, translator, notes, f"chatbot · {entry}") and not dry_run:
            entry.save()
    return notes
