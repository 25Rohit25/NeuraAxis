"""
NEURAXIS - Diagnostic Agent Output Schemas
Pydantic models for structured AI diagnostic outputs
"""

from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# Enums
# =============================================================================


class UrgencyLevel(str, Enum):
    """Patient urgency classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DiagnosisConfidence(str, Enum):
    """Confidence level categories."""

    VERY_LOW = "very_low"  # < 0.2
    LOW = "low"  # 0.2 - 0.4
    MODERATE = "moderate"  # 0.4 - 0.6
    HIGH = "high"  # 0.6 - 0.8
    VERY_HIGH = "very_high"  # > 0.8


class EvidenceType(str, Enum):
    """Types of clinical evidence."""

    SYMPTOM = "symptom"
    VITAL_SIGN = "vital_sign"
    LAB_RESULT = "lab_result"
    HISTORY = "history"
    PHYSICAL_EXAM = "physical_exam"
    IMAGING = "imaging"
    FAMILY_HISTORY = "family_history"
    MEDICATION = "medication"


# =============================================================================
# Supporting Evidence Models
# =============================================================================


class ClinicalEvidence(BaseModel):
    """Individual piece of clinical evidence."""

    type: EvidenceType
    finding: str
    significance: str = Field(description="How this finding supports or refutes the diagnosis")
    weight: float = Field(ge=0, le=1, description="Importance weight of this evidence")


class ReasoningStep(BaseModel):
    """Single step in the diagnostic reasoning chain."""

    step_number: int
    observation: str = Field(description="Clinical observation or finding")
    inference: str = Field(description="Medical inference from the observation")
    hypothesis_impact: str = Field(description="How this affects diagnostic hypotheses")
    confidence_delta: float = Field(
        ge=-1, le=1, description="Change in confidence for leading diagnosis"
    )


class SuggestedTest(BaseModel):
    """Recommended diagnostic test."""

    test_name: str
    test_type: str = Field(description="Category: lab, imaging, procedure, etc.")
    rationale: str = Field(description="Why this test is recommended")
    priority: str = Field(description="urgent, routine, or optional")
    expected_findings: str = Field(description="What results would confirm/refute diagnosis")
    cpt_code: str | None = Field(default=None, description="CPT code if available")


class RedFlag(BaseModel):
    """Critical warning sign requiring immediate attention."""

    finding: str
    severity: str
    recommended_action: str
    time_sensitivity: str = Field(description="Immediate, hours, days")


# =============================================================================
# Diagnosis Model
# =============================================================================


class Diagnosis(BaseModel):
    """Individual differential diagnosis with full reasoning."""

    # Core information
    name: str = Field(description="Diagnosis name")
    icd10_code: str = Field(description="ICD-10 code")
    icd10_description: str = Field(description="Official ICD-10 description")

    # Probability and confidence
    probability: float = Field(
        ge=0, le=1, description="Probability this is the correct diagnosis (0-1)"
    )
    confidence_score: float = Field(
        ge=0, le=1, description="Confidence in the probability estimate (0-1)"
    )
    confidence_category: DiagnosisConfidence = Field(description="Categorical confidence level")

    # Reasoning
    clinical_reasoning: str = Field(description="Detailed explanation of diagnostic reasoning")
    supporting_evidence: list[ClinicalEvidence] = Field(
        description="Evidence supporting this diagnosis"
    )
    contradicting_evidence: list[ClinicalEvidence] = Field(
        default_factory=list, description="Evidence against this diagnosis"
    )

    # Recommendations
    suggested_tests: list[SuggestedTest] = Field(
        default_factory=list, description="Tests to confirm or rule out this diagnosis"
    )

    # Classification
    is_primary: bool = Field(default=False, description="Whether this is the leading diagnosis")
    category: str = Field(description="Disease category (e.g., infectious, cardiovascular)")

    @field_validator("confidence_category", mode="before")
    @classmethod
    def set_confidence_category(cls, v, info):
        if v is not None:
            return v
        # Derive from confidence_score if not provided
        score = info.data.get("confidence_score", 0.5)
        if score < 0.2:
            return DiagnosisConfidence.VERY_LOW
        elif score < 0.4:
            return DiagnosisConfidence.LOW
        elif score < 0.6:
            return DiagnosisConfidence.MODERATE
        elif score < 0.8:
            return DiagnosisConfidence.HIGH
        else:
            return DiagnosisConfidence.VERY_HIGH


# =============================================================================
# Urgency Assessment Model
# =============================================================================


class UrgencyAssessment(BaseModel):
    """Assessment of clinical urgency."""

    level: UrgencyLevel
    score: float = Field(ge=0, le=1, description="Numerical urgency score")
    reasoning: str = Field(description="Explanation for urgency level")
    red_flags: list[RedFlag] = Field(default_factory=list)
    recommended_timeframe: str = Field(description="Recommended timeframe for treatment/evaluation")
    recommended_setting: str = Field(description="ED, urgent care, primary care, specialist, etc.")


# =============================================================================
# Full Diagnostic Response
# =============================================================================


class DiagnosticAnalysis(BaseModel):
    """Complete diagnostic analysis response from AI agent."""

    # Metadata
    analysis_id: str = Field(description="Unique identifier for this analysis")
    case_id: str | None = Field(default=None, description="Associated case ID")
    model_version: str = Field(description="AI model version used")
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

    # Patient context summary
    patient_summary: str = Field(description="Brief summary of patient presentation")

    # Differential diagnosis
    differential_diagnosis: list[Diagnosis] = Field(
        description="Ranked list of differential diagnoses"
    )
    primary_diagnosis: Diagnosis | None = Field(default=None, description="Most likely diagnosis")

    # Reasoning
    reasoning_chain: list[ReasoningStep] = Field(description="Step-by-step diagnostic reasoning")
    clinical_summary: str = Field(description="Overall clinical interpretation")

    # Urgency
    urgency_assessment: UrgencyAssessment

    # Recommendations
    immediate_actions: list[str] = Field(
        default_factory=list, description="Actions to take immediately"
    )
    additional_history_needed: list[str] = Field(
        default_factory=list, description="Additional history questions"
    )

    # Confidence metrics
    overall_confidence: float = Field(ge=0, le=1, description="Overall confidence in the analysis")
    data_quality_score: float = Field(ge=0, le=1, description="Assessment of input data quality")

    # Safety
    disclaimer: str = Field(
        default=(
            "This AI-generated analysis is for clinical decision support only. "
            "It does not replace professional medical judgment. "
            "All findings must be reviewed and validated by a qualified physician."
        )
    )
    requires_physician_review: bool = Field(default=True)

    # Token usage
    tokens_used: int | None = Field(default=None)
    processing_time_ms: int | None = Field(default=None)


# =============================================================================
# Request Models
# =============================================================================


class SymptomInput(BaseModel):
    """Patient symptom for analysis."""

    name: str
    severity: int = Field(ge=1, le=10, description="Severity 1-10")
    duration: str | None = None
    duration_unit: str | None = None
    location: str | None = None
    character: str | None = None
    onset: str | None = None
    is_primary: bool = False


class VitalSignsInput(BaseModel):
    """Patient vital signs."""

    blood_pressure_systolic: int | None = None
    blood_pressure_diastolic: int | None = None
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    temperature: float | None = None
    temperature_unit: str = "F"
    oxygen_saturation: float | None = None
    weight: float | None = None
    weight_unit: str = "kg"
    height: float | None = None
    height_unit: str = "cm"


class LabResultInput(BaseModel):
    """Lab test result."""

    test_name: str
    value: float | str
    unit: str
    normal_min: float | None = None
    normal_max: float | None = None
    status: str | None = None  # normal, high, low, critical


class MedicalHistoryInput(BaseModel):
    """Patient medical history."""

    conditions: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    surgeries: list[str] = Field(default_factory=list)
    family_history: list[str] = Field(default_factory=list)
    social_history: dict | None = None  # smoking, alcohol, etc.


class PatientContext(BaseModel):
    """Complete patient context for diagnosis."""

    age: int
    gender: str
    chief_complaint: str
    symptoms: list[SymptomInput]
    vital_signs: VitalSignsInput | None = None
    lab_results: list[LabResultInput] = Field(default_factory=list)
    medical_history: MedicalHistoryInput | None = None
    current_medications: list[str] = Field(default_factory=list)
    onset_description: str | None = None
    additional_notes: str | None = None


class DiagnosticRequest(BaseModel):
    """Request for diagnostic analysis."""

    case_id: str | None = None
    patient: PatientContext
    include_reasoning_chain: bool = True
    max_diagnoses: int = Field(default=5, ge=1, le=10)
    include_icd_codes: bool = True
    include_suggested_tests: bool = True


class DiagnosticResponse(BaseModel):
    """API response wrapper for diagnostic analysis."""

    success: bool
    analysis: DiagnosticAnalysis | None = None
    error: str | None = None
    cached: bool = False
    cache_key: str | None = None
