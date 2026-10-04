"""
Chatbot knowledge built from the published site, so the bot knows every
monitoring topic, product, solution, success story, glossary term and FAQ
question without anyone copying them into Snippets → Voci chatbot.

Each published Italian page gives one answer: a few ways of asking about it
(Italian, plus the page's English/French titles) and its short description,
with a link to the page. Two list answers are built too: "Cosa monitorate?"
(the published topics by area) and "Quali prodotti avete?".

English/French answers come from the translated pages; a page not translated
yet answers in Italian. Unpublished pages are left out. The engine rebuilds
this within a minute of any publish or unpublish (see engine.py).

Entries written by hand in Voci chatbot always win over these (engine.py).
"""
import html
import re
from dataclasses import dataclass, field

from wagtail.models import Locale

LANGS = ("it", "en", "fr")

AREAS = {  # MonitoringPage.category → label per language
    "ambiente": {"it": "Ambiente", "en": "Environment", "fr": "Environnement"},
    "viabilita": {"it": "Viabilità", "en": "Roads", "fr": "Routes"},
    "strutture": {"it": "Strutture", "en": "Structures", "fr": "Ouvrages"},
}
AREA_ORDER = ["ambiente", "viabilita", "strutture"]

TOPICS_INTRO = {
    "it": "Ecco cosa monitoriamo:",
    "en": "This is what we monitor:",
    "fr": "Voici ce que nous surveillons :",
}
TOPICS_OUTRO = {
    "it": "Chiedimi di uno di questi ambiti per saperne di più.",
    "en": "Ask me about any of them to find out more.",
    "fr": "Demandez-moi l'un de ces domaines pour en savoir plus.",
}
PRODUCTS_INTRO = {
    "it": "I nostri prodotti:",
    "en": "Our products:",
    "fr": "Nos produits :",
}
PRODUCTS_OUTRO = {
    "it": "Chiedimi di uno di questi per una descrizione.",
    "en": "Ask me about any of them for a description.",
    "fr": "Demandez-moi l'un d'eux pour une description.",
}

TOPIC_LIST_QUESTIONS = [
    "cosa monitorate?", "cosa monitora Axatel?", "che cosa monitorate", "quali ambiti monitorate?",
    "che tipo di monitoraggio fate?", "quali fenomeni potete monitorare?", "cosa potete monitorare?",
    "di cosa vi occupate nel monitoraggio?", "elenco dei monitoraggi", "cosa misurate?",
    "what do you monitor?", "que surveillez-vous ?",
]
PRODUCT_LIST_QUESTIONS = [
    "quali prodotti avete?", "che prodotti vendete?", "elenco prodotti", "catalogo prodotti",
    "cosa vendete?", "quali dispositivi avete?", "what products do you have?", "quels produits avez-vous ?",
]


@dataclass
class SiteAnswer:
    key: str
    kind: str  # topic, product, solution, case, glossary, faq, list
    label: str  # shown in Domande al chatbot
    questions: list = field(default_factory=list)
    texts: dict = field(default_factory=dict)  # language → answer text
    link: str = ""  # Italian path; the widget adds /en or /fr
    titles: dict = field(default_factory=dict)  # language → page title (for evaluate_chatbot)

    def answer_in(self, language: str) -> str:
        return (self.texts.get(language) or "").strip() or self.texts.get("it", "")


def _plain(value) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _path(page) -> str:
    """The page's address on the site, without host and language."""
    url = page.url or ""
    url = re.sub(r"^https?://[^/]+", "", url)
    return url or "/"


def _translations(page) -> dict:
    """language → live, real (not alias) translation of an Italian page."""
    found = {"it": page}
    for language in ("en", "fr"):
        locale = Locale.objects.filter(language_code=language).first()
        if locale is None:
            continue
        other = page.get_translation_or_none(locale)
        if other is not None and other.live and not other.alias_of_id:
            found[language] = other.specific
    return found


def _texts(versions: dict, getter) -> dict:
    out = {}
    for language, page in versions.items():
        value = _plain(getter(page))
        if value:
            out[language] = value
    return out


