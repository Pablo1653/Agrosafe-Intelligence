from django.db import models
import uuid
from django.conf import settings

# Create your models here.

"""
    Represents a company registered in AgroSafe Intelligence.

    This is the central entity of the CRM. It stores the company's
    core identity and general business information.

    Operational, environmental, commercial, compliance and AI-related
    data are managed by their respective applications through
    relationships with this model.
"""
class Company(models.Model):
    

    """
        Represents the commercial lifecycle of a company.
    """
    class Status(models.TextChoices):
        
        PROSPECT = "PROSPECT", "Prospecto"
        QUALIFIED = "QUALIFIED", "Calificado"
        CLIENT = "CLIENT", "Cliente"
        INACTIVE = "INACTIVE", "Inactivo"

    """
    Official registered business name (Razón Social).
    """
    business_name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Razón Social"
    )

    """
    Public unique identifier used for integrations, APIs and URLs.
    """
    company_uuid = models.UUIDField(
    default=uuid.uuid4,
    editable=False,
    unique=True
    )
    
    
    """
    Commercial or brand name used by the company.
    """
    trade_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nombre Comercial"
    )
    """
    Argentine tax identification number.
    """
    cuit = models.CharField(
        max_length=13,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="CUIT"
    )

    """
    Company's official website.
    """
    website = models.URLField(
        blank=True,
        verbose_name="Sitio Web"
    )
    
    """
    Main contact email for the company.
    """
    email = models.EmailField(
        blank=True,
        verbose_name="Correo Electrónico"
    )

    """
    Main contact phone number for the company (used to call potential clients).
    """
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Teléfono"
    )

    """
    Main economic activity or business sector.
    """
    industry = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Rubro"
    )
    """
    Primary city where the company operates.
    """

    city = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Localidad"
    )
    
    """
    Current commercial status within the sales pipeline.
    """
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROSPECT
    )

    is_active = models.BooleanField(default=True)

    """
    Date and time when the company record was created.
    """
    created_at = models.DateTimeField(auto_now_add=True)

    """
    Date and time of the last modification.
    """
    updated_at = models.DateTimeField(auto_now=True)

    """
    User who created the company record.
    """
    created_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
        related_name="companies_created"
    )
    """
        Model configuration and database optimization options.
    """
    class Meta:
        ordering = ["business_name"]

        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"

        indexes = [
        models.Index(fields=["status"]),
        models.Index(fields=["industry"]),
        models.Index(fields=["city"]),
    ]
    
    """
        Returns a human-readable representation of the company.
    """
    def __str__(self):
        if self.cuit:
            return f"{self.business_name} ({self.cuit})"
        return self.business_name