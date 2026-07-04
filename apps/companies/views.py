from django.shortcuts import render
from .models import Company


def company_list(request):
    """
    Display all registered companies.
    """
    companies = Company.objects.all()

    context = {
        "companies": companies
    }

    return render(
        request,
        "companies/company_list.html",
        context,
    )