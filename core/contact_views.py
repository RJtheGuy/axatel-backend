
from django.core.mail import mail_admins
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
 
from .models import ContactSubmission
 
 
class ContactSubmitView(APIView):
    def post(self, request):
        data = request.data
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
 
        if not name or not email:
            return Response(
                {"detail": "Nome ed email sono obbligatori."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        interests = data.get("interests") or []
        if not isinstance(interests, list):
            interests = []
 
        submission = ContactSubmission.objects.create(
            name=name,
            company=(data.get("company") or "").strip(),
            email=email,
            phone=(data.get("phone") or "").strip(),
            interests=interests,
            message=(data.get("message") or "").strip(),
        )
 
        try:
            mail_admins(
                subject=f"Nuova richiesta contatto: {submission.name}",
                message=(
                    f"Nome: {submission.name}\n"
                    f"Azienda: {submission.company or '-'}\n"
                    f"Email: {submission.email}\n"
                    f"Telefono: {submission.phone or '-'}\n"
                    f"Interessi: {', '.join(submission.interests) or '-'}\n\n"
                    f"Messaggio:\n{submission.message or '-'}"
                ),
                fail_silently=True,
            )
        except Exception:
            # Email is a courtesy notification, not the source of truth
            # — the ContactSubmission row above is already saved.
            pass
 
        return Response({"received": True}, status=status.HTTP_201_CREATED)