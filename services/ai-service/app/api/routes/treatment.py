"""
NEURAXIS - Treatment Planning API Endpoints
FastAPI routes for treatment plan generation
"""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.agents.treatment import (
    PatientEducationGenerator,
    TreatmentAgent,
    create_treatment_agent,
)
from app.agents.treatment_schemas import (
    Allergy,
    CurrentMedication,
    DiagnosisInput,
    HepaticFunction,
    InsuranceCoverage,
    LabResult,
    MedicalCondition,
    PatientDemographics,
    RenalFunction,
    TreatmentPlanRequest,
    TreatmentPlanResponse,
)
from app.core.security import get_current_user
from app.models.user import User
from app.services.contraindication_checker import get_contraindication_checker
from app.services.cost_estimation import get_cost_estimation_service
from app.services.dosage_calculator import get_dosage_calculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/treatment-plan", tags=["treatment-ai"])


# =============================================================================
# Rate Limiting
# =============================================================================


class TreatmentRateLimiter:
    """Rate limiter for treatment endpoints."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    def check_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit."""
        import time

        now = time.time()

        if user_id not in self._requests:
            self._requests[user_id] = []

        self._requests[user_id] = [
            t for t in self._requests[user_id] if now - t < self.window_seconds
        ]

        if len(self._requests[user_id]) >= self.max_requests:
            return False

        self._requests[user_id].append(now)
        return True


rate_limiter = TreatmentRateLimiter(max_requests=10, window_seconds=60)


# =============================================================================
# Dependencies
# =============================================================================


async def get_treatment_agent() -> TreatmentAgent:
    """Get treatment agent instance."""
    return create_treatment_agent()


async def check_rate_limit(
    current_user: User = Depends(get_current_user),
) -> User:
    """Check rate limit."""
    if not rate_limiter.check_limit(str(current_user.id)):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
        )
    return current_user


# =============================================================================
# Safety Middleware
# =============================================================================


def validate_request_safety(request: TreatmentPlanRequest) -> list[str]:
    """
    Validate request for obvious safety issues before processing.

    Returns:
        List of warning messages
    """
    warnings = []

    # Validate patient age
    if request.patient.age < 0 or request.patient.age > 150:
        raise HTTPException(status_code=400, detail="Invalid patient age")

    # Validate weight if provided
    if request.patient.weight_kg and (
        request.patient.weight_kg < 1 or request.patient.weight_kg > 500
    ):
        raise HTTPException(status_code=400, detail="Invalid patient weight")

    # Check for missing critical information
    if not request.patient.weight_kg and request.patient.age < 18:
        warnings.append("Pediatric patient without weight - weight-based dosing not possible")

    # Check for life-threatening allergies
    for allergy in request.allergies:
        if allergy.severity == "severe":
            warnings.append(f"Severe allergy to {allergy.allergen} documented")

    # Validate ICD-10 code format
    icd10 = request.diagnosis.icd10_code
    if not icd10 or len(icd10) < 3:
        warnings.append("Invalid or missing ICD-10 code")

    return warnings


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("", response_model=TreatmentPlanResponse)
async def generate_treatment_plan(
    request: TreatmentPlanRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(check_rate_limit),
    agent: TreatmentAgent = Depends(get_treatment_agent),
):
    """
    Generate comprehensive treatment plan.

    This endpoint uses Claude Sonnet 4 to generate personalized treatment
    recommendations including:

    - **First-line medications** with dosing, instructions, and costs
    - **Alternative treatments** if first-line fails
    - **Procedures/interventions** needed
    - **Lifestyle modifications** (diet, exercise, etc.)
    - **Follow-up schedule** with monitoring items
    - **Patient education** content

    **Safety Features:**
    - Allergy checking with cross-reactivity
    - Drug-drug interaction screening
    - Drug-condition contraindication checking
    - Renal/hepatic dose adjustments
    - Dosage validation

    **Note:** All recommendations must be reviewed by a licensed healthcare provider.
    """
    logger.info(f"Treatment plan request from user {current_user.id}: {request.diagnosis.name}")

    try:
        # Pre-validation
        validation_warnings = validate_request_safety(request)

        # Generate plan
        response = await agent.generate_plan(request)

        # Merge warnings
        if response.warnings:
            response.warnings = validation_warnings + response.warnings
        else:
            response.warnings = validation_warnings

        # Log action in background
        if response.success and request.case_id:
            background_tasks.add_task(
                log_treatment_action,
                request.case_id,
                current_user.id,
                request.diagnosis.icd10_code,
                len(response.plan.first_line_medications) if response.plan else 0,
            )

        return response

    except Exception as e:
        logger.error(f"Treatment plan generation failed: {e}", exc_info=True)
        return TreatmentPlanResponse(
            success=False,
            error=str(e),
        )


