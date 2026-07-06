from django.contrib import admin
from .models import Interaction


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("company", "interaction_type", "contact_name", "date", "outcome", "follow_up_date")
    list_filter = ("interaction_type", "outcome")
    search_fields = ("company__business_name", "contact_name", "notes")
    date_hierarchy = "date"