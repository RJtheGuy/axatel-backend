
from django.core.cache import cache
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
 
from .models import ContactSubmission
 
 
def client_ip(request) -> str:
    """Real visitor IP. Behind nginx REMOTE_ADDR is always 127.0.0.1, so
    use the X-Real-IP header nginx sets (proxy_set_header X-Real-IP
    $remote_addr), then the first X-Forwarded-For entry."""
    real_ip = request.META.get("HTTP_X_REAL_IP", "").strip()
    if real_ip:
        return real_ip
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


from .notifications import QUOTE_DETAIL_FIELDS, confirm, notify  # noqa: E402

CONSENT_VALUES = {"1", "true", "on", "yes", "si", "sì"}


class ContactSubmitView(APIView):
    # Public and anonymous: a browser logged in to the CMS on the same
    # address must not be asked for a CSRF token (forms failed for editors).
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        if data.get("website"):
            return Response({"received": True}, status=status.HTTP_201_CREATED)

        # GDPR: the visitor must accept the privacy notice (checkbox on every form).
        # Checked before the one-a-minute limit, so a refused send can be retried.
        if str(data.get("privacy") or "").strip().lower() not in CONSENT_VALUES:
            return Response(
                {"detail": "Per inviare la richiesta accetta l'informativa privacy."},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        ip_address = client_ip(request)
        rate_key = f"contact-submit:{ip_address}"
        if not cache.add(rate_key, True, timeout=60):
            return Response(
                {"detail": "Attendi un minuto prima di inviare un'altra richiesta."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        language = data.get("locale") if data.get("locale") in ("it", "en", "fr") else "it"

        phone = (data.get("phone") or "").strip()
        if not name or not (email or phone):
            return Response(
                {"detail": "Inserisci il nome e almeno un recapito: e-mail o telefono."},
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

        # Quote requests: a few extra short answers, stored as details.
        details = {}
        for key in QUOTE_DETAIL_FIELDS:
            value = (data.get(f"details_{key}") or "").strip()
            if value:
                details[key] = value[:300]

        submission = ContactSubmission(
            name=name,
            submission_type=(data.get("submission_type") or "contact"),
            details=details,
            company=(data.get("company") or "").strip(),
            email=email,
            phone=phone,
            interests=interests,
            message=message,
            attachment=attachment,
            language=language,
            privacy_consent=True,
            consent_text=(data.get("consent_text") or "").strip()[:400],
        )
        try:
            submission.full_clean()
            submission.save()
        except ValidationError:
            return Response({"detail": "Dati o documento non validi."}, status=status.HTTP_400_BAD_REQUEST)
 
        # E-mails are a courtesy on top of the saved request: their outcome is
        # recorded on it (Richieste di contatto) and never fails the form.
        try:
            notify(submission)
            confirm(submission)
        except Exception:  # noqa: BLE001
            pass

        return Response({"received": True}, status=status.HTTP_201_CREATED)