"""
NEURAXIS - Treatment Planning Schemas
Pydantic models for treatment recommendations
"""

from datetime import date, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class MedicationRoute(str, Enum):
    """Route of medication administration."""

    ORAL = "oral"
    IV = "intravenous"
    IM = "intramuscular"
    SC = "subcutaneous"
    TOPICAL = "topical"
    INHALED = "inhaled"
    NASAL = "nasal"
    OPHTHALMIC = "ophthalmic"
    OTIC = "otic"
    RECTAL = "rectal"
    TRANSDERMAL = "transdermal"
    SUBLINGUAL = "sublingual"


class MedicationFrequency(str, Enum):
    """Medication frequency."""

    ONCE_DAILY = "once daily"
    TWICE_DAILY = "twice daily"
    THREE_TIMES_DAILY = "three times daily"
    FOUR_TIMES_DAILY = "four times daily"
    EVERY_4_HOURS = "every 4 hours"
    EVERY_6_HOURS = "every 6 hours"
    EVERY_8_HOURS = "every 8 hours"
    EVERY_12_HOURS = "every 12 hours"
    AS_NEEDED = "as needed"
    ONCE_WEEKLY = "once weekly"
    TWICE_WEEKLY = "twice weekly"
    ONCE_MONTHLY = "once monthly"
    CONTINUOUS = "continuous"


class UrgencyLevel(str, Enum):
    """Treatment urgency."""

    EMERGENT = "emergent"
    URGENT = "urgent"
    ROUTINE = "routine"
    ELECTIVE = "elective"


class InteractionSeverity(str, Enum):
    """Drug interaction severity."""

    CONTRAINDICATED = "contraindicated"
    SEVERE = "severe"
    MODERATE = "moderate"
    MILD = "mild"


class CoverageStatus(str, Enum):
    """Insurance coverage status."""

    COVERED = "covered"
    PRIOR_AUTH_REQUIRED = "prior_authorization_required"
    NOT_COVERED = "not_covered"
    TIER_1 = "tier_1_preferred"
    TIER_2 = "tier_2_standard"
    TIER_3 = "tier_3_non_preferred"
    UNKNOWN = "unknown"


# =============================================================================
# Input Models
# =============================================================================


class PatientDemographics(BaseModel):
    """Patient demographic information."""

    age: int = Field(ge=0, le=150)
    gender: str = Field(description="male, female, other")
    weight_kg: float | None = Field(default=None, ge=0, le=500)
    height_cm: float | None = Field(default=None, ge=0, le=300)

    @property
    def bmi(self) -> float | None:
        """Calculate BMI if height and weight available."""
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m**2), 1)
        return None

    @property
    def bsa(self) -> float | None:
        """Calculate Body Surface Area (Mosteller formula)."""
        if self.weight_kg and self.height_cm:
            return round(((self.weight_kg * self.height_cm) / 3600) ** 0.5, 2)
        return None


class Allergy(BaseModel):
    """Patient allergy information."""

    allergen: str
    reaction: str | None = None
    severity: str = Field(default="unknown", description="mild, moderate, severe, unknown")


class MedicalCondition(BaseModel):
    """Patient medical condition."""

    name: str
    icd10_code: str | None = None
    status: str = Field(default="active", description="active, resolved, chronic")
    onset_date: date | None = None


class CurrentMedication(BaseModel):
    """Current medication patient is taking."""

    name: str
    dose: str
    frequency: str
    route: str | None = None
    indication: str | None = None
    start_date: date | None = None


class LabResult(BaseModel):
    """Laboratory result."""

    test_name: str
    value: float
    unit: str
    normal_min: float | None = None
    normal_max: float | None = None
    status: str | None = Field(default=None, description="normal, low, high, critical")
    date: datetime | None = None


class RenalFunction(BaseModel):
    """Renal function parameters."""

    creatinine: float | None = Field(default=None, description="mg/dL")
    bun: float | None = Field(default=None, description="mg/dL")
    egfr: float | None = Field(default=None, description="mL/min/1.73m²")

    @property
    def ckd_stage(self) -> str | None:
        """Determine CKD stage from eGFR."""
        if self.egfr is None:
            return None
        if self.egfr >= 90:
            return "G1"
        elif self.egfr >= 60:
            return "G2"
        elif self.egfr >= 45:
            return "G3a"
        elif self.egfr >= 30:
            return "G3b"
        elif self.egfr >= 15:
            return "G4"
        else:
            return "G5"


