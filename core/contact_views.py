
from django.core.cache import cache
from django.core.mail import mail_admins
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
 
from .models import ContactSubmission
 
 
class ContactSubmitView(APIView):
    def post(self, request):
        data = request.data
        if data.get("website"):
            return Response({"received": True}, status=status.HTTP_201_CREATED)

        ip_address = request.META.get("REMOTE_ADDR", "unknown")
        rate_key = f"contact-submit:{ip_address}"
        if not cache.add(rate_key, True, timeout=60):
            return Response(
                {"detail": "Attendi un minuto prima di inviare un'altra richiesta."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
 
        if not name or not email:
            return Response(
                {"detail": "Nome ed email sono obbligatori."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        interests = data.getlist("interests") if hasattr(data, "getlist") else data.get("interests")
        interests = interests or []
        if not isinstance(interests, list):
            interests = []
 
        message = (data.get("message") or "").strip()
        if len(message) > 5000:
            return Response({"detail": "Il messaggio è troppo lungo."}, status=status.HTTP_400_BAD_REQUEST)

        attachment = request.FILES.get("attachment")
        if attachment and attachment.size > 10 * 1024 * 1024:
            return Response({"detail": "Il documento non può superare 10 MB."}, status=status.HTTP_400_BAD_REQUEST)

        submission = ContactSubmission(
            name=name,
            submission_type=(data.get("submission_type") or "contact"),
            company=(data.get("company") or "").strip(),
            email=email,
            phone=(data.get("phone") or "").strip(),
            interests=interests,
            message=message,
            attachment=attachment,
        )
        try:
            submission.full_clean()
            submission.save()
        except ValidationError:
            return Response({"detail": "Dati o documento non validi."}, status=status.HTTP_400_BAD_REQUEST)
 
        try:
            mail_admins(
                subject=f"Nuova richiesta contatto: {submission.name}",
                message=(
                    f"Nome: {submission.name}\n"
                    f"Azienda: {submission.company or '-'}\n"
                    f"Email: {submission.email}\n"
                    f"Telefono: {submission.phone or '-'}\n"
                    f"Tipo: {submission.get_submission_type_display()}\n"
                    f"Allegato: {submission.attachment.name if submission.attachment else '-'}\n"
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