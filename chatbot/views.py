import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .engine import engine


@csrf_exempt
def chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        query = data.get("message", "").strip()

        if not query:
            return JsonResponse({"error": "Message parameter is required"}, status=400)

        answer = engine.answer(query)
        return JsonResponse({"response": answer})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)