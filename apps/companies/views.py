from django.shortcuts import render, get_object_or_404
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


def company_detail(request, company_uuid):
    """
    Display the full record for a single company, identified by its
    public UUID (not its internal numeric pk).
    """
    company = get_object_or_404(Company, company_uuid=company_uuid)
 
    context = {
        "company": company
    }
 
    return render(
        request,
        "companies/company_detail.html",
        context,
    )