from django.urls import path
from . import views

app_name = "interactions"

urlpatterns = [
    path("", views.interaction_list, name="interaction_list"),
    path("empresa/<uuid:company_uuid>/nueva/", views.interaction_create, name="interaction_create"),
    path("<uuid:interaction_uuid>/editar/", views.interaction_update, name="interaction_update"),
    path("<uuid:interaction_uuid>/eliminar/", views.interaction_delete, name="interaction_delete"),
]