"""
NEURAXIS - Patient Profile API
Comprehensive patient profile endpoints with access control
"""

import json
from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.patient import Gender, Patient, PatientStatus

# from app.core.auth import get_current_user, User  # Assume auth module exists
# from app.core.permissions import check_patient_access  # Assume permissions module

router = APIRouter(prefix="/patients/{patient_id}", tags=["patient-profile"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class ProviderInfo(BaseModel):
    id: UUID
    name: str
    specialty: Optional[str] = None


class TimelineEvent(BaseModel):
    id: UUID
    type: str
    title: str
    description: Optional[str] = None
    date: str
    time: Optional[str] = None
    provider: Optional[ProviderInfo] = None
    metadata: Optional[dict] = None


class Medication(BaseModel):
    id: UUID
    name: str
    generic_name: Optional[str] = None
    dosage: str
    frequency: str
    route: str
    start_date: str
    end_date: Optional[str] = None
    prescribed_by: ProviderInfo
    status: str
    refills_remaining: Optional[int] = None
    last_refill_date: Optional[str] = None
    next_refill_date: Optional[str] = None
    instructions: Optional[str] = None
    side_effects: Optional[List[str]] = None
    interactions: Optional[List[str]] = None
    is_controlled: bool = False


class Allergy(BaseModel):
    id: UUID
    allergen: str
    type: str
    severity: str
    reaction: str
    onset_date: Optional[str] = None
    confirmed_by: Optional[str] = None
    notes: Optional[str] = None


class ChronicCondition(BaseModel):
    id: UUID
    name: str
    icd_code: Optional[str] = None
    diagnosis_date: str
    status: str
    severity: Optional[str] = None
    treated_by: Optional[ProviderInfo] = None
    notes: Optional[str] = None
    related_medications: Optional[List[str]] = None


class VitalReading(BaseModel):
    date: str
    value: float
    systolic: Optional[int] = None
    diastolic: Optional[int] = None


class VitalTrend(BaseModel):
    type: str
    label: str
    unit: str
    readings: List[VitalReading]
    latest_value: float
    trend: str  # up, down, stable
    is_abnormal: bool


class LabResult(BaseModel):
    id: UUID
    component: str
    value: Any
    unit: str
    reference_range: str
    status: str  # normal, abnormal_low, abnormal_high, critical
    flag: Optional[str] = None
    notes: Optional[str] = None


class LabTest(BaseModel):
    id: UUID
    test_name: str
    test_code: Optional[str] = None
    category: str
    order_date: str
    result_date: Optional[str] = None
    status: str
    ordered_by: ProviderInfo
    results: List[LabResult]


class MedicalImage(BaseModel):
    id: UUID
    type: str
    body_part: str
    date: str
    thumbnail_url: str
    full_image_url: str
    dicom_url: Optional[str] = None
    ordered_by: ProviderInfo
    radiologist_notes: Optional[str] = None
    findings: Optional[str] = None
    impressions: Optional[str] = None


class PatientDocument(BaseModel):
    id: UUID
    name: str
    category: str
    file_type: str
    file_size: int
    upload_date: str
    uploaded_by: ProviderInfo
    url: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    is_confidential: bool = False


class CareTeamMember(BaseModel):
    id: UUID
    name: str
    role: str
    specialty: Optional[str] = None
    department: Optional[str] = None
    photo_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = False
    assigned_date: str
    notes: Optional[str] = None


class PatientProfile(BaseModel):
    id: UUID
    mrn: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    full_name: str
    date_of_birth: str
    age: int
    gender: str
    marital_status: Optional[str] = None
    blood_type: Optional[str] = None
    photo_url: Optional[str] = None

    email: Optional[str] = None
    phone_primary: str
    phone_secondary: Optional[str] = None

    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str

    emergency_contact_name: str
    emergency_contact_relationship: str
    emergency_contact_phone: str
    emergency_contact_email: Optional[str] = None

    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_group_number: Optional[str] = None
    insurance_document_url: Optional[str] = None

    status: str
    created_at: str
    updated_at: str
    last_visit_date: Optional[str] = None


class EditPermissions(BaseModel):
    can_edit_demographics: bool = False
    can_edit_medications: bool = False
    can_edit_allergies: bool = False
    can_edit_conditions: bool = False
    can_add_vitals: bool = False
    can_upload_documents: bool = False
    can_assign_care_team: bool = False


class PatientProfileResponse(BaseModel):
    profile: PatientProfile
    timeline: List[TimelineEvent]
    medications: List[Medication]
    allergies: List[Allergy]
    conditions: List[ChronicCondition]
    vital_trends: List[VitalTrend]
    lab_results: List[LabTest]
    images: List[MedicalImage]
    documents: List[PatientDocument]
    care_team: List[CareTeamMember]
    has_edit_access: bool
    permissions: Optional[EditPermissions] = None
    last_updated: str


# =============================================================================
# Helper Functions
# =============================================================================


def calculate_age(dob: date) -> int:
    """Calculate age from date of birth."""
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def parse_json_field(value: Optional[str]) -> List[str]:
    """Parse JSON string field to list."""
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return []


async def check_access(patient_id: UUID, user_id: UUID, db: AsyncSession) -> bool:
    """
    Check if user has access to patient.
    In production, implement proper access control:
    - Check if user is assigned to patient's care team
    - Check if user belongs to same organization
    - Check role-based permissions
    """
    # TODO: Implement actual access check
    return True


def get_edit_permissions(user_role: str) -> EditPermissions:
    """Get edit permissions based on user role."""
    if user_role == "admin":
        return EditPermissions(
            can_edit_demographics=True,
            can_edit_medications=True,
            can_edit_allergies=True,
            can_edit_conditions=True,
            can_add_vitals=True,
            can_upload_documents=True,
            can_assign_care_team=True,
        )
    elif user_role == "physician":
        return EditPermissions(
            can_edit_demographics=False,
            can_edit_medications=True,
            can_edit_allergies=True,
            can_edit_conditions=True,
            can_add_vitals=True,
            can_upload_documents=True,
            can_assign_care_team=False,
        )
    elif user_role == "nurse":
        return EditPermissions(
            can_edit_demographics=False,
            can_edit_medications=False,
            can_edit_allergies=True,
            can_edit_conditions=False,
            can_add_vitals=True,
            can_upload_documents=True,
            can_assign_care_team=False,
        )
    else:
        return EditPermissions()


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/profile", response_model=PatientProfileResponse)
async def get_patient_profile(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive patient profile.
    Includes demographics, timeline, medications, allergies, conditions,
    vitals, lab results, images, documents, and care team.
    """
    # Check access (placeholder - implement actual auth)
    # if not await check_access(patient_id, current_user.id, db):
    #     raise HTTPException(status_code=403, detail="Access denied")

    # Fetch patient
    result = await db.execute(
        select(Patient).where(and_(Patient.id == patient_id, Patient.is_deleted == False))
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Build profile response
    profile = PatientProfile(
        id=patient.id,
        mrn=patient.mrn,
        first_name=patient.first_name,
        middle_name=patient.middle_name,
        last_name=patient.last_name,
        full_name=patient.full_name,
        date_of_birth=patient.date_of_birth.isoformat(),
        age=calculate_age(patient.date_of_birth),
        gender=patient.gender.value if hasattr(patient.gender, "value") else str(patient.gender),
        marital_status=patient.marital_status,
        blood_type=patient.blood_type,
        photo_url=None,  # TODO: Implement photo storage
        email=patient.email,
        phone_primary=patient.phone_primary,
        phone_secondary=patient.phone_secondary,
        address_line_1=patient.address_line_1,
        address_line_2=patient.address_line_2,
        city=patient.city,
        state=patient.state,
        postal_code=patient.postal_code,
        country=patient.country or "USA",
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_relationship=patient.emergency_contact_relationship,
        emergency_contact_phone=patient.emergency_contact_phone,
        emergency_contact_email=patient.emergency_contact_email,
        insurance_provider=patient.insurance_provider,
        insurance_policy_number=patient.insurance_policy_number,
        insurance_group_number=patient.insurance_group_number,
        insurance_document_url=patient.insurance_document_url,
        status=patient.status.value if hasattr(patient.status, "value") else str(patient.status),
        created_at=patient.created_at.isoformat(),
        updated_at=patient.updated_at.isoformat(),
        last_visit_date=None,  # TODO: Implement visits table
    )

    # Build allergies from JSON field
    allergies_list = parse_json_field(patient.allergies)
    allergies = [
        Allergy(
            id=patient.id,  # Placeholder - use actual allergy IDs
            allergen=allergy,
            type="drug",  # Default to drug, enhance with actual data
            severity="moderate",
            reaction="Unknown",
        )
        for allergy in allergies_list
    ]

    # Build conditions from JSON field
    conditions_list = parse_json_field(patient.chronic_conditions)
    conditions = [
        ChronicCondition(
            id=patient.id,  # Placeholder
            name=condition,
            diagnosis_date=patient.created_at.isoformat(),
            status="active",
        )
        for condition in conditions_list
    ]

    # TODO: Fetch from actual tables when implemented
    # For now, return demo data structure
    timeline: List[TimelineEvent] = []
    medications: List[Medication] = []
    vital_trends: List[VitalTrend] = []
    lab_results: List[LabTest] = []
    images: List[MedicalImage] = []
    documents: List[PatientDocument] = []
    care_team: List[CareTeamMember] = []

    # Get permissions (placeholder - use actual user)
    permissions = get_edit_permissions("physician")

    return PatientProfileResponse(
        profile=profile,
        timeline=timeline,
        medications=medications,
        allergies=allergies,
        conditions=conditions,
        vital_trends=vital_trends,
        lab_results=lab_results,
        images=images,
        documents=documents,
        care_team=care_team,
        has_edit_access=True,  # TODO: Implement actual check
        permissions=permissions,
        last_updated=datetime.now().isoformat(),
    )


@router.post("/export/pdf")
async def export_patient_pdf(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),
):
    """
    Export patient profile to PDF.
    Generates a comprehensive PDF document with patient information.
    """
    # Check access
    # if not await check_access(patient_id, current_user.id, db):
    #     raise HTTPException(status_code=403, detail="Access denied")

    # Fetch patient
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # TODO: Implement actual PDF generation
    # For now, return a placeholder
    pdf_content = b"%PDF-1.4 placeholder content"

    return StreamingResponse(
        iter([pdf_content]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=patient-{patient.mrn}.pdf"},
    )


@router.get("/timeline")
async def get_patient_timeline(
    patient_id: UUID,
    event_types: Optional[List[str]] = Query(None),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get patient timeline with filtering."""
    # TODO: Implement timeline events table and query
    return {"events": [], "total": 0}


@router.get("/medications")
async def get_patient_medications(
    patient_id: UUID,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get patient medications."""
    # TODO: Implement medications table and query
    return {"medications": []}


@router.get("/vitals")
async def get_patient_vitals(
    patient_id: UUID,
    vital_types: Optional[List[str]] = Query(None),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get patient vitals with trends."""
    # TODO: Implement vitals table and query
    return {"vital_trends": []}


@router.get("/lab-results")
async def get_patient_lab_results(
    patient_id: UUID,
    category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get patient lab results."""
    # TODO: Implement lab results table and query
    return {"lab_tests": []}


@router.get("/images")
async def get_patient_images(
    patient_id: UUID,
    image_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get patient medical images."""
    # TODO: Implement images table and query
    return {"images": []}


@router.get("/documents")
async def get_patient_documents(
    patient_id: UUID,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get patient documents."""
    # TODO: Implement documents table and query
    return {"documents": []}


@router.get("/care-team")
async def get_patient_care_team(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get patient care team."""
    # TODO: Implement care team assignment table and query
    return {"care_team": []}


# =============================================================================
# WebSocket for Real-time Updates
# =============================================================================


class ConnectionManager:
    """Manage WebSocket connections for patient updates."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, patient_id: str, websocket: WebSocket):
        await websocket.accept()
        if patient_id not in self.active_connections:
            self.active_connections[patient_id] = []
        self.active_connections[patient_id].append(websocket)

    def disconnect(self, patient_id: str, websocket: WebSocket):
        if patient_id in self.active_connections:
            self.active_connections[patient_id].remove(websocket)

    async def broadcast(self, patient_id: str, message: dict):
        if patient_id in self.active_connections:
            for connection in self.active_connections[patient_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    patient_id: UUID,
):
    """WebSocket endpoint for real-time patient updates."""
    patient_id_str = str(patient_id)
    await manager.connect(patient_id_str, websocket)

    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Handle incoming messages if needed
    except WebSocketDisconnect:
        manager.disconnect(patient_id_str, websocket)


# Function to broadcast updates (called from other parts of the app)
async def broadcast_patient_update(patient_id: UUID, update_type: str, data: dict):
    """Broadcast update to all connected clients for a patient."""
    await manager.broadcast(
        str(patient_id),
        {"type": update_type, "data": data, "timestamp": datetime.now().isoformat()},
    )