@router.post("/quick")
async def quick_treatment_recommendation(
    diagnosis_name: str = Query(..., description="Diagnosis name"),
    icd10_code: str = Query(..., description="ICD-10 code"),
    age: int = Query(..., ge=0, le=150),
    gender: str = Query(...),
    weight_kg: float | None = Query(None),
    allergies: list[str] = Query(default=[]),
    current_user: User = Depends(check_rate_limit),
    agent: TreatmentAgent = Depends(get_treatment_agent),
):
    """
    Quick treatment recommendation with minimal input.

    Useful for rapid consultations when full patient data is not available.
    """
    # Build request from query params
    request = TreatmentPlanRequest(
        diagnosis=DiagnosisInput(
            name=diagnosis_name,
            icd10_code=icd10_code,
        ),
        patient=PatientDemographics(
            age=age,
            gender=gender,
            weight_kg=weight_kg,
        ),
        allergies=[Allergy(allergen=a, severity="unknown") for a in allergies],
    )

    response = await agent.generate_plan(request)

    if response.success and response.plan:
        # Return simplified response
        return {
            "success": True,
            "diagnosis": f"{diagnosis_name} ({icd10_code})",
            "first_line_medications": [
                {
                    "medication": med.generic_name,
                    "brands": med.brand_names,
                    "dose": med.dose,
                    "frequency": med.frequency.value,
                    "route": med.route.value,
                    "instructions": [i.instruction for i in med.special_instructions],
                    "reasoning": med.reasoning[:200] + "..."
                    if len(med.reasoning) > 200
                    else med.reasoning,
                }
                for med in response.plan.first_line_medications[:3]
            ],
            "lifestyle": [
                {"category": l.category, "recommendation": l.recommendation}
                for l in response.plan.lifestyle_modifications
            ],
            "follow_up": response.plan.follow_up_schedule[0].timeframe
            if response.plan.follow_up_schedule
            else None,
            "warnings": response.warnings,
            "processing_time_ms": response.plan.processing_time_ms,
        }
    else:
        return {
            "success": False,
            "error": response.error,
        }


@router.post("/validate-safety")
async def validate_medication_safety(
    medication: str = Query(..., description="Medication to check"),
    allergies: list[str] = Query(default=[]),
    conditions: list[str] = Query(default=[], description="ICD-10 codes"),
    current_medications: list[str] = Query(default=[]),
    current_user: User = Depends(get_current_user),
):
    """
    Validate medication safety without full treatment plan.

    Checks for:
    - Allergy contraindications
    - Drug-drug interactions
    - Drug-condition contraindications
    """
    checker = get_contraindication_checker()

    allergy_objs = [Allergy(allergen=a) for a in allergies]
    condition_objs = [MedicalCondition(name=c, icd10_code=c) for c in conditions]
    med_objs = [CurrentMedication(name=m, dose="", frequency="") for m in current_medications]

    contraindications, interactions = checker.check_all(
        medication,
        allergy_objs,
        condition_objs,
        med_objs,
    )

    is_safe = checker.is_safe(medication, allergy_objs, condition_objs, med_objs)

    return {
        "medication": medication,
        "is_safe": is_safe,
        "contraindications": [
            {
                "reason": c.reason,
                "condition_or_allergy": c.condition_or_allergy,
                "severity": c.severity,
                "alternative": c.alternative_suggested,
            }
            for c in contraindications
        ],
        "interactions": [
            {
                "with_medication": i.medication_2,
                "severity": i.severity.value,
                "description": i.description,
                "management": i.management,
            }
            for i in interactions
        ],
    }


