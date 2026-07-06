from django import forms
from .models import RawCompany


class GoogleMapsSearchForm(forms.Form):
    """
    Búsqueda por texto libre + ciudad, para armar la textQuery que se le
    manda a Google Places (ej. "acopio de granos" + "Rosario" ->
    "acopio de granos en Rosario, Argentina").
    """
    query = forms.CharField(
        label="Rubro o tipo de empresa",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: acopio de granos"}),
    )
    city = forms.CharField(
        label="Ciudad / zona",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Rosario"}),
    )
    max_results = forms.IntegerField(
        label="Cantidad máxima de resultados",
        initial=20,
        min_value=1,
        max_value=20,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )


class RawCompanyImportForm(forms.Form):
    """
    Accepts a CSV or Excel (.xlsx) file. Column names are matched
    loosely against Spanish/English aliases (see views._map_headers),
    so "razon_social" and "business_name" both work.
    """
    file = forms.FileField(
        label="Archivo CSV o Excel (.csv, .xlsx)",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )


class RawCompanyEditForm(forms.ModelForm):
    """
    Used from the review queue to complete/fix a record by hand
    (e.g. the company a friend recommended, with missing fields)
    before promoting it into Company.
    """

    class Meta:
        model = RawCompany
        fields = ["business_name", "trade_name", "cuit", "website", "industry", "city"]
        widgets = {
            "business_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Razón social"}),
            "trade_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre comercial"}),
            "cuit": forms.TextInput(attrs={"class": "form-control", "placeholder": "30-12345678-9"}),
            "website": forms.TextInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "industry": forms.TextInput(attrs={"class": "form-control", "placeholder": "Rubro"}),
            "city": forms.TextInput(attrs={"class": "form-control", "placeholder": "Localidad"}),
        }