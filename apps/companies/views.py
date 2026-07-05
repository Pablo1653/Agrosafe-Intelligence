from django.shortcuts import render, get_object_or_404,redirect
from django.contrib import messages
from .models import Company
from .forms import CompanyForm


def company_list(request):
    """
    Display registered companies.
 
    By default only active companies are shown. Pass ?mostrar_inactivas=1
    in the query string to include soft-deleted (is_active=False) ones too.
    """
    show_inactive = request.GET.get("mostrar_inactivas") == "1"
 
    companies = Company.objects.all()
    if not show_inactive:
        companies = companies.filter(is_active=True)
 
    context = {
        "companies": companies,
        "show_inactive": show_inactive,
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

def company_deactivate(request, company_uuid):
    """
    Soft-delete a company: sets is_active=False instead of deleting the row.
    GET shows a confirmation page; POST performs the deactivation.
    """
    company = get_object_or_404(Company, company_uuid=company_uuid)
 
    if request.method == "POST":
        company.is_active = False
        company.save(update_fields=["is_active", "updated_at"])
        messages.success(request, f"Empresa \"{company.business_name}\" dada de baja.")
        return redirect("companies:company_list")
 
    context = {
        "company": company,
        "action": "deactivate",
    }
    return render(request, "companies/company_confirm_action.html", context)
 
 
def company_activate(request, company_uuid):
    """
    Reactivate a previously soft-deleted company.
    GET shows a confirmation page; POST performs the reactivation.
    """
    company = get_object_or_404(Company, company_uuid=company_uuid)
 
    if request.method == "POST":
        company.is_active = True
        company.save(update_fields=["is_active", "updated_at"])
        messages.success(request, f"Empresa \"{company.business_name}\" reactivada.")
        return redirect("companies:company_detail", company_uuid=company.company_uuid)
 
    context = {
        "company": company,
        "action": "activate",
    }
    return render(request, "companies/company_confirm_action.html", context)