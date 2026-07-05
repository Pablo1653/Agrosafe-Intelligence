from django.db import models
from django.conf import settings
from apps.companies.models import Company


class RawCompany(models.Model):
    """
    Staging table for the scraping/import pipeline.

    Nothing coming from an external source (Google Maps, LinkedIn,
    a website, a newsletter, or a manually uploaded CSV/Excel) is
    written directly into Company. It lands here first as a
    RawCompany, gets cleaned and validated, and only then gets
    promoted into a real Company record.

    This keeps Company clean regardless of how messy or unreliable
    the original source was, and keeps a full audit trail (raw_data)
    of what was originally scraped/imported.
    """

    class Source(models.TextChoices):
        GOOGLE_MAPS = "GOOGLE_MAPS", "Google Maps"
        LINKEDIN = "LINKEDIN", "LinkedIn"
        WEBSITE = "WEBSITE", "Sitio web"
        NEWSLETTER = "NEWSLETTER", "Boletín"
        CSV_IMPORT = "CSV_IMPORT", "Importación CSV/Excel"
        MANUAL = "MANUAL", "Carga manual"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        NEEDS_REVIEW = "NEEDS_REVIEW", "Necesita revisión"
        PROMOTED = "PROMOTED", "Promovida a Company"
        REJECTED = "REJECTED", "Rechazada"

    source = models.CharField(
        max_length=20,
        choices=Source.choices,
        verbose_name="Fuente",
    )

    """
    Original, untouched payload as it came from the source
    (e.g. one row of a scraped page, one row of an uploaded CSV).
    Kept for debugging/audit even after cleaning overwrites the
    fields below.
    """
    raw_data = models.JSONField(default=dict, blank=True)

    # --- Extracted / working fields (mirror Company's editable fields) ---
    business_name = models.CharField(max_length=255, blank=True, verbose_name="Razón Social")
    trade_name = models.CharField(max_length=255, blank=True, verbose_name="Nombre Comercial")
    cuit = models.CharField(max_length=13, blank=True, verbose_name="CUIT")
    website = models.CharField(max_length=255, blank=True, verbose_name="Sitio Web")
    industry = models.CharField(max_length=150, blank=True, verbose_name="Rubro")
    city = models.CharField(max_length=120, blank=True, verbose_name="Localidad")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    """
    Why this record needs review or was rejected (e.g. "posible
    duplicado de Bunge Argentina SA", "CUIT inválido").
    """
    notes = models.TextField(blank=True)

    """
    Once promoted, points to the Company record it became.
    """
    promoted_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_sources",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_companies_created",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Empresa cruda (staging)"
        verbose_name_plural = "Empresas crudas (staging)"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source"]),
        ]

    def __str__(self):
        return f"{self.business_name or '(sin nombre)'} [{self.get_source_display()} · {self.get_status_display()}]"