from django.urls import path
from . import views

app_name = "interactions"

urlpatterns = [
    path("empresa/<uuid:company_uuid>/nueva/", views.interaction_create, name="interaction_create"),
    path("<int:pk>/editar/", views.interaction_update, name="interaction_update"),
    path("<int:pk>/eliminar/", views.interaction_delete, name="interaction_delete"),
]