"""
NEURAXIS - Drug Interaction System Schemas
Pydantic models for comprehensive drug safety validation
"""

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class InteractionSeverity(str, Enum):
    """Severity level of a drug interaction."""

    CRITICAL = "critical"  # Absolute contraindication
    MAJOR = "major"  # Serious interaction, requires monitoring/action
    MODERATE = "moderate"  # Monitor patient
    MINOR = "minor"  # Minimal clinical significance
    UNKNOWN = "unknown"


class InteractionType(str, Enum):
    """Type of interaction/alert."""

    DRUG_DRUG = "drug_drug"
    DRUG_ALLERGY = "drug_allergy"
    DRUG_CONDITION = "drug_condition"
    DUPLICATE_THERAPY = "duplicate_therapy"
    DOSAGE_RANGE = "dosage_range"
    PREGNANCY = "pregnancy"
    LACTATION = "lactation"
    QTC_PROLONGATION = "qtc_prolongation"
    GERIATRIC = "geriatric"
    PEDIATRIC = "pediatric"
    FOOD_INTERACTION = "food_interaction"


class PregnancyCategory(str, Enum):
    """FDA Pregnancy Categories."""

    A = "A"  # No risk in human studies
    B = "B"  # No risk in animal studies
    C = "C"  # Risk cannot be ruled out
    D = "D"  # Positive evidence of risk
    X = "X"  # Contraindicated in pregnancy


# =============================================================================
# Input Models
# =============================================================================


class DrugInput(BaseModel):
    """Drug to be validated."""

    drug_name: str
    rxnorm_id: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None


class PatientProfile(BaseModel):
    """Patient clinical profile for validation."""

    patient_id: Optional[str] = None
    age: int
    gender: str
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    is_pregnant: bool = False
    is_breastfeeding: bool = False
    creatinine_clearance: Optional[float] = None  # mL/min
    hepatic_impairment: Optional[str] = None  # mild, moderate, severe (Child-Pugh)
    conditions: List[str] = Field(default_factory=list)  # List of ICD-10 codes or names
    allergies: List[str] = Field(default_factory=list)  # List of allergen names
    current_medications: List[DrugInput] = Field(default_factory=list)


class InteractionCheckRequest(BaseModel):
    """Request to check interactions for a list of drugs."""

    drugs_to_check: List[DrugInput]
    patient_profile: PatientProfile
    include_minor: bool = False


# =============================================================================
# Output Models
# =============================================================================


class InteractionAlert(BaseModel):
    """A specific interaction alert."""

    alert_id: str
    severity: InteractionSeverity
    type: InteractionType
    title: str
    description: str
    clinical_implication: str
    management_recommendation: str
    references: List[str] = Field(default_factory=list)
    conflicting_agents: List[str]  # Names of drugs/conditions involved
    onset: Optional[str] = None  # rapid, delayed
    mechanism: Optional[str] = None  # e.g. CYP3A4 inhibition


class DrugSafetySummary(BaseModel):
    """Safety summary for a single drug."""

    drug_name: str
    pregnancy_category: Optional[PregnancyCategory] = None
    lactation_safety: Optional[str] = None
    qtc_risk: Optional[str] = None  # low, moderate, high
    warnings: List[str] = Field(default_factory=list)


class InteractionCheckResponse(BaseModel):
    """Response containing all identified interactions."""

    alerts: List[InteractionAlert]
    drug_summaries: Dict[str, DrugSafetySummary]  # Keyed by drug name
    has_critical_alerts: bool = False
    has_major_alerts: bool = False
    processing_time_ms: float
    timestamp: str
