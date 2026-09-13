import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .engine import engine

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        query = (data.get("message") or "").strip()

        if not query:
            return JsonResponse({"error": "Message parameter is required"}, status=400)

        answer = engine.answer(query)
        fallback = engine._fallback or "Il chatbot non è configurato correttamente."
        response = answer or fallback
        return JsonResponse({"response": response})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)