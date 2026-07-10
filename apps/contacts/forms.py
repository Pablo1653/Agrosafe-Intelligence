from django import forms

from .models import Contact


class ContactForm(forms.ModelForm):
    """
    Form for creating and editing contacts.
    """

    class Meta:
        model = Contact
        fields = [
            "company",
            "first_name",
            "last_name",
            "position",
            "email",
            "mobile",
            "phone",
            "linkedin",
            "is_primary",
            "notes",
        ]

        widgets = {
            "company": forms.Select(attrs={"class": "form-select"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "mobile": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "linkedin": forms.URLInput(attrs={"class": "form-control"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),
        }