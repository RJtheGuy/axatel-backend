"""
Page suggestions for the chat ("nuvoletta" above the chat button).

GET /api/v2/chatbot/hint/?path=/monitoraggio/frane&locale=it
→ {"enabled": true, "delay": 20, "text": "Vuoi saperne di più su Monitoraggio frane?",
   "questions": [{"label": "Come monitorate le frane?", "key": "topic:12"}, …],
   "contact": true}

Where the questions come from, first match wins:
1. Chatbot → Suggerimenti, an entry for that address.
2. The published page itself, as the chatbot already knows it
   (site_knowledge.py): one question about the page (topic, product,
   solution, case study, list page) and up to two of its FAQs. Each carries
   the answer's key, so clicking it gives exactly that answer.
3. Any other page: a generic text and the "Domande suggerite" of
   Impostazioni → Chatbot.

Reads the database only (no language model), and is cached for a minute
together with the site knowledge signature, so it is cheap to call.
"""
from __future__ import annotations

import re

from django.core.cache import cache

LANGS = ("it", "en", "fr")

GENERIC_TEXT = {
    "it": "Hai una domanda? Chiedi pure, rispondo subito.",
    "en": "Have a question? Ask away, I answer straight away.",
    "fr": "Une question ? Posez-la, je réponds tout de suite.",
}
GENERIC_QUESTIONS = {
    "it": ["Cosa monitorate?", "Quali prodotti avete?", "Come posso contattarvi?"],
    "en": ["What do you monitor?", "What products do you have?", "How can I contact you?"],
    "fr": ["Que surveillez-vous ?", "Quels produits proposez-vous ?", "Comment vous contacter ?"],
}
# One question per kind of page, in the visitor's language. {title} = the
# page title in that language (topics: without "Monitoraggio").
TEMPLATES = {
    "topic": {"it": "Come funziona il {title}?", "en": "How does {title} work?",
              "fr": "Comment fonctionne la {title} ?"},
    "product": {"it": "Cos'è {title} e a cosa serve?", "en": "What is {title} and what is it for?",
                "fr": "Qu'est-ce que {title} et à quoi sert-il ?"},
    "solution": {"it": "Cosa offrite per {title}?", "en": "What do you offer for {title}?",
                 "fr": "Que proposez-vous pour {title} ?"},
    "case": {"it": "Raccontami il progetto {title}", "en": "Tell me about the {title} project",
             "fr": "Parlez-moi du projet {title}"},
    "service": {"it": "Cosa comprende il servizio {title}?", "en": "What does the {title} service include?",
                "fr": "Que comprend le service {title} ?"},
}
LIST_LABELS = {
    "list:topics": {"it": "Cosa monitorate?", "en": "What do you monitor?", "fr": "Que surveillez-vous ?"},
    "list:products": {"it": "Quali prodotti avete?", "en": "What products do you have?",
                      "fr": "Quels produits proposez-vous ?"},
}


def normalise(path: str) -> str:
    path = (path or "/").split("?")[0].split("#")[0]
    path = re.sub(r"^/(en|fr)(?=/|$)", "", path)
    return "/" + path.strip("/") if path.strip("/") else "/"


def _settings():
    from wagtail.models import Site

    from core.site_settings import ChatbotSettings

    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
    return ChatbotSettings.for_site(site) if site else None


def _site_answers():
    """Site knowledge grouped by page address, rebuilt when the site changes."""
    from . import site_knowledge

    signature = site_knowledge.signature()
    cached = cache.get("chatbot-hint-pages")
    if cached and cached[0] == signature:
        return cached[1]
    by_path: dict[str, list] = {}
    for answer in site_knowledge.build():
        by_path.setdefault(normalise(answer.link), []).append(answer)
    cache.set("chatbot-hint-pages", (signature, by_path), 3600)
    return by_path


def _excluded(path: str, rules: str) -> bool:
    for line in (rules or "").splitlines():
        rule = normalise(line.strip()) if line.strip() else ""
        if rule and (path == rule or (rule != "/" and path.startswith(rule + "/"))):
            return True
    return False


def _short(title: str) -> str:
    return re.sub(r"^(monitoraggio|surveillance( des| du| de la| de l')?)\s+|\s+monitoring$", "",
                  title.strip(), flags=re.I)


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text and not text[:2].isupper() else text


def _question(kind: str, language: str, title: str) -> str:
    if kind == "topic":
        # "Monitoraggio frane" → "Come funziona il monitoraggio frane?";
        # a title not starting that way: "Come monitorate <name>?".
        lowered = _lower_first(title)
        starts = {"it": "monitoraggio", "en": "", "fr": "surveillance"}[language]
        if language == "en" or lowered.lower().startswith(starts):
            return TEMPLATES["topic"][language].format(title=lowered)
        other = {"it": "Come monitorate {title}?", "fr": "Comment surveillez-vous {title} ?"}[language]
        return other.format(title=_lower_first(_short(title)))
    return TEMPLATES[kind][language].format(title=title)


def build_hint(path: str, language: str) -> dict:
    language = language if language in LANGS else "it"
    path = normalise(path)
    config = _settings()
    if config is None or not config.enabled or not config.hints_enabled or _excluded(path, config.hint_excluded):
        return {"enabled": False}
    delay = max(5, int(config.hint_delay or 20))
    template = (getattr(config, f"hint_text_{language}", "") or "").strip() or (
        config.hint_text_it if language == "it" else "")

    # 1. Written for this page in the CMS.
    from .models import ChatbotHint

    custom = ChatbotHint.objects.filter(path=path, active=True).first()
    if custom and custom.questions_in(language):
        return {
            "enabled": True, "delay": delay, "contact": True,
            "text": custom.text_in(language) if language == "it" or getattr(custom, f"text_{language}")
            else GENERIC_TEXT[language],
            "questions": [{"label": q} for q in custom.questions_in(language)],
        }

    # 2. Made from the page itself.
    answers = _site_answers().get(path, [])
    # A page not translated yet would put an Italian title in an English or
    # French sentence: such a page gets the generic suggestion instead.
    main = next((a for a in answers if a.kind in TEMPLATES and (language == "it" or a.titles.get(language))), None)
    lists = [a for a in answers if a.key in LIST_LABELS]
    faqs = [a for a in answers if a.kind == "faq" and (a.labels.get(language) or language == "it")]
    questions, title = [], ""
    if main is not None:
        title = (main.titles.get(language) or main.titles.get("it") or "").strip()
        questions.append({"label": _question(main.kind, language, title), "key": main.key})
    for answer in lists:
        questions.append({"label": LIST_LABELS[answer.key][language], "key": answer.key})
    for answer in faqs:
        if len(questions) >= 3:
            break
        questions.append({"label": answer.labels.get(language) or answer.labels.get("it"), "key": answer.key})
    if custom:  # text written in the CMS, questions made from the page
        text = custom.text_in(language) if language == "it" or getattr(custom, f"text_{language}") else ""
    else:
        text = ""
    if not text:
        text = template.replace("{title}", title) if title and template and "{title}" in template else ""
    if questions:
        return {"enabled": True, "delay": delay, "contact": True,
                "text": text or GENERIC_TEXT[language], "questions": questions[:3]}

    # 3. Any other page.
    suggestions = []
    if language == "it":
        suggestions = [str(block.value).strip() for block in (config.suggestions or []) if str(block.value).strip()]
    suggestions = suggestions or GENERIC_QUESTIONS[language]
    return {"enabled": True, "delay": delay, "contact": True, "text": text or GENERIC_TEXT[language],
            "questions": [{"label": q} for q in suggestions[:3]]}
