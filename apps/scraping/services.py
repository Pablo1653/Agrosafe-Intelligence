import re
from apps.companies.models import Company
from .models import RawCompany

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _collapse_spaces(value: str) -> str:
    return " ".join((value or "").split()).strip()


def _normalize_cuit(value: str) -> str:
    """
    Keeps only digits and, if there are exactly 11 (a valid CUIT length),
    reformats as XX-XXXXXXXX-X. Anything else is left as digits-only so
    validation can flag it as malformed instead of silently accepting it.
    """
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11:
        return f"{digits[0:2]}-{digits[2:10]}-{digits[10]}"
    return digits


def clean_raw_company(raw: RawCompany) -> RawCompany:
    """
    'Clean' step: normalizes formatting only. Does not decide
    whether the record is valid or a duplicate — that's validate_raw_company.
    """
    raw.business_name = _collapse_spaces(raw.business_name)
    raw.trade_name = _collapse_spaces(raw.trade_name)
    raw.industry = _collapse_spaces(raw.industry)
    raw.city = _collapse_spaces(raw.city)
    raw.cuit = _normalize_cuit(raw.cuit)

    website = _collapse_spaces(raw.website)
    if website and not website.startswith(("http://", "https://")):
        website = f"https://{website}"
    raw.website = website

    raw.email = _collapse_spaces(raw.email).lower()

    raw.save()
    return raw


def validate_raw_company(raw: RawCompany) -> str:
    """
    'validation' step: decides what to do with a cleaned record.

    - REJECTED: missing the bare minimum to be useful.
    - NEEDS_REVIEW: malformed CUIT, malformed email, or looks like a
      duplicate of an existing Company. Pablo has to look at it manually.
    - PENDING: looks fine, ready to be promoted with one click.
    """
    if not raw.business_name and not raw.cuit:
        raw.status = RawCompany.Status.REJECTED
        raw.notes = "Sin razón social ni CUIT: registro descartado."
        raw.save(update_fields=["status", "notes", "updated_at"])
        return raw.status

    if raw.cuit and len(re.sub(r"\D", "", raw.cuit)) != 11:
        raw.status = RawCompany.Status.NEEDS_REVIEW
        raw.notes = f"CUIT con formato inválido: \"{raw.cuit}\"."
        raw.save(update_fields=["status", "notes", "updated_at"])
        return raw.status

    if raw.email and not EMAIL_RE.match(raw.email):
        raw.status = RawCompany.Status.NEEDS_REVIEW
        raw.notes = f"Email con formato inválido: \"{raw.email}\"."
        raw.save(update_fields=["status", "notes", "updated_at"])
        return raw.status

    existing = None
    if raw.cuit:
        existing = Company.objects.filter(cuit=raw.cuit).first()
    if not existing and raw.business_name:
        existing = Company.objects.filter(business_name__iexact=raw.business_name).first()

    if existing:
        raw.status = RawCompany.Status.NEEDS_REVIEW
        raw.notes = f"Ya existe una empresa similar: \"{existing.business_name}\" (CUIT {existing.cuit or '—'})."
    else:
        raw.status = RawCompany.Status.PENDING
        raw.notes = ""

    raw.save(update_fields=["status", "notes", "updated_at"])
    return raw.status


def promote_raw_company(raw: RawCompany, user=None) -> Company:
    """
    Turns a RawCompany into a real Company.

    If a matching Company already exists (by CUIT or exact business
    name), it fills in any blank fields on that existing record
    instead of creating a duplicate — it never overwrites data that's
    already there.
    """
    if raw.status in (RawCompany.Status.PROMOTED, RawCompany.Status.REJECTED):
        raise ValueError("Este registro ya fue procesado y no se puede promover de nuevo.")

    existing = None
    if raw.cuit:
        existing = Company.objects.filter(cuit=raw.cuit).first()
    if not existing and raw.business_name:
        existing = Company.objects.filter(business_name__iexact=raw.business_name).first()

    if existing:
        changed_fields = []
        for field in ["trade_name", "website", "industry", "city", "email"]:
            raw_value = getattr(raw, field)
            if raw_value and not getattr(existing, field):
                setattr(existing, field, raw_value)
                changed_fields.append(field)
        if changed_fields:
            existing.save(update_fields=changed_fields + ["updated_at"])
        company = existing
    else:
        company = Company.objects.create(
            business_name=raw.business_name,
            trade_name=raw.trade_name,
            cuit=raw.cuit or None,
            website=raw.website,
            industry=raw.industry,
            city=raw.city,
            email=raw.email,
            created_by=user if (user and user.is_authenticated) else None,
        )

    raw.status = RawCompany.Status.PROMOTED
    raw.promoted_company = company
    raw.save(update_fields=["status", "promoted_company", "updated_at"])
    return company


def reject_raw_company(raw: RawCompany, reason: str = "") -> RawCompany:
    raw.status = RawCompany.Status.REJECTED
    if reason:
        raw.notes = reason
    raw.save(update_fields=["status", "notes", "updated_at"])
    return raw