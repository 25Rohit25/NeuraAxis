"""
NEURAXIS - Medical Case API Routes
FastAPI routes for case creation and management
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.case import (
    CaseDraft,
    CaseHistoryItem,
    CaseImage,
    CaseMedication,
    CaseStatus,
    CaseSymptom,
    MedicalCase,
    SymptomDatabase,
    UrgencyLevel,
)
from app.models.patient import Patient

router = APIRouter(prefix="/cases", tags=["cases"])


# =============================================================================
# Pydantic Schemas
# =============================================================================


class SymptomInput(BaseModel):
    code: Optional[str] = None
    name: str
    category: str
    severity: int = Field(ge=1, le=10)
    duration: Optional[str] = None
    notes: Optional[str] = None
    is_ai_suggested: bool = False


class MedicationInput(BaseModel):
    name: str
    dosage: str
    frequency: str
    route: str
    start_date: Optional[str] = None
    prescribed_by: Optional[str] = None
    is_active: bool = True
    is_from_patient_record: bool = False
    compliance: Optional[str] = None


class VitalsInput(BaseModel):
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    heart_rate: int
    temperature: float
    temperature_unit: str
    oxygen_saturation: int
    respiratory_rate: int
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    height: Optional[float] = None
    height_unit: Optional[str] = None
    pain_level: Optional[int] = None
    recorded_at: str


class ChiefComplaintInput(BaseModel):
    complaint: str
    duration: str
    duration_unit: str
    onset: str
    severity: int
    location: Optional[str] = None
    character: Optional[str] = None
    aggravating_factors: Optional[List[str]] = None
    relieving_factors: Optional[List[str]] = None


class PatientInput(BaseModel):
    patient_id: str
    mrn: str
    full_name: str


class HistoryItemInput(BaseModel):
    type: str  # condition, allergy, surgery, family
    name: str
    status: Optional[str] = None
    severity: Optional[str] = None
    diagnosis_date: Optional[str] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None
    is_from_patient_record: bool = False


class AssessmentInput(BaseModel):
    clinical_impression: str
    differential_diagnosis: List[str]
    recommended_tests: List[str]
    treatment_plan: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    urgency_level: str


class CaseCreateInput(BaseModel):
    patient: PatientInput
    chief_complaint: ChiefComplaintInput
    symptoms: List[SymptomInput]
    vitals: VitalsInput
    medications: Optional[List[MedicationInput]] = None
    history_items: Optional[List[HistoryItemInput]] = None
    assessment: AssessmentInput


class CaseResponse(BaseModel):
    id: str
    case_number: str
    patient_id: str
    status: str
    urgency_level: str
    chief_complaint: str
    created_at: str


class DraftInput(BaseModel):
    id: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    chief_complaint: Optional[str] = None
    current_step: int = 0
    data: dict


class DraftResponse(BaseModel):
    id: str
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    chief_complaint: Optional[str] = None
    current_step: int
    data: dict
    created_at: str
    updated_at: str


class SymptomSearchResult(BaseModel):
    id: str
    code: str
    name: str
    category: str
    common_severity: int
    related_symptoms: List[str]


# =============================================================================
# Helper Functions
# =============================================================================


def generate_case_number() -> str:
    """Generate unique case number."""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = str(uuid4())[:6].upper()
    return f"CASE-{timestamp}-{random_part}"


# =============================================================================
# Case Creation Endpoints
# =============================================================================


@router.post("", response_model=CaseResponse)
async def create_case(
    input_data: CaseCreateInput,
    db: AsyncSession = Depends(get_db),
):
    """Create a new medical case."""

    # Verify patient exists
    result = await db.execute(
        select(Patient).where(Patient.id == UUID(input_data.patient.patient_id))
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Create case
    case = MedicalCase(
        case_number=generate_case_number(),
        patient_id=UUID(input_data.patient.patient_id),
        status=CaseStatus.PENDING,
        urgency_level=UrgencyLevel(input_data.assessment.urgency_level),
        # Chief complaint
        chief_complaint=input_data.chief_complaint.complaint,
        complaint_duration=input_data.chief_complaint.duration,
        complaint_duration_unit=input_data.chief_complaint.duration_unit,
        complaint_onset=input_data.chief_complaint.onset,
        complaint_severity=input_data.chief_complaint.severity,
        complaint_location=input_data.chief_complaint.location,
        complaint_character=input_data.chief_complaint.character,
        aggravating_factors=input_data.chief_complaint.aggravating_factors,
        relieving_factors=input_data.chief_complaint.relieving_factors,
        # Vitals
        vitals_bp_systolic=input_data.vitals.blood_pressure_systolic,
        vitals_bp_diastolic=input_data.vitals.blood_pressure_diastolic,
        vitals_heart_rate=input_data.vitals.heart_rate,
        vitals_temperature=input_data.vitals.temperature,
        vitals_temp_unit=input_data.vitals.temperature_unit,
        vitals_o2_saturation=input_data.vitals.oxygen_saturation,
        vitals_respiratory_rate=input_data.vitals.respiratory_rate,
        vitals_weight=input_data.vitals.weight,
        vitals_weight_unit=input_data.vitals.weight_unit,
        vitals_height=input_data.vitals.height,
        vitals_height_unit=input_data.vitals.height_unit,
        vitals_pain_level=input_data.vitals.pain_level,
        vitals_recorded_at=datetime.fromisoformat(
            input_data.vitals.recorded_at.replace("Z", "+00:00")
        ),
        # Assessment
        clinical_impression=input_data.assessment.clinical_impression,
        differential_diagnosis=input_data.assessment.differential_diagnosis,
        recommended_tests=input_data.assessment.recommended_tests,
        treatment_plan=input_data.assessment.treatment_plan,
        follow_up_instructions=input_data.assessment.follow_up_instructions,
    )

    db.add(case)
    await db.flush()  # Get case ID

    # Add symptoms
    for symptom_data in input_data.symptoms:
        symptom = CaseSymptom(
            case_id=case.id,
            code=symptom_data.code,
            name=symptom_data.name,
            category=symptom_data.category,
            severity=symptom_data.severity,
            duration=symptom_data.duration,
            notes=symptom_data.notes,
            is_ai_suggested=symptom_data.is_ai_suggested,
        )
        db.add(symptom)

    # Add medications
    if input_data.medications:
        for med_data in input_data.medications:
            medication = CaseMedication(
                case_id=case.id,
                name=med_data.name,
                dosage=med_data.dosage,
                frequency=med_data.frequency,
                route=med_data.route,
                is_active=med_data.is_active,
                is_from_patient_record=med_data.is_from_patient_record,
                compliance=med_data.compliance,
            )
            db.add(medication)

    # Add history items
    if input_data.history_items:
        for item_data in input_data.history_items:
            history_item = CaseHistoryItem(
                case_id=case.id,
                type=item_data.type,
                name=item_data.name,
                status=item_data.status,
                severity=item_data.severity,
                relationship=item_data.relationship,
                notes=item_data.notes,
                is_from_patient_record=item_data.is_from_patient_record,
            )
            db.add(history_item)

    await db.commit()
    await db.refresh(case)

    return CaseResponse(
        id=str(case.id),
        case_number=case.case_number,
        patient_id=str(case.patient_id),
        status=case.status.value,
        urgency_level=case.urgency_level.value,
        chief_complaint=case.chief_complaint,
        created_at=case.created_at.isoformat(),
    )


@router.get("/{case_id}")
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get case details."""
    result = await db.execute(
        select(MedicalCase)
        .options(
            selectinload(MedicalCase.symptoms),
            selectinload(MedicalCase.medications),
            selectinload(MedicalCase.images),
            selectinload(MedicalCase.history_items),
            selectinload(MedicalCase.patient),
        )
        .where(MedicalCase.id == case_id)
    )
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return {
        "id": str(case.id),
        "case_number": case.case_number,
        "patient": {
            "id": str(case.patient.id),
            "mrn": case.patient.mrn,
            "full_name": case.patient.full_name,
        },
        "status": case.status.value,
        "urgency_level": case.urgency_level.value,
        "chief_complaint": {
            "complaint": case.chief_complaint,
            "duration": case.complaint_duration,
            "duration_unit": case.complaint_duration_unit,
            "onset": case.complaint_onset,
            "severity": case.complaint_severity,
            "location": case.complaint_location,
            "character": case.complaint_character,
            "aggravating_factors": case.aggravating_factors,
            "relieving_factors": case.relieving_factors,
        },
        "vitals": {
            "blood_pressure_systolic": case.vitals_bp_systolic,
            "blood_pressure_diastolic": case.vitals_bp_diastolic,
            "heart_rate": case.vitals_heart_rate,
            "temperature": case.vitals_temperature,
            "temperature_unit": case.vitals_temp_unit,
            "oxygen_saturation": case.vitals_o2_saturation,
            "respiratory_rate": case.vitals_respiratory_rate,
            "pain_level": case.vitals_pain_level,
        },
        "symptoms": [
            {
                "id": str(s.id),
                "code": s.code,
                "name": s.name,
                "category": s.category,
                "severity": s.severity,
                "duration": s.duration,
                "notes": s.notes,
                "is_ai_suggested": s.is_ai_suggested,
            }
            for s in case.symptoms
        ],
        "medications": [
            {
                "id": str(m.id),
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "route": m.route,
                "compliance": m.compliance,
            }
            for m in case.medications
        ],
        "assessment": {
            "clinical_impression": case.clinical_impression,
            "differential_diagnosis": case.differential_diagnosis,
            "recommended_tests": case.recommended_tests,
            "treatment_plan": case.treatment_plan,
            "follow_up_instructions": case.follow_up_instructions,
        },
        "ai_suggestions": case.ai_suggestions,
        "created_at": case.created_at.isoformat(),
    }


