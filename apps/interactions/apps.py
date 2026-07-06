from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.interactions"     # ← con el prefijo "apps."
    verbose_name = "Interacciones"