class HepaticFunction(BaseModel):
    """Hepatic function parameters."""

    alt: float | None = Field(default=None, description="U/L")
    ast: float | None = Field(default=None, description="U/L")
    bilirubin: float | None = Field(default=None, description="mg/dL")
    albumin: float | None = Field(default=None, description="g/dL")
    inr: float | None = None

    @property
    def child_pugh_score(self) -> str | None:
        """Simplified Child-Pugh assessment."""
        if self.bilirubin is None or self.albumin is None:
            return None

        score = 0
        # Bilirubin
        if self.bilirubin < 2:
            score += 1
        elif self.bilirubin <= 3:
            score += 2
        else:
            score += 3

        # Albumin
        if self.albumin and self.albumin > 3.5:
            score += 1
        elif self.albumin and self.albumin >= 2.8:
            score += 2
        else:
            score += 3

        # INR
        if self.inr and self.inr < 1.7:
            score += 1
        elif self.inr and self.inr <= 2.3:
            score += 2
        else:
            score += 3

        if score <= 6:
            return "A"
        elif score <= 9:
            return "B"
        else:
            return "C"


class InsuranceCoverage(BaseModel):
    """Insurance coverage information."""

    plan_type: str | None = Field(default=None, description="HMO, PPO, Medicare, Medicaid")
    formulary_tier: int | None = Field(default=None, ge=1, le=5)
    prior_auth_required: bool = False
    copay_generic: float | None = None
    copay_brand: float | None = None
    deductible_remaining: float | None = None


class DiagnosisInput(BaseModel):
    """Primary diagnosis for treatment planning."""

    name: str
    icd10_code: str
    severity: str | None = Field(default=None, description="mild, moderate, severe")
    onset: str | None = Field(default=None, description="acute, chronic, recurrent")


class ResearchFinding(BaseModel):
    """Research finding from Research Agent."""

    finding: str
    evidence_grade: str = Field(description="A, B, or C")
    source_count: int = 0
    recommendation: str | None = None


class TreatmentPlanRequest(BaseModel):
    """Request for treatment plan generation."""

    case_id: str | None = None
    diagnosis: DiagnosisInput
    patient: PatientDemographics
    allergies: list[Allergy] = Field(default_factory=list)
    conditions: list[MedicalCondition] = Field(default_factory=list)
    current_medications: list[CurrentMedication] = Field(default_factory=list)
    lab_results: list[LabResult] = Field(default_factory=list)
    renal_function: RenalFunction | None = None
    hepatic_function: HepaticFunction | None = None
    insurance: InsuranceCoverage | None = None
    research_findings: list[ResearchFinding] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)


# =============================================================================
# Output Models
# =============================================================================


class DosageCalculation(BaseModel):
    """Dosage calculation details."""

    calculated_dose: str
    calculation_method: str = Field(description="weight-based, fixed, bsa-based, age-adjusted")
    formula_used: str | None = None
    adjustments: list[str] = Field(
        default_factory=list, description="renal, hepatic, age adjustments"
    )


class SpecialInstruction(BaseModel):
    """Special instructions for medication."""

    instruction: str
    reason: str | None = None
    timing: str | None = Field(default=None, description="with food, at bedtime, etc.")


class MedicationCost(BaseModel):
    """Cost information for medication."""

    estimated_monthly_cost: float | None = None
    generic_available: bool = False
    generic_cost: float | None = None
    insurance_coverage: CoverageStatus = CoverageStatus.UNKNOWN
    copay_estimate: float | None = None
    prior_auth_notes: str | None = None


class DrugInteraction(BaseModel):
    """Drug-drug interaction warning."""

    medication_1: str
    medication_2: str
    severity: InteractionSeverity
    description: str
    clinical_effect: str
    management: str


class ContraindicationWarning(BaseModel):
    """Contraindication warning."""

    medication: str
    reason: str
    condition_or_allergy: str
    severity: str = Field(description="absolute, relative")
    alternative_suggested: str | None = None


