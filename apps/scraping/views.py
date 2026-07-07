import csv
import io

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import RawCompany
from .forms import RawCompanyImportForm, RawCompanyEditForm, GoogleMapsSearchForm
from .services import clean_raw_company, validate_raw_company, promote_raw_company, reject_raw_company
from .sources.google_places import search_google_places, GooglePlacesError

try:
    import openpyxl
except ImportError:
    openpyxl = None


# Column name aliases accepted in an uploaded CSV/Excel, so both
# Spanish and English headers work without configuration.
HEADER_ALIASES = {
    "business_name": ["business_name", "razon_social", "razón social", "nombre", "empresa"],
    "trade_name": ["trade_name", "nombre_comercial", "nombre comercial"],
    "cuit": ["cuit"],
    "website": ["website", "sitio_web", "sitio web", "web"],
    "phone": ["phone","telefono","teléfono","telefono_principal","tel","celular","mobile","whatsapp",],
    "industry": ["industry", "rubro", "actividad"],
    "city": ["city", "localidad", "ciudad"],
    "email": ["email", "mail", "correo", "correo_electronico", "correo electrónico", "e-mail"],
    
}


def _map_headers(headers):
    normalized = {(h or "").strip().lower(): h for h in headers}
    mapping = {}
    for field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def _read_csv(uploaded_file):
    text = uploaded_file.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return reader.fieldnames or [], list(reader)


