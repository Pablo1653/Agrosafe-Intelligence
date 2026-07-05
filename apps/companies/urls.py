from django.urls import path
from . import views

app_name = "companies"

urlpatterns = [
    path("", views.company_list, name="company_list"),
    path("<uuid:company_uuid>/", views.company_detail, name="company_detail"),
]