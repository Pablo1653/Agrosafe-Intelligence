from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("__str__", "company", "position", "email", "mobile", "is_primary", "is_active")
    list_filter = ("is_primary", "is_active")
    search_fields = ("first_name", "last_name", "email", "company__business_name")