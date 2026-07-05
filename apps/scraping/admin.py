from django.contrib import admin
from .models import RawCompany


@admin.register(RawCompany)
class RawCompanyAdmin(admin.ModelAdmin):
    list_display = ("business_name", "source", "status", "cuit", "city", "created_at")
    list_filter = ("source", "status")
    search_fields = ("business_name", "trade_name", "cuit")
    readonly_fields = ("raw_data", "created_at", "updated_at")