class MedicationRecommendation(BaseModel):
    """Single medication recommendation."""

    medication_id: str
    generic_name: str
    brand_names: list[str] = Field(default_factory=list)
    drug_class: str

    # Dosing
    dose: str
    dosage_calculation: DosageCalculation | None = None
    frequency: MedicationFrequency
    route: MedicationRoute
    duration: str | None = Field(default=None, description="7 days, 2 weeks, ongoing, etc.")

    # Instructions
    special_instructions: list[SpecialInstruction] = Field(default_factory=list)

    # Cost
    cost_info: MedicationCost | None = None

    # Clinical
    indication: str
    mechanism_of_action: str | None = None
    expected_benefit: str
    time_to_effect: str | None = None

    # Reasoning
    reasoning: str = Field(description="Why this medication was chosen")
    evidence_basis: str | None = None
    guideline_reference: str | None = None

    # Priority
    is_first_line: bool = True
    priority_order: int = 1


class ProcedureRecommendation(BaseModel):
    """Procedure or intervention recommendation."""

    procedure_name: str
    cpt_code: str | None = None
    urgency: UrgencyLevel
    description: str
    indication: str
    expected_outcome: str
    risks: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    pre_procedure_requirements: list[str] = Field(default_factory=list)
    estimated_cost: float | None = None
    insurance_notes: str | None = None


class LifestyleModification(BaseModel):
    """Lifestyle modification recommendation."""

    category: str = Field(description="diet, exercise, smoking, alcohol, sleep, stress")
    recommendation: str
    specific_guidance: list[str] = Field(default_factory=list)
    expected_impact: str
    resources: list[str] = Field(default_factory=list)


class FollowUpSchedule(BaseModel):
    """Follow-up appointment schedule."""

    timeframe: str = Field(description="2 weeks, 1 month, 3 months, etc.")
    visit_type: str = Field(description="in-person, telehealth, phone")
    purpose: str
    monitoring_items: list[str] = Field(default_factory=list)
    labs_to_order: list[str] = Field(default_factory=list)
    warning_signs: list[str] = Field(default_factory=list)


class PatientEducationPoint(BaseModel):
    """Patient education content."""

    topic: str
    key_message: str
    details: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)


class SafetyCheck(BaseModel):
    """Safety validation result."""

    check_type: str
    passed: bool
    details: str
    action_required: str | None = None


class TreatmentPlan(BaseModel):
    """Complete treatment plan."""

    plan_id: str
    case_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    # Diagnosis summary
    diagnosis_summary: str
    treatment_goals: list[str] = Field(default_factory=list)

    # Medications
    first_line_medications: list[MedicationRecommendation] = Field(default_factory=list)
    alternative_medications: list[MedicationRecommendation] = Field(default_factory=list)
    medications_to_discontinue: list[str] = Field(default_factory=list)

    # Procedures
    procedures: list[ProcedureRecommendation] = Field(default_factory=list)

    # Lifestyle
    lifestyle_modifications: list[LifestyleModification] = Field(default_factory=list)

    # Follow-up
    follow_up_schedule: list[FollowUpSchedule] = Field(default_factory=list)

    # Education
    patient_education: list[PatientEducationPoint] = Field(default_factory=list)

    # Safety
    contraindications_checked: list[ContraindicationWarning] = Field(default_factory=list)
    drug_interactions: list[DrugInteraction] = Field(default_factory=list)
    safety_checks: list[SafetyCheck] = Field(default_factory=list)

    # Metadata
    urgency_level: UrgencyLevel = UrgencyLevel.ROUTINE
    overall_reasoning: str = ""
    clinical_notes: str | None = None

    # Compliance
    model_version: str = ""
    processing_time_ms: int = 0
    tokens_used: int | None = None

    # Disclaimer
    disclaimer: str = Field(
        default=(
            "This treatment plan is AI-generated and must be reviewed and approved "
            "by a licensed healthcare provider before implementation. Individual patient "
            "circumstances may require modifications to these recommendations."
        )
    )


class TreatmentPlanResponse(BaseModel):
    """API response for treatment plan."""

    success: bool
    plan: TreatmentPlan | None = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