def _titles(versions: dict) -> list:
    return [p.title for p in versions.values() if p.title]


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _short_topic(title: str) -> str:
    return re.sub(r"^(monitoraggio|surveillance( des| du| de la)?)\s+|\s+monitoring$", "", title.strip(), flags=re.I)


def _italian_live(model):
    return model.objects.live().filter(locale__language_code="it").specific().order_by("path")


def build() -> list[SiteAnswer]:
    """Every answer the published site gives. Safe to call often (a few queries)."""
    answers: list[SiteAnswer] = []
    answers += _topics()
    answers += _products()
    answers += _simple("solutions.SolutionPage", "solution", "Soluzione",
                       lambda p: p.short_description or p.search_description,
                       lambda p: [f"cos'è {p.title}?", f"cosa offrite per {p.title}?", p.eyebrow])
    answers += _simple("casi.CasoSuccessoPage", "case", "Caso di successo",
                       lambda p: p.description or p.search_description,
                       lambda p: [f"progetto {p.client}" if p.client else "", f"caso di successo {p.title}",
                                  f"cosa avete fatto per {p.client}?" if p.client else ""])
    # A glossary term that is also a page (LoRaWAN, SCADA, Firmware…) would
    # tie with that page and send the fallback: its questions go to the page.
    by_name = {}
    for answer in answers:
        for title in answer.titles.values():
            by_name.setdefault(title.strip().lower(), answer)
    for term in _glossary():
        page = by_name.get(term.label.split(": ", 1)[-1].strip().lower())
        if page is not None:
            page.questions += term.questions
        else:
            answers.append(term)
    answers += _faqs()
    for answer in answers:
        seen, clean = set(), []
        for question in answer.questions:
            question = (question or "").strip()
            if question and question.lower() not in seen:
                seen.add(question.lower())
                clean.append(question)
        answer.questions = clean
    return [a for a in answers if a.questions and a.texts.get("it")]


def _model(label):
    from django.apps import apps
    try:
        return apps.get_model(label)
    except LookupError:
        return None


def _topics() -> list[SiteAnswer]:
    model = _model("monitoring.MonitoringPage")
    if model is None:
        return []
    out, by_area = [], {}
    for page in _italian_live(model):
        versions = _translations(page)
        name = _short_topic(page.title)
        texts = _texts(versions, lambda p: p.short_description or p.search_description)
        questions = [page.title, f"monitorate {name}?", f"monitoraggio {name}", f"come monitorate {name}?",
                     f"sistemi per monitorare {name}", *(_titles(versions))]
        out.append(SiteAnswer(f"topic:{page.pk}", "topic", f"Monitoraggio: {page.title}", questions, texts, _path(page),
                              {lang: p.title for lang, p in versions.items()}))
        key = re.sub(r"[^a-z]", "", (page.category or "").lower().replace("à", "a")) or "altro"
        by_area.setdefault(key, []).append({lang: _short_topic(p.title) for lang, p in versions.items()})
    if by_area:
        texts = {}
        for language in LANGS:
            lines = [TOPICS_INTRO[language]]
            for key in AREA_ORDER + sorted(k for k in by_area if k not in AREA_ORDER):
                if key not in by_area:
                    continue
                label = AREAS.get(key, {}).get(language) or key.capitalize()
                names = sorted(_cap(n.get(language) or n["it"]) for n in by_area[key])
                lines.append(f"• {label}: {', '.join(names)}")
            lines.append(TOPICS_OUTRO[language])
            texts[language] = "\n".join(lines)
        index = model.objects.live().filter(locale__language_code="it").first()
        link = _path(index.get_parent()) if index else "/monitoraggio/"
        out.append(SiteAnswer("list:topics", "list", "Elenco: cosa monitoriamo", TOPIC_LIST_QUESTIONS, texts, link))
    return out


