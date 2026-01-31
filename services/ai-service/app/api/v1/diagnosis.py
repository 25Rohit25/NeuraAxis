"""
NEURAXIS AI Service - Diagnosis Routes
"""

from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class SymptomInput(BaseModel):
    """Symptom input schema."""
    name: str
    severity: str = Field(..., pattern="^(mild|moderate|severe)$")
    duration_days: Optional[int] = None
    notes: Optional[str] = None


class DiagnosisRequest(BaseModel):
    """Diagnosis request schema."""
    patient_id: str
    symptoms: List[SymptomInput]
    medical_history: Optional[str] = None
    additional_notes: Optional[str] = None


class DifferentialDiagnosis(BaseModel):
    """Differential diagnosis schema."""
    name: str
    icd_code: Optional[str] = None
    probability: float = Field(..., ge=0, le=1)
    reasoning: str


class DiagnosisResponse(BaseModel):
    """Diagnosis response schema."""
    id: str
    patient_id: str
    status: str
    primary_diagnosis: str
    icd_code: Optional[str] = None
    confidence_score: float
    severity: str
    differential_diagnoses: List[DifferentialDiagnosis]
    recommendations: List[str]
    ai_model_version: str
    created_at: str


class DiagnosisListResponse(BaseModel):
    """List of diagnoses response."""
    data: List[DiagnosisResponse]
    total: int


@router.post("", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
async def create_diagnosis(request: DiagnosisRequest):
    """
    Generate an AI-powered diagnosis based on symptoms.
    
    This endpoint accepts patient symptoms and medical history,
    then uses AI models to generate a diagnosis with confidence scores.
    """
    # TODO: Implement actual AI diagnosis logic
    # This is a demo response
    
    diagnosis = DiagnosisResponse(
        id=str(uuid4()),
        patient_id=request.patient_id,
        status="completed",
        primary_diagnosis="Upper Respiratory Infection",
        icd_code="J06.9",
        confidence_score=0.87,
        severity="moderate",
        differential_diagnoses=[
            DifferentialDiagnosis(
                name="Acute Bronchitis",
                icd_code="J20.9",
                probability=0.72,
                reasoning="Symptoms align with bronchial inflammation",
            ),
            DifferentialDiagnosis(
                name="Viral Pharyngitis",
                icd_code="J02.9",
                probability=0.65,
                reasoning="Sore throat and fever patterns suggest viral origin",
            ),
            DifferentialDiagnosis(
                name="Influenza",
                icd_code="J11.1",
                probability=0.45,
                reasoning="Seasonal considerations and symptom overlap",
            ),
        ],
        recommendations=[
            "Rest and adequate hydration",
            "Over-the-counter pain relievers as needed",
            "Monitor for worsening symptoms",
            "Consider follow-up if symptoms persist beyond 7 days",
        ],
        ai_model_version="neuraxis-diagnosis-v1.2.0",
        created_at="2024-01-20T10:00:00Z",
    )
    
    return diagnosis


@router.get("/{diagnosis_id}", response_model=DiagnosisResponse)
async def get_diagnosis(diagnosis_id: str):
    """
    Get a diagnosis by ID.
    
    - **diagnosis_id**: Diagnosis unique identifier
    """
    # TODO: Implement actual database query
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Diagnosis not found",
    )


@router.get("/patient/{patient_id}", response_model=DiagnosisListResponse)
async def get_patient_diagnoses(patient_id: str):
    """
    Get all diagnoses for a patient.
    
    - **patient_id**: Patient's unique identifier
    """
    # TODO: Implement actual database query
    return DiagnosisListResponse(data=[], total=0)


@router.post("/{diagnosis_id}/review")
async def submit_review(
    diagnosis_id: str,
    approved: bool,
    notes: Optional[str] = None,
):
    """
    Submit a clinical review for a diagnosis.
    
    - **diagnosis_id**: Diagnosis unique identifier
    - **approved**: Whether the diagnosis is approved
    - **notes**: Optional review notes
    """
    # TODO: Implement actual review logic
    return {
        "message": "Review submitted successfully",
        "diagnosis_id": diagnosis_id,
        "approved": approved,
        "notes": notes,
    }
