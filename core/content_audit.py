"""
Content check before go-live (and any time after): finds what an editor
still has to do, with a link to fix each item.

    python manage.py check_content            # full list
    python manage.py check_content --summary  # counts only

The same list is in the CMS: Rapporti → Controllo contenuti.

Groups, most urgent first:
  placeholders   test values and parts still to complete ("test", "lorem
                 ipsum", "MODIFICATO", [DA COMPLETARE], example.com, an
                 invalid VAT number…)
  old_links      links to the old WordPress site (www.axatel.it/…), which
                 stop working when the domain moves here
  menu           menu entries pointing to a page that is deleted or not
                 published
  coming_soon    published pages without content (visitors see "In arrivo"):
                 write them or hide them from the menu
  cards          missing card text or picture (lists, homepage, chatbot)
  drafts         changes saved but not published, pages never published
  translations   Italian pages without an English/French version online
  settings       menu labels, team, chatbot answers still without EN/FR;
                 form recipients, legal pages
  images         pictures whose only description is a file name
  seo            pages without a description for Google (recommended)

Read-only: it never changes anything.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from django.db import models
from django.urls import reverse

GROUPS = [
    ("placeholders", "Valori di prova o da completare",
     "Testi di prova, parti tra parentesi quadre da completare, indirizzi di esempio, partita IVA non valida."),
    ("old_links", "Link al vecchio sito",
     "Indirizzi www.axatel.it/… del sito WordPress: smetteranno di funzionare quando il dominio passerà a questo sito. "
     "Usa il collegamento a una pagina (o un documento caricato in Documenti)."),
    ("menu", "Menu: link a pagine non disponibili",
     "Voci visibili che puntano a una pagina cancellata o non pubblicata."),
    ("coming_soon", "Pagine pubblicate senza contenuto",
     "I visitatori vedono \"In arrivo\". Scrivi il contenuto, oppure spegni \"Visibile\" sulla voce di menu."),
    ("cards", "Testo o immagine della card mancante",
     "Usati negli elenchi, nella homepage e nelle risposte del chatbot."),
    ("drafts", "Modifiche non pubblicate",
     "Bozze salvate ma non ancora online: pubblicale o annullale."),
    ("translations", "Pagine non tradotte",
     "La versione inglese o francese non è online: chi cambia lingua vede il testo italiano con un avviso."),
    ("settings", "Impostazioni da completare",
     "Etichette del menu, team, risposte del chatbot senza traduzione; destinatari dei moduli; pagine legali."),
    ("images", "Immagini senza descrizione",
     "Il titolo sembra il nome di un file: scrivi una descrizione (testo alternativo per chi non vede l'immagine e per Google)."),
    ("seo", "Descrizione per Google mancante (consigliato)",
     "Tab Promuovi → Descrizione per i motori di ricerca, oppure il testo breve della card."),
]
GROUP_LABELS = {key: label for key, label, _ in GROUPS}

# What each page type shows on its card: (text field, image field).
CARD_FIELDS = {
    "monitoringpage": ("short_description", "cover_image"),
    "solutionpage": ("short_description", "cover_image"),
    "servicepage": ("short_description", None),
    "productpage": ("tagline", "cover_image"),
    "casosuccessopage": ("description", "cover_image"),
    "infopage": ("introduction", None),
}
# Pages whose body is their content (an empty one shows "In arrivo").
BODY_PAGES = {"monitoringpage", "solutionpage", "infopage", "flexpage", "servicepage", "casosuccessopage"}

SKIP_FIELDS = {"slug", "url_path", "draft_title", "path", "content_type", "locale", "translation_key",
               "latest_revision", "live_revision", "owner", "locked_by", "seo_title", "icon"}

PLACEHOLDER_WHOLE = re.compile(
    r"^\s*(test\w*|prova\d*|testo( di prova)?|titolo|sottotitolo|descrizione|asd\w*|qwerty|x{2,}|a{3,}|lorem|"
    r"todo|tbd|da fare|da completare|placeholder|esempio|sample|n/?a)\s*\d*\s*[.!]?\s*$", re.I)
PLACEHOLDER_ANY = [
    (re.compile(r"lorem ipsum|dolor sit amet", re.I), "testo segnaposto (lorem ipsum)"),
    (re.compile(r"\bMODIFICATO\b"), "testo di prova"),
    (re.compile(r"\b(TODO|FIXME|TBD)\b"), "nota da completare"),
    (re.compile(r"testo di prova|test test|asdf|qwerty|^(test|prova)\s*[:\-–]", re.I), "testo di prova"),
    (re.compile(r"[\w.+-]+@[\w-]+\.(test|invalid|example|local)\b|\bexample\.(com|org|it)\b", re.I),
     "indirizzo di esempio"),
    (re.compile(r"\b(0{6,}|1234567\d*)\b|\+39\s*0{3,}"), "numero di prova"),
    (re.compile(r"\[(?!\d+\])[^\[\]\n<>]{2,140}\]"), "parte tra parentesi quadre da completare"),
]
OLD_SITE = re.compile(r"(?:https?:)?//(?:www\.)?axatel\.it(?:/[^\s\"'<>)]*)?", re.I)
# Names used as examples in Italy ("Mario Rossi" = John Doe) and by the built-in team.
EXAMPLE_NAMES = re.compile(
    r"^(mario rossi|giuseppe verdi|luigi bianchi|marco bianchi|giulia bianchi|anna verdi|luca neri|paolo costa|"
    r"sara gallo|elena fontana|john doe|jane doe|nome cognome|\w+ persona)$", re.I)
FILE_LIKE = re.compile(
    r"^(img|image|dsc|dscn|pxl|photo|foto|screenshot|schermata|whatsapp|wp-|immagine|unnamed|untitled|download)"
    r"[\s_\-]*[\w\-]*$|^[\w\-]*\d{4,}[\w\-]*$|\.(jpe?g|png|webp|gif|svg)$|^[0-9a-f]{12,}$", re.I)


@dataclass
class Finding:
    group: str
    title: str
    detail: str
    url: str = ""
    language: str = ""
    extra: dict = field(default_factory=dict)


# ── helpers ──────────────────────────────────────────────────────────────

def _strip(html_text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_text or "")).strip()


def _leaves(value):
    """Every string inside a StreamField's JSON."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            if key in ("type", "id"):
                continue
            yield from _leaves(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _leaves(item)


def page_texts(page):
    """(field label, text) for every text field, StreamField and inline item of a page."""
    from wagtail.fields import RichTextField, StreamField

    for f in page._meta.concrete_fields:
        if f.name in SKIP_FIELDS or f.name.endswith("_ptr") or f.is_relation:
            continue
        label = str(getattr(f, "verbose_name", f.name))
        if isinstance(f, StreamField):
            try:
                data = json.loads(f.value_to_string(page) or "[]")
            except (TypeError, ValueError):
                continue
            for text in _leaves(data):
                yield label, text
        elif isinstance(f, (models.CharField, models.TextField, RichTextField)):
            value = getattr(page, f.name, "")
            if value:
                yield label, str(value)
    # Inline items (glossary terms, specification rows…)
    for relation in getattr(page._meta, "child_relations", []) or []:
        try:
            items = getattr(page, relation.get_accessor_name()).all()
        except Exception:  # noqa: BLE001
            continue
        for item in items:
            for f in item._meta.concrete_fields:
                if isinstance(f, (models.CharField, models.TextField)) and not f.is_relation:
                    value = getattr(item, f.name, "")
                    if value:
                        yield str(f.verbose_name), str(value)


def placeholder_problems(text: str, split: bool = False):
    """Problems in a text: "label: example" strings, or (label, example)
    pairs with split=True (one per occurrence)."""
    plain = _strip(text)
    found = []
    if plain and PLACEHOLDER_WHOLE.match(plain):
        found.append(("testo di prova", plain[:40]))
    for pattern, label in PLACEHOLDER_ANY:
        for match in pattern.finditer(plain):
            found.append((label, match.group(0)))
    if split:
        return found
    return [f"{label}: \"{example[:60]}\"" for label, example in found]


def old_links(text: str) -> list[str]:
    return [m.group(0) for m in OLD_SITE.finditer(text or "") if "@" not in text[max(0, m.start() - 1):m.start()]]


def valid_vat(value: str) -> bool:
    """Italian Partita IVA (11 digits with check digit)."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 11 or digits == "0" * 11:
        return False
    total = 0
    for i, ch in enumerate(digits[:10]):
        n = int(ch)
        if i % 2:
            n *= 2
            n = n - 9 if n > 9 else n
        total += n
    return (10 - total % 10) % 10 == int(digits[10])


def valid_tax_code(value: str) -> bool:
    code = re.sub(r"\s", "", value or "").upper()
    if re.fullmatch(r"\d{11}", code):
        return valid_vat(code)
    return bool(re.fullmatch(r"[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]", code))


def _edit(page) -> str:
    return reverse("wagtailadmin_pages:edit", args=[page.pk])


def _setting_url(model) -> str:
    try:
        return reverse("wagtailsettings:edit", args=[model._meta.app_label, model._meta.model_name])
    except Exception:  # noqa: BLE001
        return ""


def _snippet_url(obj) -> str:
    try:
        return reverse(f"wagtailsnippets_{obj._meta.app_label}_{obj._meta.model_name}:edit", args=[obj.pk])
    except Exception:  # noqa: BLE001
        return ""


def _is_empty_body(page) -> bool:
    body = getattr(page, "body", None)
    if body is None:
        return False
    if isinstance(body, str):
        return not _strip(body)
    try:
        return len(body) == 0
    except TypeError:
        return False


def _where(page) -> str:
    """The address on the site, as visitors see it (/en/… for English)."""
    try:
        path = page.get_url_parts()[2] or page.url_path
    except Exception:  # noqa: BLE001
        path = page.url_path
    language = page.locale.language_code
    return path if language == "it" else f"/{language}{path}"


# ── checks ───────────────────────────────────────────────────────────────

def _menu_pages():
    """Visible menu entries: [(label path, page id or None, custom url)]."""
    from wagtail.models import Site

    from .site_settings import NavigationSettings

    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
    if site is None:
        return [], None
    nav = NavigationSettings.for_site(site)
    entries = []
    stream = getattr(nav, "items", None) or getattr(nav, "menu_items", None) or []

    def visible(v):
        return v.get("visible") is None or bool(v.get("visible"))

    def page_id(v):
        p = v.get("page")
        return getattr(p, "pk", p)

    for block in stream:
        item = block.value
        if not visible(item):
            continue
        entries.append((item.get("label", ""), page_id(item), item.get("custom_url") or ""))
        for group in item.get("groups") or []:
            if not visible(group):
                continue
            for link in group.get("links") or []:
                if visible(link):
                    entries.append((f"{item.get('label')} › {group.get('label')} › {link.get('label')}",
                                    page_id(link), link.get("custom_url") or ""))
    return entries, nav


def run_audit() -> list[Finding]:
    from wagtail.images import get_image_model
    from wagtail.models import Locale, Page, Site

    findings: list[Finding] = []
    pages = (Page.objects.filter(depth__gt=1).exclude(content_type__model="page")
             .select_related("locale", "content_type").specific())
    pages = list(pages)
    italian = [p for p in pages if p.locale.language_code == "it"]
    other_locales = list(Locale.objects.exclude(language_code="it"))

    # Menu (used by coming_soon too)
    menu_entries, nav = _menu_pages()
    menu_page_ids = {pid for _, pid, _ in menu_entries if pid}
    by_id = {p.pk: p for p in pages}
    nav_url = _setting_url(type(nav)) if nav is not None else ""
    for label, pid, custom in menu_entries:
        if not pid and not custom and " › " in label:
            findings.append(Finding("menu", label, "nessuna pagina né indirizzo collegato", nav_url))
        if pid:
            target = by_id.get(pid)
            if target is None:
                findings.append(Finding("menu", label, "la pagina collegata non esiste più", nav_url))
            elif not target.live:
                findings.append(Finding("menu", label, f"la pagina \"{target.title}\" non è pubblicata", nav_url))
        for link in old_links(custom):
            findings.append(Finding("old_links", f"Menu: {label}", link, nav_url))

    for page in pages:
        kind = page.content_type.model
        language = page.locale.language_code
        url = _edit(page)
        name = f"{page.title} ({_where(page)})"

        # Drafts
        if page.live and page.has_unpublished_changes:
            findings.append(Finding("drafts", name, "modifiche salvate ma non pubblicate", url, language))
        elif not page.live and not page.alias_of_id:
            findings.append(Finding("drafts", name, "mai pubblicata", url, language))

        if page.alias_of_id:
            continue  # a mirror of the Italian page: checked there

        source = page
        if page.has_unpublished_changes:
            # Check what will go online next, not only what is online now.
            try:
                source = page.get_latest_revision_as_object()
            except Exception:  # noqa: BLE001
                source = page

        problems: dict[str, dict] = {}
        links: dict[str, set] = {}
        for label, text in page_texts(source):
            for kind_label, example in placeholder_problems(text, split=True):
                entry = problems.setdefault(kind_label, {"fields": [], "examples": []})
                if label not in entry["fields"]:
                    entry["fields"].append(label)
                if example and example not in entry["examples"]:
                    entry["examples"].append(example)
            for link in old_links(text):
                links.setdefault(link, set()).add(label)
        for kind_label, entry in problems.items():
            count = f" ({len(entry['examples'])})" if len(entry["examples"]) > 1 else ""
            examples = ", ".join(f"\"{e[:50]}\"" for e in entry["examples"][:3])
            findings.append(Finding("placeholders", name,
                                    f"{kind_label}{count}: {examples} — in: {', '.join(entry['fields'][:5])}",
                                    url, language))
        for link, labels in links.items():
            findings.append(Finding("old_links", name, f"{link} — in: {', '.join(sorted(labels)[:5])}", url, language))

        if not page.live:
            continue

        if kind in BODY_PAGES and _is_empty_body(page):
            in_menu = " — è nel menu" if page.pk in menu_page_ids or (
                page.get_translation_or_none(Locale.get_default()) and
                page.get_translation_or_none(Locale.get_default()).pk in menu_page_ids) else ""
            findings.append(Finding("coming_soon", name, f"nessun contenuto: il sito mostra \"In arrivo\"{in_menu}",
                                    url, language))

        if kind in CARD_FIELDS and language == "it":
            text_field, image_field = CARD_FIELDS[kind]
            missing = []
            if not (getattr(page, text_field, "") or "").strip():
                missing.append("testo breve")
            if image_field and not getattr(page, f"{image_field}_id", None):
                missing.append("immagine")
            if missing:
                findings.append(Finding("cards", name, "manca: " + ", ".join(missing), url, language))

        if language == "it" and page.depth > 2:
            meta = getattr(page, "get_meta_description", None)
            description = (meta() if callable(meta) else "") or page.search_description
            if not (description or "").strip():
                findings.append(Finding("seo", name, "nessuna descrizione", url, language))

    # Translations of live Italian pages
    for page in italian:
        if not page.live or page.depth <= 1:
            continue
        missing = []
        for locale in other_locales:
            translation = page.get_translation_or_none(locale)
            if translation is None:
                missing.append(f"{locale.language_code.upper()}: non esiste")
            elif translation.alias_of_id:
                missing.append(f"{locale.language_code.upper()}: copia italiana")
            elif not translation.live:
                missing.append(f"{locale.language_code.upper()}: bozza da pubblicare")
        if missing:
            findings.append(Finding("translations", f"{page.title} ({_where(page)})", "; ".join(missing),
                                    _edit(page), "it"))

    findings += _settings_findings(other_locales, menu_entries, nav)
    findings += _footer_findings()

    # Images
    Image = get_image_model()
    has_description = any(f.name == "description" for f in Image._meta.fields)
    for image in Image.objects.order_by("title"):
        if has_description and (image.description or "").strip():
            continue
        if FILE_LIKE.search((image.title or "").strip()):
            findings.append(Finding("images", image.title, "nessuna descrizione",
                                    reverse("wagtailimages:edit", args=[image.pk])))

    order = {key: i for i, (key, _, _) in enumerate(GROUPS)}
    findings.sort(key=lambda f: (order.get(f.group, 99), f.title.lower(), f.language))
    return findings


def _settings_findings(other_locales, menu_entries, nav) -> list[Finding]:
    from wagtail.models import Site

    from chatbot.models import ChatbotEntry

    from .notifications import recipients_for
    from .site_settings import FormNotificationSettings, TeamSettings

    findings = []
    codes = [l.language_code for l in other_locales]
    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()

    # Menu labels without translation
    if nav is not None and codes:
        stream = getattr(nav, "items", None) or getattr(nav, "menu_items", None) or []
        untranslated = []

        def check(value, path):
            if value.get("visible") is not None and not value.get("visible"):
                return
            for code in codes:
                if not (value.get(f"label_{code}") or "").strip():
                    untranslated.append(f"{path} ({code.upper()})")

        for block in stream:
            item = block.value
            if item.get("visible") is not None and not item.get("visible"):
                continue
            check(item, item.get("label", ""))
            for group in item.get("groups") or []:
                check(group, group.get("label", ""))
                if group.get("visible") is not None and not group.get("visible"):
                    continue
                for link in group.get("links") or []:
                    check(link, link.get("label", ""))
        if untranslated:
            findings.append(Finding("settings", "Navigazione",
                                    f"{len(untranslated)} etichette senza traduzione, es. " + ", ".join(untranslated[:4])
                                    + " → manage.py translate_settings, poi rileggi",
                                    _setting_url(type(nav))))

    # Team
    if site and codes:
        team = TeamSettings.for_site(site)
        for member in team.members.all():
            if not getattr(member, "visible", True):
                continue
            missing = [code.upper() for code in codes
                       if (member.role and not getattr(member, f"role_{code}", ""))
                       or (member.bio and not getattr(member, f"bio_{code}", ""))]
            if missing:
                findings.append(Finding("settings", f"Team: {member.name}",
                                        "ruolo o descrizione senza traduzione " + "/".join(missing),
                                        _setting_url(TeamSettings)))
            if EXAMPLE_NAMES.match((member.name or "").strip()):
                findings.append(Finding("placeholders", f"Team: {member.name}",
                                        "sembra un nome d'esempio: sostituisci con una persona reale o spegni Visibile",
                                        _setting_url(TeamSettings)))
            for problem in placeholder_problems(f"{member.name} {member.role} {member.bio}"):
                findings.append(Finding("placeholders", f"Team: {member.name}", problem, _setting_url(TeamSettings)))

    # Chatbot entries
    entries = list(ChatbotEntry.objects.all())
    if not any(e.is_fallback for e in entries):
        findings.append(Finding("settings", "Chatbot", "nessuna voce segnata come risposta di riserva", ""))
    untranslated = {code: [] for code in codes}
    for entry in entries:
        title = f"Voce chatbot: {entry.questions.splitlines()[0][:50] if entry.questions else entry.pk}"
        for code in codes:
            if hasattr(entry, f"answer_{code}") and not (getattr(entry, f"answer_{code}") or "").strip():
                untranslated[code].append(title.split(": ", 1)[1])
        for problem in placeholder_problems(entry.answer or ""):
            findings.append(Finding("placeholders", title, problem, _snippet_url(entry)))
    for code, names in untranslated.items():
        if names:
            try:
                url = reverse(f"wagtailsnippets_{ChatbotEntry._meta.app_label}_{ChatbotEntry._meta.model_name}:list")
            except Exception:  # noqa: BLE001
                url = ""
            findings.append(Finding("settings", "Voci chatbot",
                                    f"{len(names)} risposte senza traduzione {code.upper()}, es. "
                                    + ", ".join(f"\"{n}\"" for n in names[:3])
                                    + " → manage.py translate_settings, poi rileggi", url, code))

    # Form recipients
    if not recipients_for("contact"):
        findings.append(Finding("settings", "Notifiche moduli", "nessun destinatario per le richieste dal sito",
                                _setting_url(FormNotificationSettings)))
    return findings


def _footer_findings() -> list[Finding]:
    from wagtail.models import Site

    from .site_settings import FooterSettings

    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
    if site is None:
        return []
    footer = FooterSettings.for_site(site)
    url = _setting_url(FooterSettings)
    findings = []
    if re.sub(r"\D", "", footer.vat_value or "").startswith("1234567"):
        findings.append(Finding("placeholders", "Footer: Partita IVA", f"\"{footer.vat_value}\" è un numero di prova", url))
    elif footer.vat_value and not valid_vat(footer.vat_value):
        findings.append(Finding("placeholders", "Footer: Partita IVA", f"\"{footer.vat_value}\" non è una partita IVA valida", url))
    if not footer.vat_value:
        findings.append(Finding("placeholders", "Footer: Partita IVA", "vuota", url))
    if footer.tax_value and not valid_tax_code(footer.tax_value):
        findings.append(Finding("placeholders", "Footer: Codice Fiscale", f"\"{footer.tax_value}\" non è un codice fiscale valido", url))
    for block in footer.contacts:
        text = " ".join(str(v) for v in _leaves(dict(block.value)))
        for problem in placeholder_problems(text):
            findings.append(Finding("placeholders", "Footer: contatti", problem, url))
        for link in old_links(text):
            findings.append(Finding("old_links", "Footer: contatti", link, url))
    for kind, label in (("privacy", "Privacy policy"), ("cookie", "Cookie policy")):
        page = getattr(footer, f"{kind}_page")
        if page is None:
            findings.append(Finding("settings", f"Footer: {label}", "nessuna pagina collegata → manage.py create_legal_pages", url))
        elif not page.live:
            findings.append(Finding("settings", f"Footer: {label}", "la pagina è ancora una bozza", _edit(page)))
    return findings


def summary(findings: list[Finding]) -> list[tuple[str, str, str, int]]:
    counts = {}
    for f in findings:
        counts[f.group] = counts.get(f.group, 0) + 1
    return [(key, label, help_text, counts.get(key, 0)) for key, label, help_text in GROUPS]