def _products() -> list[SiteAnswer]:
    model = _model("products.ProductPage")
    if model is None:
        return []
    out, names = [], []
    for page in _italian_live(model):
        versions = _translations(page)
        texts = _texts(versions, lambda p: p.tagline or p.search_description)
        questions = [page.title, f"cos'è {page.title}?", f"cosa fa {page.title}?", f"a cosa serve {page.title}?",
                     f"scheda tecnica {page.title}", page.model_code, *(_titles(versions))]
        out.append(SiteAnswer(f"product:{page.pk}", "product", f"Prodotto: {page.title}", questions, texts, _path(page),
                              {lang: p.title for lang, p in versions.items()}))
        names.append({lang: p.title for lang, p in versions.items()})
    if names:
        texts = {}
        for language in LANGS:
            listed = ", ".join(sorted(n.get(language) or n["it"] for n in names))
            texts[language] = f"{PRODUCTS_INTRO[language]} {listed}.\n{PRODUCTS_OUTRO[language]}"
        first = model.objects.live().filter(locale__language_code="it").first()
        link = _path(first.get_parent()) if first else "/prodotti/"
        out.append(SiteAnswer("list:products", "list", "Elenco: prodotti", PRODUCT_LIST_QUESTIONS, texts, link))
    return out


def _simple(label, kind, prefix, text_of, more_questions) -> list[SiteAnswer]:
    model = _model(label)
    if model is None:
        return []
    out = []
    for page in _italian_live(model):
        versions = _translations(page)
        texts = _texts(versions, text_of)
        questions = [page.title, *more_questions(page), *(_titles(versions))]
        out.append(SiteAnswer(f"{kind}:{page.pk}", kind, f"{prefix}: {page.title}", questions, texts, _path(page),
                              {lang: p.title for lang, p in versions.items()}))
    return out


def _glossary() -> list[SiteAnswer]:
    model = _model("home.GlossaryPage")
    if model is None:
        return []
    out = []
    for page in _italian_live(model):
        versions = _translations(page)
        terms = {lang: list(p.terms.all()) for lang, p in versions.items()}
        for position, term in enumerate(terms["it"]):
            texts = {"it": _plain(term.definition)}
            for language in ("en", "fr"):
                other = terms.get(language) or []
                if len(other) == len(terms["it"]) and _plain(other[position].definition):
                    texts[language] = _plain(other[position].definition)
            aliases = [a.strip() for a in (term.aliases or "").split(",") if a.strip()]
            questions = [term.term, f"cos'è {term.term}?", f"cosa significa {term.term}?", *aliases]
            out.append(SiteAnswer(f"glossary:{term.pk}", "glossary", f"Glossario: {term.term}", questions, texts, _path(page)))
    return out


def _faq_items(page):
    body = getattr(page, "body", None)
    if body is None or not hasattr(body, "raw_data"):
        return []
    items = []
    for block in body.raw_data:
        if block.get("type") != "faq":
            continue
        for item in (block.get("value") or {}).get("items") or []:
            value = item.get("value", item)
            if value.get("question") and value.get("answer"):
                items.append((value["question"], value["answer"]))
    return items


def _faqs() -> list[SiteAnswer]:
    from wagtail.models import Page

    out = []
    for page in Page.objects.live().filter(locale__language_code="it").specific().order_by("path"):
        italian = _faq_items(page)
        if not italian:
            continue
        versions = _translations(page)
        translated = {lang: _faq_items(p) for lang, p in versions.items() if lang != "it"}
        for position, (question, answer) in enumerate(italian):
            texts = {"it": _plain(answer)}
            questions = [question]
            for language, items in translated.items():
                if len(items) == len(italian):
                    texts[language] = _plain(items[position][1])
                    questions.append(items[position][0])
            out.append(SiteAnswer(f"faq:{page.pk}:{position}", "faq", f"FAQ: {question[:80]}", questions, texts, _path(page)))
    return out


def signature():
    """Changes whenever a page is published, unpublished or deleted."""
    from django.db.models import Count, Max
    from wagtail.models import Page

    row = Page.objects.live().aggregate(n=Count("id"), last=Max("last_published_at"))
    return (row["n"], row["last"])
