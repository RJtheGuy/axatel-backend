"""
CMS → Chatbot → Prova il chatbot.

Ask questions as a visitor would, follow-ups included (the conversation is
kept in the form), and see why the bot answered as it did. Below: what was
asked in the last 30 days, and the questions most often left unanswered,
each with "Crea risposta". Questions asked here are not logged.
"""
import json
from collections import Counter
from datetime import timedelta
from urllib.parse import quote

from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .models import ChatbotQuestion

KIND_LABELS = dict(ChatbotQuestion._meta.get_field("kind").choices)
KIND_HELP = {
    "entry": "Una Voce chatbot scritta a mano.",
    "page": "La descrizione di una pagina del sito (con il paragrafo più vicino alla domanda, se c'è).",
    "passage": "Un paragrafo di una pagina del sito che risponde alla domanda.",
    "context": "Ha tenuto conto della domanda precedente.",
    "more": "Il paragrafo successivo della pagina di cui si parlava.",
    "clarify": "Due risposte erano ugualmente vicine: chiede quale.",
    "fallback": "Nessuna risposta abbastanza vicina: risposta di riserva.",
    "greeting": "Un saluto.", "thanks": "Un ringraziamento.", "unclear": "Messaggio senza senso o troppo vago.",
}


def _stats():
    since = timezone.now() - timedelta(days=30)
    recent = ChatbotQuestion.objects.filter(created_at__gte=since)
    total = recent.count()
    by_kind = {row["kind"] or "": row["n"] for row in recent.values("kind").annotate(n=Count("id"))}
    answered = recent.filter(answered=True).count()
    missed = Counter()
    sample = {}
    unanswered_rows = recent.filter(answered=False).exclude(kind="unclear").exclude(source="Domanda non chiara")
    for question in unanswered_rows.values_list("question", flat=True)[:2000]:
        key = " ".join(question.lower().split()).strip(" ?!.")
        missed[key] += 1
        sample.setdefault(key, question)
    add = reverse("wagtailsnippets_chatbot_chatbotentry:add")
    unanswered = [{"question": sample[k], "count": n, "create": f"{add}?domanda={quote(sample[k])}"}
                  for k, n in missed.most_common(15)]
    return {
        "total": total,
        "answered_pct": round(100 * answered / total) if total else 0,
        "kinds": [(KIND_LABELS.get(k, k or "Prima di questo aggiornamento"), n) for k, n in sorted(by_kind.items(), key=lambda kv: -kv[1])],
        "unanswered": unanswered,
        "context_pct": round(100 * recent.filter(in_context=True).count() / total) if total else 0,
    }


def test_view(request):
    from .views import build_reply

    language = request.POST.get("language") or request.GET.get("language") or "it"
    language = language if language in ("it", "en", "fr") else "it"
    try:
        history = json.loads(request.POST.get("history") or "[]")
        context = json.loads(request.POST.get("context") or "{}")
    except ValueError:
        history, context = [], {}
    if request.POST.get("reset"):
        history, context = [], {}
    question = (request.POST.get("question") or "").strip()[:500]
    key = (request.POST.get("key") or "").strip() or None
    if request.method == "POST" and question and not request.POST.get("reset"):
        reply = build_reply(question, language, context=context, key=key)
        meta = reply.get("meta") or {}
        history.append({
            "question": question,
            "text": reply["text"],
            "link": reply["link"],
            "kind": KIND_LABELS.get(reply["kind"], reply["kind"]),
            "kind_help": KIND_HELP.get(reply["kind"], ""),
            "chips": reply["chips"],
            "details": ", ".join(f"{k}: {v}" for k, v in meta.items() if v not in (None, "", False)),
        })
        context = reply["context"]
    return render(request, "chatbot/admin/test.html", {
        "history": history[-12:],
        "history_json": json.dumps(history[-12:]),
        "context_json": json.dumps(context),
        "language": language,
        "languages": [("it", "Italiano"), ("en", "English"), ("fr", "Français")],
        "stats": _stats(),
        "questions_url": reverse("wagtailsnippets_chatbot_chatbotquestion:list"),
    })
