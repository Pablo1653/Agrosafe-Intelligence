from django.shortcuts import render

# Create your views here.


from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContactForm
from .models import Contact


def contact_list(request):

    show_inactive = request.GET.get("mostrar_inactivos") == "1"

    contacts = Contact.objects.select_related("company")

    if not show_inactive:
        contacts = contacts.filter(is_active=True)

    return render(
        request,
        "contacts/contact_list.html",
        {
            "contacts": contacts,
            "show_inactive": show_inactive,
        },
    )


def contact_detail(request, contact_uuid):

    contact = get_object_or_404(Contact, contact_uuid=contact_uuid)

    return render(
        request,
        "contacts/contact_detail.html",
        {
            "contact": contact
        },
    )


def contact_create(request):

    if request.method == "POST":

        form = ContactForm(request.POST)

        if form.is_valid():

            contact = form.save()

            messages.success(
                request,
                "Contacto creado correctamente."
            )

            return redirect(
                "contacts:contact_detail",
                contact_uuid=contact.contact_uuid,
            )

    else:

        form = ContactForm()

    return render(
        request,
        "contacts/contact_form.html",
        {
            "form": form,
            "is_edit": False,
        },
    )


def contact_update(request, contact_uuid):

    contact = get_object_or_404(Contact, contact_uuid=contact_uuid)

    if request.method == "POST":

        form = ContactForm(request.POST, instance=contact)

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Contacto actualizado."
            )

            return redirect(
                "contacts:contact_detail",
                contact_uuid=contact.contact_uuid,
            )

    else:

        form = ContactForm(instance=contact)

    return render(
        request,
        "contacts/contact_form.html",
        {
            "form": form,
            "is_edit": True,
            "contact": contact,
        },
    )


def contact_deactivate(request, contact_uuid):

    contact = get_object_or_404(Contact, contact_uuid=contact_uuid)

    if request.method == "POST":

        contact.is_active = False

        contact.save(update_fields=["is_active", "updated_at"])

        messages.success(request, "Contacto dado de baja.")

        return redirect("contacts:contact_list")

    return render(
        request,
        "contacts/contact_confirm_action.html",
        {
            "contact": contact,
            "action": "deactivate",
        },
    )


def contact_activate(request, contact_uuid):

    contact = get_object_or_404(Contact, contact_uuid=contact_uuid)

    if request.method == "POST":

        contact.is_active = True

        contact.save(update_fields=["is_active", "updated_at"])

        messages.success(request, "Contacto reactivado.")

        return redirect(
            "contacts:contact_detail",
            contact_uuid=contact.contact_uuid,
        )

    return render(
        request,
        "contacts/contact_confirm_action.html",
        {
            "contact": contact,
            "action": "activate",
        },
    )