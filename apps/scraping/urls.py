from django.urls import path
from . import views

app_name = "scraping"

urlpatterns = [
    path("", views.raw_company_list, name="raw_company_list"),
    path("importar/", views.import_view, name="import"),
    path("google-maps/", views.google_maps_search_view, name="google_maps_search"),
    path("<int:pk>/editar/", views.raw_company_edit, name="raw_company_edit"),
    path("<int:pk>/promover/", views.raw_company_promote, name="raw_company_promote"),
    path("<int:pk>/rechazar/", views.raw_company_reject, name="raw_company_reject"),
]