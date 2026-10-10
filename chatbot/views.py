import json
import logging
import random
from datetime import timedelta

from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny

from core.contact_views import client_ip

from .engine import engine
from .models import ChatbotEntry, ChatbotQuestion

logger = logging.getLogger(__name__)

RATE_LIMIT = 20  # questions per minute per visitor
RETENTION_DAYS = 180
NOT_READY = {
    "it": "Il chatbot non è configurato correttamente.",
    "en": "The chatbot is not set up yet.",
    "fr": "Le chatbot n'est pas encore configuré.",
}


SPECIAL_LABELS = {"unclear": "Domanda non chiara", "greeting": "Saluto", "thanks": "Ringraziamento"}


def _config():
    from wagtail.models import Site

    from core.site_settings import ChatbotSettings

    try:
        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        return ChatbotSettings.for_site(site) if site else None
    except Exception:  # noqa: BLE001 - the built-in behaviour is fine
        logger.exception("Chatbot settings unavailable")
        return None


def _special_reply(kind, language, config=None):
    """Greeting, thanks or "not understood" (chatbot/understanding.py): the
    texts of Impostazioni → Chatbot when filled in, else the built-in ones."""
    from .understanding import REPLIES

    text = ""
    config = config if config is not None else _config()
    if config is not None:
        if kind == "unclear":
            text = getattr(config, f"unclear_reply_{language}", "") or ""
        elif kind == "greeting" and language == "it":
            text = config.welcome_message or ""  # the CMS welcome text is Italian
    return text.strip() or REPLIES[kind][language]


def _fallback_reply(language):
    entry = ChatbotEntry.objects.filter(is_fallback=True, active=True).first()
    return entry.answer_in(language) if entry else NOT_READY[language]


def _log(question, language, reply, from_hint=False):
    try:
        meta = reply.get("meta") or {}
        kind = reply.get("kind") or ""
        key = reply.get("answer_key") or ""
        answer = engine.get_answer(key) if key else None
        entry_id = getattr(answer, "entry_id", None)
        if kind == "fallback":
            entry_id = ChatbotEntry.objects.filter(is_fallback=True).values_list("pk", flat=True).first()
        source = SPECIAL_LABELS.get(kind) or ("" if answer is None or answer.kind == "entry" else answer.label)
        ChatbotQuestion.objects.create(
            from_hint=from_hint,
            question=question[:300], language=language,
            entry_id=entry_id, source=(source or "")[:200],
            score=meta.get("passage_score") or meta.get("best_score") or 0,
            margin=meta.get("margin") or 0,
            answered=kind not in ("fallback", "unclear"),
            kind=kind[:20], answer_key=key[:60], in_context=bool(meta.get("in_context")),
        )
        if random.random() < 0.02:  # now and then, forget old questions
            ChatbotQuestion.objects.filter(created_at__lt=timezone.now() - timedelta(days=RETENTION_DAYS)).delete()
    except Exception:
        logger.exception("Could not log chatbot question")


def build_reply(query, language, context=None, key=None, config=None):
    """The engine's turn plus the texts from the CMS, as the chat receives it.
    Also used by the CMS test page (chatbot/admin_views.py)."""
    config = config if config is not None else _config()
    options = {}
    if config is not None:
        options = {
            "page_text": getattr(config, "page_text_answers", True),
            "related": getattr(config, "related_pages", True),
            "contact": getattr(config, "contact_button", True),
        }
    reply = engine.respond(query, language, context=context, options=options, key=key)
    kind = reply["kind"]
    if kind in SPECIAL_LABELS:
        reply["text"] = _special_reply(kind, language, config)
    elif not reply["text"]:
        reply["text"] = _fallback_reply(language)
    contact_path = ((getattr(config, "contact_path", "") if config is not None else "") or "/contatti").strip()
    for chip in reply["chips"]:
        if chip["type"] == "contact":
            chip["link"] = contact_path if contact_path.startswith("/") else "/" + contact_path
    return reply


@csrf_exempt
@api_view(['POST'])
# Public and anonymous. Without this, Django REST framework treats a browser
# that is logged in to the CMS on the same address as a session user and
# refuses the question ("CSRF Failed"): the chat then failed for editors only.
@authentication_classes([])
@permission_classes([AllowAny])
def chat(request):
    """One turn of the conversation.

    POST {"message", "locale", "key"?, "hint"?, "context"?}
      key:     answer of a question picked in a page suggestion or a button
      context: sent back as received with the previous answer
    → {"response", "link", "link_label", "chips": [{type, label, key?, link?}], "context"}
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
        query = (data.get("message") or "").strip()[:500]
        language = data.get("locale") if data.get("locale") in ("it", "en", "fr") else "it"
        if not query:
            return JsonResponse({"error": "Message parameter is required"}, status=400)

        # Each question costs CPU (the model runs on the server): keep a
        # single visitor from flooding it.
        rate_key = f"chatbot-rate:{client_ip(request)}"
        cache.add(rate_key, 0, timeout=60)
        try:
            count = cache.incr(rate_key)
        except ValueError:
            count = 1
        if count > RATE_LIMIT:
            return JsonResponse({"error": "Troppe domande in poco tempo: riprova tra un minuto."}, status=429)

        context = data.get("context") if isinstance(data.get("context"), dict) else None
        key = str(data.get("key") or "")[:100] or None
        reply = build_reply(query, language, context=context, key=key)
        if not request.headers.get("X-Smoke-Test"):
            _log(query, language, reply, bool(data.get("hint")))
        # link: the page the answer comes from (Italian path; the widget adds /en or /fr).
        return JsonResponse({
            "response": reply["text"], "link": reply["link"] or "", "link_label": reply.get("link_label") or "",
            "chips": reply["chips"], "context": reply["context"],
        })
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception:
        logger.exception("Chatbot failed to answer")
        return JsonResponse({"error": "Il chatbot non è disponibile in questo momento."}, status=500)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def hint(request):
    """The page suggestion for the chat bubble (chatbot/hints.py)."""
    from .hints import build_hint

    language = request.GET.get("locale") if request.GET.get("locale") in ("it", "en", "fr") else "it"
    try:
        return JsonResponse(build_hint(request.GET.get("path", "/"), language))
    except Exception:
        logger.exception("Chatbot hint failed")
        return JsonResponse({"enabled": False})
