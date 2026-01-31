"""
NEURAXIS AI Service - Patient Routes
"""

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

router = APIRouter()


class PatientBase(BaseModel):
    """Base patient schema."""
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    medical_record_number: Optional[str] = None


class PatientCreate(PatientBase):
    """Create patient schema."""
    pass


class PatientUpdate(BaseModel):
    """Update patient schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class PatientResponse(PatientBase):
    """Patient response schema."""
    id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PaginatedPatientResponse(BaseModel):
    """Paginated patient response."""
    data: List[PatientResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# Demo data
DEMO_PATIENTS = [
    PatientResponse(
        id=str(uuid4()),
        first_name="John",
        last_name="Doe",
        date_of_birth="1985-03-15",
        gender="male",
        email="john.doe@example.com",
        phone="+1-555-0101",
        medical_record_number="MRN-001-2024",
        created_at="2024-01-15T10:30:00Z",
        updated_at="2024-01-15T10:30:00Z",
    ),
    PatientResponse(
        id=str(uuid4()),
        first_name="Jane",
        last_name="Smith",
        date_of_birth="1990-07-22",
        gender="female",
        email="jane.smith@example.com",
        phone="+1-555-0102",
        medical_record_number="MRN-002-2024",
        created_at="2024-01-16T14:45:00Z",
        updated_at="2024-01-16T14:45:00Z",
    ),
]


@router.get("", response_model=PaginatedPatientResponse)
async def list_patients(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
):
    """
    List all patients with pagination.
    
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 10, max: 100)
    - **search**: Search by name
    """
    # TODO: Implement actual database query
    patients = DEMO_PATIENTS
    
    if search:
        patients = [
            p for p in patients
            if search.lower() in p.first_name.lower()
            or search.lower() in p.last_name.lower()
        ]
    
    total = len(patients)
    total_pages = (total + limit - 1) // limit
    
    return PaginatedPatientResponse(
        data=patients,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    """
    Get a patient by ID.
    
    - **patient_id**: Patient's unique identifier
    """
    # TODO: Implement actual database query
    for patient in DEMO_PATIENTS:
        if patient.id == patient_id:
            return patient
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Patient not found",
    )


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient: PatientCreate):
    """
    Create a new patient.
    """
    # TODO: Implement actual database insert
    new_patient = PatientResponse(
        id=str(uuid4()),
        **patient.model_dump(),
        created_at="2024-01-20T10:00:00Z",
        updated_at="2024-01-20T10:00:00Z",
    )
    return new_patient


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: str, patient: PatientUpdate):
    """
    Update an existing patient.
    
    - **patient_id**: Patient's unique identifier
    """
    # TODO: Implement actual database update
    for p in DEMO_PATIENTS:
        if p.id == patient_id:
            update_data = patient.model_dump(exclude_unset=True)
            updated = p.model_copy(update=update_data)
            return updated
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Patient not found",
    )


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: str):
    """
    Delete a patient.
    
    - **patient_id**: Patient's unique identifier
    """
    # TODO: Implement actual database delete
    return None
