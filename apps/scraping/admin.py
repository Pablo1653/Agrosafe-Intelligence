from django.contrib import admin
from .models import RawCompany


@admin.register(RawCompany)
class RawCompanyAdmin(admin.ModelAdmin):
    list_display = ("business_name", "source", "status", "cuit", "city", "email", "created_at")
    list_filter = ("source", "status")
    search_fields = ("business_name", "trade_name", "cuit", "email")
    readonly_fields = ("raw_data", "created_at", "updated_at")