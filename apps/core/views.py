from django.shortcuts import render
from django.utils import timezone

from apps.companies.models import Company
from apps.interactions.models import Interaction
from apps.scraping.models import RawCompany


def home(request):
    """
    Dashboard de arranque: qué hay que hacer hoy, no solo un saludo.
    """
    today = timezone.localdate()

    # Para cada empresa, nos interesa solo su interacción MÁS RECIENTE:
    # si ya la volviste a llamar, no tiene sentido seguir mostrando el
    # seguimiento de una interacción vieja como "vencido".
    latest_by_company = {}
    for interaction in Interaction.objects.select_related("company").order_by("date"):
        latest_by_company[interaction.company_id] = interaction

    pending_followups = [
        interaction for interaction in latest_by_company.values()
        if interaction.follow_up_date and interaction.follow_up_date <= today
    ]
    pending_followups.sort(key=lambda i: i.follow_up_date)

    companies_never_contacted = (
        Company.objects
        .filter(is_active=True, interactions__isnull=True)
        .order_by("-created_at")
    )

    scraping_counts = {
        "needs_review": RawCompany.objects.filter(status=RawCompany.Status.NEEDS_REVIEW).count(),
        "pending": RawCompany.objects.filter(status=RawCompany.Status.PENDING).count(),
    }

    recent_interactions = (
        Interaction.objects.select_related("company").order_by("-created_at")[:8]
    )

    context = {
        "today": today,
        "pending_followups": pending_followups[:10],
        "pending_followups_count": len(pending_followups),
        "companies_never_contacted": companies_never_contacted[:10],
        "companies_never_contacted_count": companies_never_contacted.count(),
        "scraping_counts": scraping_counts,
        "recent_interactions": recent_interactions,
        "total_active_companies": Company.objects.filter(is_active=True).count(),
    }
    return render(request, "core/home.html", context)