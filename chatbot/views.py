import json
import logging
import random
from datetime import timedelta

from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
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


def _log(question, language, meta):
    try:
        ChatbotQuestion.objects.create(
            question=question[:300], language=language,
            entry_id=meta.get("entry_id"), score=meta.get("best_score", 0) or 0,
            margin=meta.get("margin", 0) or 0, answered=not meta.get("used_fallback", True),
        )
        if random.random() < 0.02:  # now and then, forget old questions
            ChatbotQuestion.objects.filter(created_at__lt=timezone.now() - timedelta(days=RETENTION_DAYS)).delete()
    except Exception:
        logger.exception("Could not log chatbot question")


@csrf_exempt
@api_view(['POST'])
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

        answer, meta = engine.answer_with_scores(query)
        entry = ChatbotEntry.objects.filter(pk=meta.get("entry_id")).first() if meta.get("entry_id") else None
        response = entry.answer_in(language) if entry else (answer or engine._fallback or NOT_READY[language])
        if not request.headers.get("X-Smoke-Test"):
            _log(query, language, meta)
        return JsonResponse({"response": response})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception:
        logger.exception("Chatbot failed to answer")
        return JsonResponse({"error": "Il chatbot non è disponibile in questo momento."}, status=500)
