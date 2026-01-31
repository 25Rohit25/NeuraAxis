"""
NEURAXIS - Patient Search API Routes
FastAPI endpoints for advanced patient search with full-text search and filters
"""

import json
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import (
    and_,
    case,
    extract,
    func,
    or_,
    select,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.patient import Gender, Patient, PatientStatus

router = APIRouter(prefix="/patients", tags=["patients"])


# =============================================================================
# Schemas
# =============================================================================


class PatientListItem(BaseModel):
    """Patient list item for search results."""

    id: UUID
    mrn: str
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: date
    age: int
    gender: Gender
    phone_primary: str
    email: Optional[str]
    city: str
    state: str
    status: PatientStatus
    primary_diagnosis: Optional[str]
    allergies_count: int
    conditions_count: int
    last_visit_date: Optional[date]
    created_at: datetime
    updated_at: datetime


class SearchFacets(BaseModel):
    """Faceted counts for filters."""

    status: dict[str, int]
    gender: dict[str, int]
    age_ranges: dict[str, int]
    top_conditions: list[dict[str, int | str]]


class PatientSearchResponse(BaseModel):
    """Paginated patient search response."""

    items: list[PatientListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next_page: bool
    has_previous_page: bool
    facets: Optional[SearchFacets] = None


class BulkActionRequest(BaseModel):
    """Request for bulk patient actions."""

    action: str = Field(..., pattern="^(export|archive|activate|delete)$")
    patient_ids: list[UUID]


class BulkActionResponse(BaseModel):
    """Response for bulk actions."""

    success: bool
    processed_count: int
    failed_count: int
    errors: list[str] = []


# =============================================================================
# Search Endpoint
# =============================================================================


@router.get(
    "/search",
    response_model=PatientSearchResponse,
    summary="Search patients with advanced filtering",
    description="""
    Search patients with full-text search, filters, sorting, and pagination.
    
    **Search:**
    - Full-text search across name, MRN, phone, and email
    
    **Filters:**
    - Status: active, inactive, deceased, transferred
    - Gender: male, female, other
    - Age range: min/max age
    - Conditions: filter by chronic conditions
    - Has allergies: boolean filter
    - Date ranges: created date, last visit date
    
    **Sorting:**
    - name, mrn, dateOfBirth, lastVisit, createdAt
    - Direction: asc, desc
    
    **Pagination:**
    - Default page size: 20 (max: 100)
    """,
)
async def search_patients(
    # Text search
    q: Optional[str] = Query(None, description="Search query"),
    # Filters
    status: Optional[list[str]] = Query(None, description="Status filter"),
    gender: Optional[list[str]] = Query(None, description="Gender filter"),
    age_min: Optional[int] = Query(None, ge=0, le=150, description="Minimum age"),
    age_max: Optional[int] = Query(None, ge=0, le=150, description="Maximum age"),
    conditions: Optional[list[str]] = Query(None, description="Condition filter"),
    has_allergies: Optional[bool] = Query(None, description="Has allergies"),
    created_after: Optional[date] = Query(None, description="Created after date"),
    created_before: Optional[date] = Query(None, description="Created before date"),
    last_visit_after: Optional[date] = Query(None, description="Last visit after"),
    last_visit_before: Optional[date] = Query(None, description="Last visit before"),
    # Sorting
    sort_by: str = Query("createdAt", description="Sort field"),
    sort_direction: str = Query("desc", pattern="^(asc|desc)$"),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    # Options
    include_facets: bool = Query(False, description="Include faceted counts"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PatientSearchResponse:
    """Search patients with advanced filtering and pagination."""
    organization_id = current_user.get("organization_id")

    # Calculate current date for age calculation
    today = date.today()
    current_year = today.year

    # Base query
    query = select(Patient).where(
        Patient.organization_id == UUID(organization_id),
        Patient.is_deleted == False,  # noqa: E712
    )

    # ==========================================================================
    # Apply filters
    # ==========================================================================

    # Full-text search
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.mrn.ilike(search_term),
                Patient.phone_primary.ilike(search_term),
                Patient.email.ilike(search_term),
                func.concat(Patient.first_name, " ", Patient.last_name).ilike(search_term),
            )
        )

    # Status filter
    if status:
        status_enums = [PatientStatus(s) for s in status if s in PatientStatus.__members__.values()]
        if status_enums:
            query = query.where(Patient.status.in_(status_enums))

    # Gender filter
    if gender:
        gender_enums = [Gender(g) for g in gender if g in Gender.__members__.values()]
        if gender_enums:
            query = query.where(Patient.gender.in_(gender_enums))

    # Age filter (calculate from DOB)
    if age_min is not None:
        max_dob = date(current_year - age_min, today.month, today.day)
        query = query.where(Patient.date_of_birth <= max_dob)

    if age_max is not None:
        min_dob = date(current_year - age_max - 1, today.month, today.day)
        query = query.where(Patient.date_of_birth >= min_dob)

    # Conditions filter (search in JSON array)
    if conditions:
        for condition in conditions:
            query = query.where(Patient.chronic_conditions.ilike(f'%"{condition}"%'))

    # Allergies filter
    if has_allergies is not None:
        if has_allergies:
            query = query.where(
                and_(
                    Patient.allergies.isnot(None),
                    Patient.allergies != "[]",
                    Patient.allergies != "",
                )
            )
        else:
            query = query.where(
                or_(
                    Patient.allergies.is_(None),
                    Patient.allergies == "[]",
                    Patient.allergies == "",
                )
            )

    # Created date filter
    if created_after:
        query = query.where(Patient.created_at >= created_after)
    if created_before:
        query = query.where(Patient.created_at <= created_before)

    # TODO: Add last_visit filter when visits table exists

    # ==========================================================================
    # Sorting
    # ==========================================================================

    sort_column_map = {
        "name": func.concat(Patient.last_name, Patient.first_name),
        "mrn": Patient.mrn,
        "dateOfBirth": Patient.date_of_birth,
        "createdAt": Patient.created_at,
        "lastVisit": Patient.updated_at,  # Placeholder until visits table
    }

    sort_column = sort_column_map.get(sort_by, Patient.created_at)

    if sort_direction == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # ==========================================================================
    # Get total count
    # ==========================================================================

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # ==========================================================================
    # Pagination
    # ==========================================================================

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    patients = result.scalars().all()

    # ==========================================================================
    # Transform to response
    # ==========================================================================

    items = [_patient_to_list_item(p) for p in patients]

    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1

    # ==========================================================================
    # Facets (optional)
    # ==========================================================================

    facets = None
    if include_facets:
        facets = await _get_search_facets(db, organization_id, today)

    return PatientSearchResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next_page=has_next,
        has_previous_page=has_previous,
        facets=facets,
    )


# =============================================================================
# Bulk Actions Endpoint
# =============================================================================


@router.post(
    "/bulk-action",
    response_model=BulkActionResponse,
    summary="Perform bulk action on patients",
)
async def bulk_action(
    request: BulkActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> BulkActionResponse:
    """Perform bulk actions on selected patients."""
    organization_id = current_user.get("organization_id")

    processed = 0
    failed = 0
    errors = []

    for patient_id in request.patient_ids:
        try:
            # Get patient
            result = await db.execute(
                select(Patient).where(
                    Patient.id == patient_id,
                    Patient.organization_id == UUID(organization_id),
                    Patient.is_deleted == False,  # noqa: E712
                )
            )
            patient = result.scalar_one_or_none()

            if not patient:
                failed += 1
                errors.append(f"Patient {patient_id} not found")
                continue

            # Perform action
            if request.action == "archive":
                patient.status = PatientStatus.INACTIVE
            elif request.action == "activate":
                patient.status = PatientStatus.ACTIVE
            elif request.action == "delete":
                patient.is_deleted = True
                patient.deleted_at = func.now()
            # Export is handled separately

            patient.updated_by = UUID(current_user["id"])
            processed += 1

        except Exception as e:
            failed += 1
            errors.append(f"Error processing {patient_id}: {str(e)}")

    if request.action != "export":
        await db.commit()

    return BulkActionResponse(
        success=failed == 0,
        processed_count=processed,
        failed_count=failed,
        errors=errors if errors else [],
    )


# =============================================================================
# Autocomplete Endpoint
# =============================================================================


@router.get(
    "/autocomplete",
    response_model=list[dict],
    summary="Autocomplete patient search",
)
async def autocomplete_patients(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[dict]:
    """Quick autocomplete for patient search."""
    organization_id = current_user.get("organization_id")
    search_term = f"%{q}%"

    query = (
        select(
            Patient.id,
            Patient.mrn,
            Patient.first_name,
            Patient.last_name,
            Patient.date_of_birth,
        )
        .where(
            Patient.organization_id == UUID(organization_id),
            Patient.is_deleted == False,  # noqa: E712
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.mrn.ilike(search_term),
                func.concat(Patient.first_name, " ", Patient.last_name).ilike(search_term),
            ),
        )
        .order_by(Patient.last_name, Patient.first_name)
        .limit(limit)
    )

    result = await db.execute(query)
    patients = result.all()

    return [
        {
            "id": str(p.id),
            "mrn": p.mrn,
            "name": f"{p.first_name} {p.last_name}",
            "dob": p.date_of_birth.isoformat(),
        }
        for p in patients
    ]


# =============================================================================
# Helper Functions
# =============================================================================


def _patient_to_list_item(patient: Patient) -> PatientListItem:
    """Convert Patient model to list item."""
    # Parse JSON fields
    allergies = json.loads(patient.allergies) if patient.allergies else []
    conditions = json.loads(patient.chronic_conditions) if patient.chronic_conditions else []

    return PatientListItem(
        id=patient.id,
        mrn=patient.mrn,
        first_name=patient.first_name,
        last_name=patient.last_name,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        age=patient.age,
        gender=patient.gender,
        phone_primary=patient.phone_primary,
        email=patient.email,
        city=patient.city,
        state=patient.state,
        status=patient.status,
        primary_diagnosis=conditions[0] if conditions else None,
        allergies_count=len(allergies),
        conditions_count=len(conditions),
        last_visit_date=None,  # TODO: Get from visits table
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


async def _get_search_facets(
    db: AsyncSession,
    organization_id: str,
    today: date,
) -> SearchFacets:
    """Get faceted counts for filters."""
    current_year = today.year

    # Status counts
    status_query = (
        select(Patient.status, func.count(Patient.id))
        .where(
            Patient.organization_id == UUID(organization_id),
            Patient.is_deleted == False,  # noqa: E712
        )
        .group_by(Patient.status)
    )
    status_result = await db.execute(status_query)
    status_counts = {str(row[0].value): row[1] for row in status_result.all()}

    # Gender counts
    gender_query = (
        select(Patient.gender, func.count(Patient.id))
        .where(
            Patient.organization_id == UUID(organization_id),
            Patient.is_deleted == False,  # noqa: E712
        )
        .group_by(Patient.gender)
    )
    gender_result = await db.execute(gender_query)
    gender_counts = {str(row[0].value): row[1] for row in gender_result.all()}

    # Age range counts
    age_ranges = {
        "0-17": 0,
        "18-30": 0,
        "31-50": 0,
        "51-70": 0,
        "71+": 0,
    }

    # Get all patients' DOBs for age calculation
    dob_query = select(Patient.date_of_birth).where(
        Patient.organization_id == UUID(organization_id),
        Patient.is_deleted == False,  # noqa: E712
    )
    dob_result = await db.execute(dob_query)
    dobs = [row[0] for row in dob_result.all()]

    for dob in dobs:
        age = current_year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age <= 17:
            age_ranges["0-17"] += 1
        elif age <= 30:
            age_ranges["18-30"] += 1
        elif age <= 50:
            age_ranges["31-50"] += 1
        elif age <= 70:
            age_ranges["51-70"] += 1
        else:
            age_ranges["71+"] += 1

    # Top conditions (parse JSON and aggregate)
    # This is expensive - should be cached or pre-computed in production
    conditions_query = select(Patient.chronic_conditions).where(
        Patient.organization_id == UUID(organization_id),
        Patient.is_deleted == False,  # noqa: E712
        Patient.chronic_conditions.isnot(None),
        Patient.chronic_conditions != "[]",
    )
    conditions_result = await db.execute(conditions_query)

    condition_counts: dict[str, int] = {}
    for row in conditions_result.all():
        if row[0]:
            try:
                conditions = json.loads(row[0])
                for condition in conditions:
                    condition_counts[condition] = condition_counts.get(condition, 0) + 1
            except json.JSONDecodeError:
                pass

    top_conditions = sorted(
        [{"condition": k, "count": v} for k, v in condition_counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )[:10]

    return SearchFacets(
        status=status_counts,
        gender=gender_counts,
        age_ranges=age_ranges,
        top_conditions=top_conditions,
    )