@router.post("/calculate-dose")
async def calculate_medication_dose(
    medication: str = Query(...),
    age: int = Query(..., ge=0, le=150),
    weight_kg: float | None = Query(None),
    height_cm: float | None = Query(None),
    gender: str = Query(...),
    egfr: float | None = Query(None, description="eGFR in mL/min/1.73m²"),
    child_pugh: str | None = Query(None, description="Child-Pugh class (A/B/C)"),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate medication dose with adjustments.

    Calculates appropriate dose based on:
    - Patient weight (for weight-based dosing)
    - Age adjustments
    - Renal function (eGFR)
    - Hepatic function (Child-Pugh)
    """
    calculator = get_dosage_calculator()

    patient = PatientDemographics(
        age=age,
        gender=gender,
        weight_kg=weight_kg,
        height_cm=height_cm,
    )

    renal = RenalFunction(egfr=egfr) if egfr else None

    # Build hepatic if provided
    hepatic = None
    if child_pugh:
        # Create minimal hepatic function to get Child-Pugh working
        bilirubin = 1.5 if child_pugh == "A" else (2.5 if child_pugh == "B" else 4.0)
        albumin = 3.6 if child_pugh == "A" else (3.0 if child_pugh == "B" else 2.5)
        hepatic = HepaticFunction(bilirubin=bilirubin, albumin=albumin)

    result = calculator.calculate_dose(
        medication_name=medication,
        patient=patient,
        renal_function=renal,
        hepatic_function=hepatic,
    )

    return {
        "medication": medication,
        "calculated_dose": result.calculated_dose,
        "calculation_method": result.calculation_method,
        "formula_used": result.formula_used,
        "adjustments": result.adjustments,
        "patient_info": {
            "age": age,
            "weight_kg": weight_kg,
            "egfr": egfr,
            "child_pugh": child_pugh,
        },
    }


@router.get("/cost-estimate")
async def estimate_medication_costs(
    medications: list[str] = Query(..., description="List of medication names"),
    plan_type: str | None = Query(None, description="Insurance plan type"),
    copay_generic: float | None = Query(None),
    copay_brand: float | None = Query(None),
    current_user: User = Depends(get_current_user),
):
    """
    Estimate costs for medication list.

    Returns retail costs and estimated insurance copays.
    """
    cost_service = get_cost_estimation_service()

    insurance = None
    if plan_type or copay_generic or copay_brand:
        insurance = InsuranceCoverage(
            plan_type=plan_type,
            copay_generic=copay_generic,
            copay_brand=copay_brand,
        )

    result = cost_service.estimate_total_monthly_cost(medications, insurance)

    return {
        "medications": result["medications"],
        "totals": {
            "retail_monthly": result["total_retail"],
            "with_insurance_monthly": result["total_with_insurance"],
            "estimated_savings": result["estimated_savings"],
        },
    }


@router.get("/alternatives")
async def find_cheaper_alternatives(
    medication: str = Query(..., description="Current medication"),
    current_user: User = Depends(get_current_user),
):
    """
    Find cheaper alternatives for a medication.

    Returns therapeutically equivalent medications with lower costs.
    """
    cost_service = get_cost_estimation_service()

    alternatives = cost_service.find_cheaper_alternatives(medication)

    return {
        "current_medication": medication,
        "alternatives": alternatives,
    }


@router.get("/education/{category}")
async def get_patient_education(
    category: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get patient education content by category.

    Categories: diabetes, hypertension, heart-failure, copd, etc.
    """
    generator = PatientEducationGenerator()

    education = generator.get_education_for_diagnosis(category)

    return {
        "category": category,
        "education_points": [
            {
                "topic": e.topic,
                "key_message": e.key_message,
                "details": e.details,
                "resources": e.resources,
            }
            for e in education
        ],
    }


@router.get("/health")
async def treatment_health_check():
    """Health check for treatment service."""
    from app.core.config import settings

    anthropic_configured = bool(getattr(settings, "ANTHROPIC_API_KEY", None))

    return JSONResponse(
        status_code=200 if anthropic_configured else 503,
        content={
            "service": "treatment-planning",
            "status": "healthy" if anthropic_configured else "degraded",
            "anthropic_configured": anthropic_configured,
            "model": TreatmentAgent.MODEL if anthropic_configured else None,
            "timestamp": datetime.now().isoformat(),
        },
    )


# =============================================================================
# Background Tasks
# =============================================================================


async def log_treatment_action(
    case_id: str,
    user_id: str,
    icd10_code: str,
    medications_count: int,
):
    """Log treatment plan action for audit."""
    logger.info(
        f"Treatment plan logged - Case: {case_id}, User: {user_id}, "
        f"ICD-10: {icd10_code}, Meds: {medications_count}"
    )
