from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path("", views.company_list, name="company_list"),
    path("nueva/", views.company_create, name="company_create"),
    path("<uuid:company_uuid>/", views.company_detail, name="company_detail"),
    path("<uuid:company_uuid>/editar/", views.company_update, name="company_update"),
]