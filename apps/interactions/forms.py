from django import forms
from .models import Interaction


class InteractionForm(forms.ModelForm):
    class Meta:
        model = Interaction
        fields = [
            "contact_name",
            "interaction_type",
            "date",
            "notes",
            "outcome",
            "follow_up_date",
        ]
        widgets = {
            "contact_name": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Con quién hablaste (opcional)"
            }),
            "interaction_type": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "¿Qué se habló?"}),
            "outcome": forms.Select(attrs={"class": "form-select"}),
            "follow_up_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }