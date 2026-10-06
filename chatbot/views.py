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


def _special_reply(kind, language):
    """Greeting, thanks or "not understood" (chatbot/understanding.py): the
    texts of Impostazioni → Chatbot when filled in, else the built-in ones."""
    from wagtail.models import Site

    from core.site_settings import ChatbotSettings

    from .understanding import REPLIES

    text = ""
    try:
        site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        config = ChatbotSettings.for_site(site) if site else None
        if config is not None:
            if kind == "unclear":
                text = getattr(config, f"unclear_reply_{language}", "") or ""
            elif kind == "greeting" and language == "it":
                text = config.welcome_message or ""  # the CMS welcome text is Italian
    except Exception:  # noqa: BLE001 - the built-in text is fine
        logger.exception("Chatbot settings unavailable")
    return text.strip() or REPLIES[kind][language]


def _log(question, language, meta, from_hint=False):
    try:
        ChatbotQuestion.objects.create(
            from_hint=from_hint,
            question=question[:300], language=language,
            entry_id=meta.get("entry_id"), source=(meta.get("source") or "")[:200],
            score=meta.get("best_score", 0) or 0,
            margin=meta.get("margin", 0) or 0, answered=not meta.get("used_fallback", True),
        )
        if random.random() < 0.02:  # now and then, forget old questions
            ChatbotQuestion.objects.filter(created_at__lt=timezone.now() - timedelta(days=RETENTION_DAYS)).delete()
    except Exception:
        logger.exception("Could not log chatbot question")


@csrf_exempt
@api_view(['POST'])
# Public and anonymous. Without this, Django REST framework treats a browser
# that is logged in to the CMS on the same address as a session user and
# refuses the question ("CSRF Failed"): the chat then failed for editors only.
@authentication_classes([])
@permission_classes([AllowAny])
def chat(request):
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
        key = f"chatbot-rate:{client_ip(request)}"
        cache.add(key, 0, timeout=60)
        try:
            count = cache.incr(key)
        except ValueError:
            count = 1
        if count > RATE_LIMIT:
            return JsonResponse({"error": "Troppe domande in poco tempo: riprova tra un minuto."}, status=429)

        # A question picked in the page suggestion carries the key of its
        # answer (chatbot/hints.py): that exact answer, no guessing.
        key = str(data.get("key") or "")[:100]
        from_hint = bool(data.get("hint"))
        chosen = None
        if key:
            engine._ensure_loaded()
            chosen = engine.get_answer(key)
        if chosen is not None:
            answer, meta = chosen.answer_in("it"), {
                "best_score": 1.0, "margin": 0.0, "used_fallback": False, "answer_key": chosen.key,
                "entry_id": getattr(chosen, "entry_id", None),
                "source": "" if chosen.kind == "entry" else chosen.label, "link": chosen.link,
            }
        else:
            answer, meta = engine.answer_with_scores(query)
            chosen = engine.get_answer(meta.get("answer_key")) if meta.get("answer_key") else None
        if meta.get("special"):
            response = _special_reply(meta["special"], language)
            meta["source"] = SPECIAL_LABELS[meta["special"]]
        elif chosen is not None:
            response = chosen.answer_in(language)
        else:
            entry = ChatbotEntry.objects.filter(pk=meta.get("entry_id")).first() if meta.get("entry_id") else None
            response = entry.answer_in(language) if entry else (answer or engine._fallback or NOT_READY[language])
        if not request.headers.get("X-Smoke-Test"):
            _log(query, language, meta, from_hint)
        # link: the page the answer comes from (Italian path; the widget adds /en or /fr).
        return JsonResponse({"response": response, "link": meta.get("link") or ""})
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

