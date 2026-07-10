from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [

    path("", views.contact_list, name="contact_list"),

    path("nuevo/", views.contact_create, name="contact_create"),

    path("<uuid:contact_uuid>/",views.contact_detail,name="contact_detail",),

    path("<uuid:contact_uuid>/editar/",views.contact_update,name="contact_update",),

    path("<uuid:contact_uuid>/baja/",views.contact_deactivate,name="contact_deactivate",),

    path("<uuid:contact_uuid>/activar/",views.contact_activate,name="contact_activate",),

]