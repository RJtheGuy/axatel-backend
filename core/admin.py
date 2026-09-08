
from django.contrib import admin
from .models import ContactSubmission
 
 
@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "company", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "email", "company", "message")
    readonly_fields = [f.name for f in ContactSubmission._meta.fields]
 