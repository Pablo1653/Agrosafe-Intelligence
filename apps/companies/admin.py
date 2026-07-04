from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):

    list_display = (
        "business_name",
        "trade_name",
        "city",
        "industry",
        "status",
    )

    search_fields = (
        "business_name",
        "trade_name",
        "cuit",
    )

    list_filter = (
        "status",
        "industry",
    )

    ordering = (
        "business_name",
    )