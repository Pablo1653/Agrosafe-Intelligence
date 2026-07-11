from django.db import transaction

from .models import Contact


def get_active_contacts():
    return Contact.objects.filter(is_active=True).select_related("company")


def set_primary_contact(contact):
    with transaction.atomic():
        Contact.objects.filter(
            company=contact.company, is_primary=True
        ).exclude(pk=contact.pk).update(is_primary=False)

        if not contact.is_primary:
            contact.is_primary = True
            contact.save(update_fields=["is_primary", "updated_at"])