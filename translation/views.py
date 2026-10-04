from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from wagtail.models import Locale, Page

from .models import LANGUAGES, TranslationJob


def request_translation(request, page_id):
    """Confirm and queue the translation of one Italian page."""
    page = get_object_or_404(Page, id=page_id).specific
    if not page.permissions_for_user(request.user).can_edit():
        raise PermissionDenied
    available = [(code, label) for code, label in LANGUAGES if Locale.objects.filter(language_code=code).exists()]

    if request.method == "POST":
        chosen = [code for code, _ in available if request.POST.get(code)]
        if chosen:
            publish = bool(request.POST.get("publish"))
            TranslationJob.objects.create(page=page, languages=",".join(chosen), requested_by=request.user,
                                          publish=publish)
            messages.success(
                request,
                f"Traduzione di '{page.title}' in coda ({', '.join(c.upper() for c in chosen)}). "
                + ("Tra uno o due minuti è online." if publish else
                   "Tra uno o due minuti trovi la bozza nella versione inglese/francese: rileggila e premi Pubblica."),
            )
        return redirect(reverse("wagtailadmin_pages:edit", args=[page.id]))

    pending = TranslationJob.objects.filter(page=page, status__in=["queued", "running"]).exists()
    return TemplateResponse(request, "translation/confirm.html", {
        "page": page, "languages": available, "pending": pending,
    })