def _read_xlsx(uploaded_file):
    if not openpyxl:
        raise RuntimeError(
            "Falta instalar openpyxl para leer archivos .xlsx. "
            "Corré: pip install openpyxl"
        )
    workbook = openpyxl.load_workbook(uploaded_file, data_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [str(h) if h is not None else "" for h in rows[0]]
    data = []
    for row in rows[1:]:
        row_dict = {headers[i]: row[i] for i in range(len(headers)) if i < len(row)}
        data.append(row_dict)
    return headers, data


def import_view(request):
    """
    Upload a CSV or Excel file with companies. Every row becomes a
    RawCompany (source=CSV_IMPORT), then goes through clean + validate
    immediately, landing in PENDING / NEEDS_REVIEW / REJECTED.
    Nothing is written to Company directly from here.
    """
    if request.method == "POST":
        form = RawCompanyImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["file"]
            filename = uploaded_file.name.lower()

            try:
                if filename.endswith(".csv"):
                    headers, rows = _read_csv(uploaded_file)
                elif filename.endswith(".xlsx"):
                    headers, rows = _read_xlsx(uploaded_file)
                else:
                    messages.error(request, "Formato no soportado. Subí un archivo .csv o .xlsx.")
                    return render(request, "scraping/import_form.html", {"form": form})
            except RuntimeError as exc:
                messages.error(request, str(exc))
                return render(request, "scraping/import_form.html", {"form": form})

            mapping = _map_headers(headers)
            if "business_name" not in mapping:
                messages.error(
                    request,
                    "El archivo necesita al menos una columna de razón social "
                    "(ej. 'razon_social' o 'business_name')."
                )
                return render(request, "scraping/import_form.html", {"form": form})

            created_count = 0
            for row in rows:
                values = {
                    field: str(row.get(col, "") or "").strip()
                    for field, col in mapping.items()
                }
                if not any(values.values()):
                    continue

                raw = RawCompany.objects.create(
                    source=RawCompany.Source.CSV_IMPORT,
                    raw_data={k: ("" if v is None else str(v)) for k, v in row.items()},
                    business_name=values.get("business_name", ""),
                    trade_name=values.get("trade_name", ""),
                    cuit=values.get("cuit", ""),
                    website=values.get("website", ""),
                    industry=values.get("industry", ""),
                    city=values.get("city", ""),
                    email=values.get("email", ""),
                    phone=values.get("phone", ""),
                    created_by=request.user if request.user.is_authenticated else None,
                )
                clean_raw_company(raw)
                validate_raw_company(raw)
                created_count += 1

            messages.success(
                request,
                f"Se importaron {created_count} registros. Revisalos en la cola de revisión."
            )
            return redirect("scraping:raw_company_list")
    else:
        form = RawCompanyImportForm()

    return render(request, "scraping/import_form.html", {"form": form})


def raw_company_list(request):
    """
    Review queue. Defaults to showing NEEDS_REVIEW, since that's the
    bucket that actually needs Pablo's attention; PENDING ones are
    already "ready to promote" and REJECTED/PROMOTED are done.
    """
    status_filter = request.GET.get("status", RawCompany.Status.NEEDS_REVIEW)

    queryset = RawCompany.objects.select_related("promoted_company")
    if status_filter != "ALL":
        queryset = queryset.filter(status=status_filter)

    counts = {choice.value: RawCompany.objects.filter(status=choice.value).count()
              for choice in RawCompany.Status}
    counts["ALL"] = RawCompany.objects.count()

    context = {
        "raw_companies": queryset,
        "status_filter": status_filter,
        "counts": counts,
        "statuses": RawCompany.Status,
    }
    return render(request, "scraping/raw_company_list.html", context)


def raw_company_edit(request, pk):
    """
    Manually filling out a record before approving it—for example, the
    company recommended to me by a friend, with the missing fields filled in by hand.
    The validation runs again after saving, so it exits the NEEDS_REVIEW status
    if the correction has resolved the issue.
    """
    raw = get_object_or_404(RawCompany, pk=pk)

    if request.method == "POST":
        form = RawCompanyEditForm(request.POST, instance=raw)
        if form.is_valid():
            form.save()
            clean_raw_company(raw)
            validate_raw_company(raw)
            messages.success(request, "Registro actualizado.")
            return redirect("scraping:raw_company_list")
    else:
        form = RawCompanyEditForm(instance=raw)

    return render(request, "scraping/raw_company_edit.html", {"form": form, "raw": raw})


def raw_company_promote(request, pk):
    raw = get_object_or_404(RawCompany, pk=pk)
    if request.method == "POST":
        try:
            company = promote_raw_company(raw, user=request.user)
            messages.success(request, f"\"{company.business_name}\" promovida a Company.")
        except ValueError as exc:
            messages.error(request, str(exc))
    next_url = request.POST.get("next") or "scraping:raw_company_list"
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("scraping:raw_company_list")


def raw_company_reject(request, pk):
    raw = get_object_or_404(RawCompany, pk=pk)
    if request.method == "POST":
        reject_raw_company(raw, reason="Rechazado manualmente desde la cola de revisión.")
        messages.success(request, "Registro rechazado.")
    next_url = request.POST.get("next") or "scraping:raw_company_list"
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("scraping:raw_company_list")


def google_maps_search_view(request):
    """
    Search for businesses on Google Places by category + city and import them as
    RawCompany (source=GOOGLE_MAPS), running them through the same clean+validate
    process used for CSV/Excel imports.
    """
    if request.method == "POST":
        form = GoogleMapsSearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["query"]
            city = form.cleaned_data["city"]
            max_results = form.cleaned_data["max_results"]
            text_query = f"{query} en {city}, Argentina"

            api_key = getattr(settings, "GOOGLE_PLACES_API_KEY", "")
            try:
                results = search_google_places(text_query, api_key, max_results=max_results)
            except GooglePlacesError as exc:
                messages.error(request, str(exc))
                return render(request, "scraping/google_maps_search.html", {"form": form})

            created_count = 0
            for place in results:
                raw = RawCompany.objects.create(
                    source=RawCompany.Source.GOOGLE_MAPS,
                    raw_data=place,
                    business_name=place.get("business_name", ""),
                    website=place.get("website", ""),
                    city=place.get("city") or city,
                    industry=query,
                    created_by=request.user if request.user.is_authenticated else None,
                )
                clean_raw_company(raw)
                validate_raw_company(raw)
                created_count += 1

            messages.success(
                request,
                f"Se encontraron {created_count} empresas para \"{query}\" en {city}."
            )
            return redirect("scraping:raw_company_list")
    else:
        form = GoogleMapsSearchForm()

    return render(request, "scraping/google_maps_search.html", {"form": form})