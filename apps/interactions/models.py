from django.db import models
from django.conf import settings
from apps.companies.models import Company


class Interaction(models.Model):
    """
    Registro de una actividad de contacto con una empresa: una llamada,
    un email, una visita, etc.

    Por ahora apunta directo a Company. Cuando exista la app `contacts`,
    se puede agregar un ForeignKey real a Contact sin perder este
    historial: contact_name queda como el dato de respaldo/legado.
    """

    class InteractionType(models.TextChoices):
        CALL = "CALL", "Llamada"
        EMAIL = "EMAIL", "Email"
        MEETING = "MEETING", "Reunión"
        WHATSAPP = "WHATSAPP", "WhatsApp"
        VISIT = "VISIT", "Visita"
        OTHER = "OTHER", "Otro"

    class Outcome(models.TextChoices):
        POSITIVE = "POSITIVE", "Positivo"
        NEUTRAL = "NEUTRAL", "Neutro"
        NEGATIVE = "NEGATIVE", "Negativo"
        NO_RESPONSE = "NO_RESPONSE", "Sin respuesta"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="interactions",
        verbose_name="Empresa",
    )

    """
    Nombre de la persona con la que se habló, como texto libre por
    ahora (no hay app de contactos todavía).
    """
    contact_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Contacto (nombre)",
    )

    interaction_type = models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        default=InteractionType.CALL,
        verbose_name="Tipo",
    )

    date = models.DateTimeField(verbose_name="Fecha")

    notes = models.TextField(blank=True, verbose_name="Notas")

    outcome = models.CharField(
        max_length=20,
        choices=Outcome.choices,
        blank=True,
        verbose_name="Resultado",
    )

    """
    Si hay que retomar contacto en el futuro, cuándo.
    """
    follow_up_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Próximo seguimiento",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interactions_created",
    )

    class Meta:
        ordering = ["-date"]
        verbose_name = "Interacción"
        verbose_name_plural = "Interacciones"
        indexes = [
            models.Index(fields=["company", "-date"]),
            models.Index(fields=["follow_up_date"]),
        ]

    def __str__(self):
        return f"{self.get_interaction_type_display()} con {self.company.business_name} ({self.date:%d/%m/%Y})"