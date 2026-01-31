"""
NEURAXIS - Patient API Routes
FastAPI endpoints for patient registration and management
"""

import json
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.patient import Patient, PatientStatus
from app.schemas.patient import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    PatientCreate,
    PatientList,
    PatientResponse,
    PatientSummary,
    PatientUpdate,
    PotentialDuplicate,
)
from app.utils.duplicate_detection import check_for_duplicates
from app.utils.mrn import generate_unique_mrn

router = APIRouter(prefix="/patients", tags=["patients"])


# =============================================================================
# Create Patient
# =============================================================================


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
    description="Create a new patient record with comprehensive information",
)
async def create_patient(
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PatientResponse:
    """
    Register a new patient.

    - Validates all input data
    - Checks for potential duplicates
    - Generates unique MRN
    - Creates patient record
    """
    organization_id = current_user.get("organization_id")
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization",
        )

    # Check for duplicates
    duplicates = await check_for_duplicates(
        session=db,
        patient_model=Patient,
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        date_of_birth=patient_data.date_of_birth,
        organization_id=UUID(organization_id),
    )

    if duplicates and duplicates[0].similarity_score >= 0.95:
        # Very high similarity - likely exact duplicate
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "A patient with similar information already exists",
                "existing_mrn": duplicates[0].mrn,
                "similarity_score": duplicates[0].similarity_score,
            },
        )

    # Generate unique MRN
    mrn = await generate_unique_mrn(db, Patient)

    # Prepare patient data
    patient_dict = patient_data.model_dump()

    # Convert lists to JSON strings for storage
    for field in ["allergies", "chronic_conditions", "current_medications", "past_surgeries"]:
        if patient_dict.get(field):
            patient_dict[field] = json.dumps(patient_dict[field])

    # Create patient record
    patient = Patient(
        **patient_dict,
        mrn=mrn,
        organization_id=UUID(organization_id),
        created_by=UUID(current_user["id"]),
        status=PatientStatus.ACTIVE,
    )

    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    return _patient_to_response(patient)


# =============================================================================
# Get Patient
# =============================================================================


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get patient by ID",
)
async def get_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PatientResponse:
    """Get a patient by their ID."""
    organization_id = current_user.get("organization_id")

    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.organization_id == UUID(organization_id),
            Patient.is_deleted == False,  # noqa: E712
        )
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return _patient_to_response(patient)


