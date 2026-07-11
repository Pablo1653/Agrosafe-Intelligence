from django.db import models
from django.conf import settings
import uuid
from apps.companies.models import Company


class Interaction(models.Model):
    """
    Recording a contact activity with a company: a phone call,
    an email, a visit, etc.

    For now, it points directly to Company. Once the `contacts` app is available,
    you can add a real ForeignKey to Contact without losing this
    history: `contact_name` remains as the backup/legacy data.
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

    interaction_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="interactions",
        verbose_name="Empresa",
    )

    """
   Name of the person you spoke with, as free text for
    now (there is no contacts app yet).
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
    If there is a need to follow up on the contact in the future, when.
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