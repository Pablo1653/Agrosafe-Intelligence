from .models import Contact


def get_active_contacts():
    return Contact.objects.filter(is_active=True).select_related("company")