@router.get(
    "/mrn/{mrn}",
    response_model=PatientResponse,
    summary="Get patient by MRN",
)
async def get_patient_by_mrn(
    mrn: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PatientResponse:
    """Get a patient by their Medical Record Number."""
    organization_id = current_user.get("organization_id")

    result = await db.execute(
        select(Patient).where(
            Patient.mrn == mrn,
            Patient.organization_id == UUID(organization_id),
            Patient.is_deleted == False,  # noqa: E712
        )
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    return _patient_to_response(patient)


# =============================================================================
# List Patients
# =============================================================================


@router.get(
    "/",
    response_model=PatientList,
    summary="List patients",
)
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or MRN"),
    status: Optional[PatientStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PatientList:
    """
    List patients with pagination and filtering.

    - Supports search by name or MRN
    - Filter by status
    - Paginated results
    """
    organization_id = current_user.get("organization_id")

    # Base query
    query = select(Patient).where(
        Patient.organization_id == UUID(organization_id),
        Patient.is_deleted == False,  # noqa: E712
    )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Patient.first_name.ilike(search_term),
                Patient.last_name.ilike(search_term),
                Patient.mrn.ilike(search_term),
                func.concat(Patient.first_name, " ", Patient.last_name).ilike(search_term),
            )
        )

    # Apply status filter
    if status:
        query = query.where(Patient.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Patient.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    patients = result.scalars().all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PatientList(
        items=[_patient_to_summary(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# =============================================================================
# Update Patient
# =============================================================================


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update patient",
)
async def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> PatientResponse:
    """Update a patient's information."""
    organization_id = current_user.get("organization_id")

    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.organization_id == UUID(organization_id),
            Patient.is_deleted == False,  # noqa: E712
        )
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # Update fields
    update_data = patient_data.model_dump(exclude_unset=True)

    # Convert lists to JSON strings
    for field in ["allergies", "chronic_conditions", "current_medications", "past_surgeries"]:
        if field in update_data and update_data[field] is not None:
            update_data[field] = json.dumps(update_data[field])

    for field, value in update_data.items():
        setattr(patient, field, value)

    patient.updated_by = UUID(current_user["id"])

    await db.commit()
    await db.refresh(patient)

    return _patient_to_response(patient)


# =============================================================================
# Delete Patient (Soft Delete)
# =============================================================================


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete patient",
)
async def delete_patient(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    """Soft delete a patient record."""
    organization_id = current_user.get("organization_id")

    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.organization_id == UUID(organization_id),
            Patient.is_deleted == False,  # noqa: E712
        )
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    patient.is_deleted = True
    patient.deleted_at = func.now()
    patient.updated_by = UUID(current_user["id"])

    await db.commit()


# =============================================================================
# Duplicate Detection
# =============================================================================


@router.post(
    "/check-duplicates",
    response_model=DuplicateCheckResponse,
    summary="Check for duplicate patients",
)
async def check_duplicates(
    request: DuplicateCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> DuplicateCheckResponse:
    """
    Check if a patient with similar information already exists.

    Returns potential matches with similarity scores.
    """
    organization_id = current_user.get("organization_id")

    duplicates = await check_for_duplicates(
        session=db,
        patient_model=Patient,
        first_name=request.first_name,
        last_name=request.last_name,
        date_of_birth=request.date_of_birth,
        organization_id=UUID(organization_id),
    )

    return DuplicateCheckResponse(
        has_duplicates=len(duplicates) > 0,
        potential_duplicates=[
            PotentialDuplicate(
                id=d.id,
                mrn=d.mrn,
                full_name=f"{d.first_name} {d.last_name}",
                date_of_birth=d.date_of_birth,
                similarity_score=d.similarity_score,
                match_reason=d.match_reason,
            )
            for d in duplicates
        ],
    )


# =============================================================================
# File Upload
# =============================================================================


@router.post(
    "/{patient_id}/insurance-document",
    response_model=dict,
    summary="Upload insurance document",
)
async def upload_insurance_document(
    patient_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Upload an insurance document for a patient."""
    organization_id = current_user.get("organization_id")

    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed. Allowed: {allowed_types}",
        )

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit",
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )

    # TODO: Upload to cloud storage (S3, GCS, etc.)
    # For now, return a placeholder URL
    document_url = f"/storage/insurance/{patient_id}/{file.filename}"

    patient.insurance_document_url = document_url
    patient.updated_by = UUID(current_user["id"])

    await db.commit()

    return {
        "message": "Document uploaded successfully",
        "document_url": document_url,
    }


# =============================================================================
# Helper Functions
# =============================================================================


def _patient_to_response(patient: Patient) -> PatientResponse:
    """Convert Patient model to PatientResponse."""
    return PatientResponse(
        id=patient.id,
        mrn=patient.mrn,
        organization_id=patient.organization_id,
        first_name=patient.first_name,
        middle_name=patient.middle_name,
        last_name=patient.last_name,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        age=patient.age,
        gender=patient.gender,
        marital_status=patient.marital_status,
        email=patient.email,
        phone_primary=patient.phone_primary,
        phone_secondary=patient.phone_secondary,
        address_line1=patient.address_line1,
        address_line2=patient.address_line2,
        city=patient.city,
        state=patient.state,
        postal_code=patient.postal_code,
        country=patient.country,
        blood_type=patient.blood_type,
        height_cm=patient.height_cm,
        weight_kg=patient.weight_kg,
        allergies=json.loads(patient.allergies) if patient.allergies else [],
        chronic_conditions=json.loads(patient.chronic_conditions)
        if patient.chronic_conditions
        else [],
        current_medications=json.loads(patient.current_medications)
        if patient.current_medications
        else [],
        past_surgeries=json.loads(patient.past_surgeries) if patient.past_surgeries else [],
        family_history=patient.family_history,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_relationship=patient.emergency_contact_relationship,
        emergency_contact_phone=patient.emergency_contact_phone,
        emergency_contact_email=patient.emergency_contact_email,
        insurance_provider=patient.insurance_provider,
        insurance_policy_number=patient.insurance_policy_number,
        insurance_group_number=patient.insurance_group_number,
        insurance_document_url=patient.insurance_document_url,
        status=patient.status,
        created_at=patient.created_at,
        updated_at=patient.updated_at,
    )


def _patient_to_summary(patient: Patient) -> PatientSummary:
    """Convert Patient model to PatientSummary."""
    return PatientSummary(
        id=patient.id,
        mrn=patient.mrn,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth,
        age=patient.age,
        gender=patient.gender,
        phone_primary=patient.phone_primary,
        status=patient.status,
        created_at=patient.created_at,
    )
