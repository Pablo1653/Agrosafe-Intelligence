from django import forms
from .models import Company


class CompanyForm(forms.ModelForm):
    """
    Form for creating and editing a Company.

    Only exposes the fields the user should fill in manually.
    Audit fields (company_uuid, created_at, updated_at, created_by)
    and is_active are handled elsewhere, not through this form.
    """

    class Meta:
        model = Company
        fields = [
            "business_name",
            "trade_name",
            "cuit",
            "website",
            "industry",
            "city",
            "status",
        ]
        widgets = {
            "business_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Razón social"}),
            "trade_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre comercial"}),
            "cuit": forms.TextInput(attrs={"class": "form-control", "placeholder": "30-12345678-9"}),
            "website": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "industry": forms.TextInput(attrs={"class": "form-control", "placeholder": "Rubro"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Localidad"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }