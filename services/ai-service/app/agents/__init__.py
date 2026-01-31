"""
NEURAXIS - Agents Package
AI agents for medical diagnosis and analysis
"""

from app.agents.diagnostic import (
    ConfidenceCalibrator,
    DiagnosticAgent,
    TokenUsageTracker,
    create_diagnostic_agent,
    token_tracker,
)
from app.agents.icd10_validator import (
    ICD10Validator,
    get_icd10_validator,
    validate_diagnosis_codes,
)
from app.agents.research import (
    CitationFormatter,
    ContradictionDetector,
    QueryExpander,
    ReRanker,
    ResearchAgent,
    ResearchSynthesizer,
    create_research_agent,
)
from app.agents.research_schemas import (
    Citation,
    ClinicalTrial,
    Document,
    EvidenceGrade,
    ResearchQuery,
    ResearchRequest,
    ResearchResponse,
    ResearchResult,
    SourceType,
    StudyType,
)
from app.agents.schemas import (
    Diagnosis,
    DiagnosisConfidence,
    DiagnosticAnalysis,
    DiagnosticRequest,
    DiagnosticResponse,
    LabResultInput,
    MedicalHistoryInput,
    PatientContext,
    SymptomInput,
    UrgencyLevel,
    VitalSignsInput,
)
from app.agents.treatment import (
    PatientEducationGenerator,
    TreatmentAgent,
    create_treatment_agent,
)
from app.agents.treatment_schemas import (
    ContraindicationWarning,
    CoverageStatus,
    DosageCalculation,
    DrugInteraction,
    FollowUpSchedule,
    LifestyleModification,
    MedicationCost,
    MedicationRecommendation,
    PatientEducationPoint,
    ProcedureRecommendation,
    SafetyCheck,
    TreatmentPlan,
    TreatmentPlanRequest,
    TreatmentPlanResponse,
)

__all__ = [
    # Diagnostic Agent
    "DiagnosticAgent",
    "create_diagnostic_agent",
    "TokenUsageTracker",
    "ConfidenceCalibrator",
    "token_tracker",
    # Diagnostic Schemas
    "DiagnosticRequest",
    "DiagnosticResponse",
    "DiagnosticAnalysis",
    "Diagnosis",
    "UrgencyLevel",
    "DiagnosisConfidence",
    "PatientContext",
    "SymptomInput",
    "VitalSignsInput",
    "LabResultInput",
    "MedicalHistoryInput",
    # ICD-10
    "ICD10Validator",
    "get_icd10_validator",
    "validate_diagnosis_codes",
    # Research Agent
    "ResearchAgent",
    "QueryExpander",
    "ReRanker",
    "CitationFormatter",
    "ContradictionDetector",
    "ResearchSynthesizer",
    "create_research_agent",
    # Research Schemas
    "ResearchQuery",
    "ResearchRequest",
    "ResearchResponse",
    "ResearchResult",
    "Document",
    "Citation",
    "ClinicalTrial",
    "EvidenceGrade",
    "SourceType",
    "StudyType",
    # Treatment Agent
    "TreatmentAgent",
    "PatientEducationGenerator",
    "create_treatment_agent",
    # Treatment Schemas
    "TreatmentPlan",
    "TreatmentPlanRequest",
    "TreatmentPlanResponse",
    "MedicationRecommendation",
    "ProcedureRecommendation",
    "LifestyleModification",
    "FollowUpSchedule",
    "PatientEducationPoint",
    "SafetyCheck",
    "DrugInteraction",
    "ContraindicationWarning",
    "DosageCalculation",
    "MedicationCost",
    "CoverageStatus",
]