# =============================================================================
# Draft Endpoints
# =============================================================================


@router.post("/drafts", response_model=DraftResponse)
async def save_draft(
    input_data: DraftInput,
    db: AsyncSession = Depends(get_db),
):
    """Save or update a case draft."""

    if input_data.id:
        # Update existing draft
        result = await db.execute(select(CaseDraft).where(CaseDraft.id == UUID(input_data.id)))
        draft = result.scalar_one_or_none()

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        draft.patient_id = UUID(input_data.patient_id) if input_data.patient_id else None
        draft.patient_name = input_data.patient_name
        draft.chief_complaint = input_data.chief_complaint
        draft.current_step = input_data.current_step
        draft.data = input_data.data
    else:
        # Create new draft
        draft = CaseDraft(
            patient_id=UUID(input_data.patient_id) if input_data.patient_id else None,
            patient_name=input_data.patient_name,
            chief_complaint=input_data.chief_complaint,
            current_step=input_data.current_step,
            data=input_data.data,
        )
        db.add(draft)

    await db.commit()
    await db.refresh(draft)

    return DraftResponse(
        id=str(draft.id),
        patient_id=str(draft.patient_id) if draft.patient_id else None,
        patient_name=draft.patient_name,
        chief_complaint=draft.chief_complaint,
        current_step=draft.current_step,
        data=draft.data,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


@router.get("/drafts/{draft_id}", response_model=DraftResponse)
async def get_draft(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a case draft."""
    result = await db.execute(select(CaseDraft).where(CaseDraft.id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    return DraftResponse(
        id=str(draft.id),
        patient_id=str(draft.patient_id) if draft.patient_id else None,
        patient_name=draft.patient_name,
        chief_complaint=draft.chief_complaint,
        current_step=draft.current_step,
        data=draft.data,
        created_at=draft.created_at.isoformat(),
        updated_at=draft.updated_at.isoformat(),
    )


@router.get("/drafts")
async def list_drafts(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """List user's case drafts."""
    result = await db.execute(select(CaseDraft).order_by(desc(CaseDraft.updated_at)).limit(limit))
    drafts = result.scalars().all()

    return {
        "drafts": [
            {
                "id": str(d.id),
                "patient_id": str(d.patient_id) if d.patient_id else None,
                "patient_name": d.patient_name,
                "chief_complaint": d.chief_complaint,
                "current_step": d.current_step,
                "updated_at": d.updated_at.isoformat(),
            }
            for d in drafts
        ]
    }


@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a case draft."""
    result = await db.execute(select(CaseDraft).where(CaseDraft.id == draft_id))
    draft = result.scalar_one_or_none()

    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    await db.delete(draft)
    await db.commit()

    return {"status": "deleted"}


# =============================================================================
# Symptom Search Endpoints
# =============================================================================


@router.get("/symptoms/search")
async def search_symptoms(
    q: str = Query(..., min_length=2),
    category: Optional[str] = None,
    limit: int = Query(15, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Search symptom database."""

    query = select(SymptomDatabase).where(
        and_(
            SymptomDatabase.is_active == True,
            or_(
                SymptomDatabase.name.ilike(f"%{q}%"),
                func.json_contains(SymptomDatabase.synonyms, f'"{q}"'),
            ),
        )
    )

    if category:
        query = query.where(SymptomDatabase.category == category)

    query = query.limit(limit)

    result = await db.execute(query)
    symptoms = result.scalars().all()

    return {
        "symptoms": [
            SymptomSearchResult(
                id=str(s.id),
                code=s.code,
                name=s.name,
                category=s.category,
                common_severity=s.common_severity or 5,
                related_symptoms=s.related_symptoms or [],
            )
            for s in symptoms
        ]
    }


@router.get("/symptoms/autocomplete")
async def autocomplete_symptoms(
    q: str = Query(..., min_length=1),
    type: Optional[str] = None,  # complaint, symptom
    limit: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Autocomplete suggestions for symptoms."""

    query = (
        select(SymptomDatabase.name)
        .where(
            and_(
                SymptomDatabase.is_active == True,
                SymptomDatabase.name.ilike(f"{q}%"),
            )
        )
        .limit(limit)
    )

    result = await db.execute(query)
    names = result.scalars().all()

    return {"suggestions": names}


# =============================================================================
# Image Upload Endpoint
# =============================================================================


@router.post("/images/upload")
async def upload_case_image(
    file: UploadFile = File(...),
    type: str = Query("photo"),
    description: Optional[str] = None,
):
    """Upload an image for a case."""

    # TODO: Implement actual file upload to cloud storage (S3, MinIO, etc.)
    # For now, return mock response

    return {
        "id": str(uuid4()),
        "url": f"/uploads/{file.filename}",
        "thumbnailUrl": f"/uploads/thumbs/{file.filename}",
        "type": type,
        "fileName": file.filename,
        "fileSize": 0,  # Would be actual file size
    }
