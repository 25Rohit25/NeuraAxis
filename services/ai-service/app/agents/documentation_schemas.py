"""
NEURAXIS - Clinical Documentation Schemas
Data models for automated clinical documentation generation.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class NoteType(str, Enum):
    SOAP = "SOAP Note"
    H_AND_P = "History & Physical"
    PROGRESS = "Progress Note"
    DISCHARGE = "Discharge Summary"
    CONSULT = "Consultation Note"
    PROCEDURE = "Procedure Note"
    ER_NOTE = "Emergency Department Note"


class VisitType(str, Enum):
    NEW_PATIENT = "New Patient"
    FOLLOW_UP = "Follow-up"
    ACUTE_VISIT = "Acute Visit"
    ANNUAL_PHYSICAL = "Annual Physical"
    TELEHEALTH = "Telehealth"


class ComplexityLevel(str, Enum):
    STRAIGHTFORWARD = "Straightforward"
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


# =============================================================================
# Input Models
# =============================================================================


class DocumentationRequest(BaseModel):
    """Input data for generating clinical documentation."""

    case_id: str
    patient_id: str
    visit_type: VisitType
    note_type: NoteType
    encounter_date: datetime = Field(default_factory=datetime.now)

    # Clinical Data Inputs
    transcript: Optional[str] = None  # Speech-to-text output
    chief_complaint: str
    hpi: Optional[str] = None  # History of Present Illness
    ros: Optional[Dict[str, Any]] = None  # Review of Systems
    vitals: Dict[str, Any] = Field(default_factory=dict)
    physical_exam: Dict[str, Any] = Field(default_factory=dict)

    # Agent Outputs (to be integrated)
    diagnosis_data: Optional[Dict[str, Any]] = None  # From DiagnosticAgent
    treatment_plan: Optional[Dict[str, Any]] = None  # From TreatmentAgent
    lab_results: Dict[str, Any] = Field(default_factory=dict)
    imaging_results: Dict[str, Any] = Field(default_factory=dict)  # From ImageAnalysis

    # Preferences
    macros_used: Dict[str, str] = Field(default_factory=dict)  # .cc -> ...
    template_id: Optional[str] = None


# =============================================================================
# Output Component Models
# =============================================================================


class SOAPContent(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str


class CodingSuggestion(BaseModel):
    code: str
    description: str
    type: str = "ICD-10"  # or CPT
    confidence: float
    reasoning: str


class BillingInfo(BaseModel):
    em_code: str  # Evaluation & Management code (e.g. 99213)
    cpt_codes: List[CodingSuggestion]
    complexity: ComplexityLevel
    time_spent_minutes: Optional[int] = None


class PatientDocuments(BaseModel):
    instructions: str  # 6th grade reading level
    medication_list: List[str]
    follow_up_instructions: str
    warnings: List[str]


class FHIRBundle(BaseModel):
    """Simplified FHIR Bundle representation."""

    resourceType: str = "Bundle"
    type: str = "document"
    entry: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Final Response Model
# =============================================================================


class DocumentationResponse(BaseModel):
    document_id: str
    case_id: str
    created_at: datetime
    note_type: NoteType

    # Content
    content: str  # The full formatted text
    soap_structured: Optional[SOAPContent] = None  # If applicable

    # Coding & Billing
    icd10_codes: List[CodingSuggestion]
    billing: BillingInfo

    # Patient Facing
    patient_instructions: PatientDocuments

    # Interoperability
    fhir_bundle: Optional[FHIRBundle] = None

    # Validation
    compliance_checks: List[str] = Field(default_factory=list)  # e.g. "Missing ROS"
    is_compliant: bool = True

    model_version: str = "claude-sonnet-4"


# =============================================================================
# Templates
# =============================================================================


class NoteTemplate(BaseModel):
    id: str
    name: str
    type: NoteType
    structure: str  # Markdown template
    required_sections: List[str]
