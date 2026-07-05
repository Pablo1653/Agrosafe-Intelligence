from django.shortcuts import render, get_object_or_404,redirect
from django.contrib import messages
from .models import Company
from .forms import CompanyForm


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


def company_create(request):
    """
    Create a new company.
 
    Note: created_by is left blank for now (no login system yet).
    Once authentication is added, set company.created_by = request.user
    here before saving.
    """
    if request.method == "POST":
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save()
            messages.success(request, f"Empresa \"{company.business_name}\" creada correctamente.")
            return redirect("companies:company_detail", company_uuid=company.company_uuid)
    else:
        form = CompanyForm()
 
    context = {
        "form": form,
        "is_edit": False,
    }
    return render(request, "companies/company_form.html", context)
 
 
def company_update(request, company_uuid):
    """
    Edit an existing company.
    """
    company = get_object_or_404(Company, company_uuid=company_uuid)
 
    if request.method == "POST":
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f"Empresa \"{company.business_name}\" actualizada correctamente.")
            return redirect("companies:company_detail", company_uuid=company.company_uuid)
    else:
        form = CompanyForm(instance=company)
 
    context = {
        "form": form,
        "is_edit": True,
        "company": company,
    }
    return render(request, "companies/company_form.html", context)