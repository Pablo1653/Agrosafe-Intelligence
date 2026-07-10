from django.db import models
from django.conf import settings
import uuid

from apps.companies.models import Company


class Contact(models.Model):
    """
    Represents a person belonging to a company.

    A company can have multiple contacts. Contacts are the people
    with whom commercial, technical and administrative interactions
    take place.

    Future applications such as interactions, reminders, documents
    and AI scoring will reference this model.
    """

    """
    Company this contact belongs to.
    """
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name="Empresa",
    )

    """
    Public unique identifier used for integrations, APIs and URLs.
    """
    contact_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    """
    Contact's first name.
    """
    first_name = models.CharField(
        max_length=100,
        verbose_name="Nombre",
    )

    """
    Contact's last name.
    """
    last_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Apellido",
    )

    """
    Contact's job title inside the company.
    Example:
        - Gerente General
        - Responsable de Higiene y Seguridad
        - Comprador
    """
    position = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Cargo",
    )

    """
    Main contact email.
    """
    email = models.EmailField(
        blank=True,
        verbose_name="Correo Electrónico",
    )

    """
    Office phone number.
    """
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Teléfono",
    )

    """
    Mobile phone number.
    """
    mobile = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Celular",
    )


    """
    LinkedIn profile URL.
    """
    linkedin = models.URLField(
        blank=True,
        verbose_name="LinkedIn",
    )

    """
    Free text notes about the contact.
    """
    notes = models.TextField(
        blank=True,
        verbose_name="Observaciones",
    )

    """
    Indicates whether this is the company's primary contact.
    """
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Contacto principal",
    )

    """
    Soft delete flag.
    """
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
    )

    """
    Date and time when the contact was created.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    """
    Date and time of the last modification.
    """
    updated_at = models.DateTimeField(
        auto_now=True,
    )

    """
    User who created the contact.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts_created",
    )

    class Meta:
        ordering = [
            "company__business_name",
            "last_name",
            "first_name",
        ]

        verbose_name = "Contacto"
        verbose_name_plural = "Contactos"

        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["last_name"]),
            models.Index(fields=["email"]),
            models.Index(fields=["is_primary"]),
            models.Index(fields=["is_active"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["company"],
                condition=models.Q(is_primary=True),
                name="unique_primary_contact_per_company",
            )
        ]

    def __str__(self):
        full_name = f"{self.first_name} {self.last_name}".strip()

        if self.company:
            return f"{full_name} - {self.company.business_name}"

        return full_name