from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from apps.companies.models import Company
from .models import Interaction
from .forms import InteractionForm


def interaction_list(request):
    """
    All recorded interactions, regardless of the company.
    Complements the dashboard: here you can view/search the
    complete history, not just the last 8.
    """
    interactions = Interaction.objects.select_related("company").order_by("-date")

    filtro = request.GET.get("filtro", "")
    if filtro == "pendientes":
        today = timezone.localdate()
        interactions = interactions.filter(follow_up_date__isnull=False, follow_up_date__lte=today)

    context = {
        "interactions": interactions,
        "filtro": filtro,
    }
    return render(request, "interactions/interaction_list.html", context)


def interaction_create(request, company_uuid):
    """
    Create an interaction for a specific company. You can access this from
    that company's detail page.
    """
    company = get_object_or_404(Company, company_uuid=company_uuid)

    if request.method == "POST":
        form = InteractionForm(request.POST)
        if form.is_valid():
            interaction = form.save(commit=False)
            interaction.company = company
            interaction.created_by = request.user if request.user.is_authenticated else None
            interaction.save()
            messages.success(request, "Interacción registrada.")
            return redirect("companies:company_detail", company_uuid=company.company_uuid)
    else:
        form = InteractionForm(initial={"date": timezone.now()})

    context = {
        "form": form,
        "company": company,
        "is_edit": False,
    }
    return render(request, "interactions/interaction_form.html", context)


def interaction_update(request, interaction_uuid):
    """
    Edit an existing interaction.
    """
    interaction = get_object_or_404(Interaction, interaction_uuid=interaction_uuid)
    company = interaction.company

    if request.method == "POST":
        form = InteractionForm(request.POST, instance=interaction)
        if form.is_valid():
            form.save()
            messages.success(request, "Interacción actualizada.")
            return redirect("companies:company_detail", company_uuid=company.company_uuid)
    else:
        form = InteractionForm(instance=interaction)

    context = {
        "form": form,
        "company": company,
        "is_edit": True,
        "interaction": interaction,
    }
    return render(request, "interactions/interaction_form.html", context)


def interaction_delete(request, interaction_uuid):
    """
    Delete an interaction (unlike “Company,” here it is actually deleted:
    it is an activity record, not a business entity
    worth keeping even if it is inactive).
    """

    interaction = get_object_or_404(Interaction, interaction_uuid=interaction_uuid)
    company_uuid = interaction.company.company_uuid

    if request.method == "POST":
        interaction.delete()
        messages.success(request, "Interacción eliminada.")

    return redirect("companies:company_detail", company_uuid=company_uuid)