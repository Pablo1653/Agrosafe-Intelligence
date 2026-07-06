from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from apps.companies.models import Company
from .models import Interaction
from .forms import InteractionForm


def interaction_list(request):
    """
    Todas las interacciones registradas, sin importar la empresa.
    Complementa el dashboard: acá se puede ver/buscar el historial
    completo, no solo las últimas 8.
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
    Crear una interacción para una empresa puntual. Se accede desde
    la ficha de detalle de esa empresa.
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


def interaction_update(request, pk):
    """
    Editar una interacción existente.
    """
    interaction = get_object_or_404(Interaction, pk=pk)
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


def interaction_delete(request, pk):
    """
    Eliminar una interacción (a diferencia de Company, acá sí se borra
    de verdad: es un registro de actividad, no una entidad de negocio
    que valga la pena conservar inactiva).
    """
    interaction = get_object_or_404(Interaction, pk=pk)
    company_uuid = interaction.company.company_uuid

    if request.method == "POST":
        interaction.delete()
        messages.success(request, "Interacción eliminada.")

    return redirect("companies:company_detail", company_uuid=company_uuid)