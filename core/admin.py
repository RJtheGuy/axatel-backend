from django.contrib import admin, messages

from .models import ContactSubmission
from .notifications import notify


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("name", "submission_type", "email", "company", "language", "e_mail_sent", "created_at")
    list_filter = ("submission_type", "language", "created_at")
    search_fields = ("name", "email", "company", "message")
    readonly_fields = [f.name for f in ContactSubmission._meta.fields]
    actions = ["send_again"]

    @admin.display(description="E-mail", boolean=True)
    def e_mail_sent(self, obj):
        if obj.notified_at:
            return True
        return False if obj.notify_error else None

    @admin.action(description="Invia di nuovo la notifica e-mail")
    def send_again(self, request, queryset):
        sent = sum(1 for submission in queryset if notify(submission))
        failed = queryset.count() - sent
        self.message_user(request, f"{sent} notifiche inviate.", messages.SUCCESS)
        if failed:
            self.message_user(request, f"{failed} non inviate: vedi 'Errore di invio' nella richiesta.", messages.WARNING)
