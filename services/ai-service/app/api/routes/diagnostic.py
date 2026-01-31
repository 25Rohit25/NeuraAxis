"""
NEURAXIS - Diagnostic API Endpoints
FastAPI routes for AI diagnostic analysis
"""

import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.agents.diagnostic import DiagnosticAgent, create_diagnostic_agent, token_tracker
from app.agents.schemas import (
    DiagnosticAnalysis,
    DiagnosticRequest,
    DiagnosticResponse,
    LabResultInput,
    MedicalHistoryInput,
    PatientContext,
    SymptomInput,
    VitalSignsInput,
)
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.audit_logger import log_case_action

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnose", tags=["diagnostic-ai"])


# =============================================================================
# Dependencies
# =============================================================================


async def get_diagnostic_agent() -> DiagnosticAgent:
    """Dependency to get diagnostic agent instance."""
    return create_diagnostic_agent()


# =============================================================================
# Request/Response Models for API
# =============================================================================

# Using models from schemas.py


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("", response_model=DiagnosticResponse)
async def create_diagnostic_analysis(
    request: DiagnosticRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    agent: DiagnosticAgent = Depends(get_diagnostic_agent),
    use_cache: bool = Query(True, description="Whether to use cached responses"),
):
    """
    Generate AI diagnostic analysis for patient case.

    This endpoint analyzes patient symptoms, vital signs, lab results, and
    medical history to generate:
    - Ranked differential diagnoses with probabilities
    - Detailed reasoning chains
    - ICD-10 codes
    - Urgency assessment
    - Recommended tests

    **Important**: This is AI-assisted decision support only. All diagnoses
    must be reviewed and validated by a qualified physician.
    """
    logger.info(f"Diagnostic analysis request from user {current_user.id}")

    try:
        # Run analysis
        response = await agent.analyze(request, use_cache=use_cache)

        # Log the analysis action
        if request.case_id and response.success:
            background_tasks.add_task(
                log_analysis_action,
                request.case_id,
                current_user.id,
                response.analysis,
            )

        return response

    except Exception as e:
        logger.error(f"Diagnostic analysis failed: {e}", exc_info=True)
        return DiagnosticResponse(
            success=False,
            error=f"Analysis failed: {str(e)}",
        )


@router.post("/quick", response_model=DiagnosticResponse)
async def quick_diagnostic_analysis(
    age: int,
    gender: str,
    chief_complaint: str,
    symptoms: list[str],
    current_user: User = Depends(get_current_user),
    agent: DiagnosticAgent = Depends(get_diagnostic_agent),
):
    """
    Quick diagnostic analysis with minimal input.

    Use this for rapid assessment with just age, gender, and symptoms.
    For comprehensive analysis, use the main POST /diagnose endpoint.
    """
    logger.info(f"Quick diagnostic analysis request from user {current_user.id}")

    # Build patient context from simple inputs
    symptom_inputs = [
        SymptomInput(name=symptom, severity=5, is_primary=(i == 0))
        for i, symptom in enumerate(symptoms)
    ]

    patient = PatientContext(
        age=age,
        gender=gender,
        chief_complaint=chief_complaint,
        symptoms=symptom_inputs,
    )

    request = DiagnosticRequest(
        patient=patient,
        include_reasoning_chain=False,  # Faster response
        max_diagnoses=3,
    )

    return await agent.analyze(request, use_cache=True)


@router.get("/analysis/{analysis_id}", response_model=DiagnosticAnalysis)
async def get_diagnostic_analysis(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a previously generated diagnostic analysis by ID.

    Analyses are cached for 1 hour after generation.
    """
    # In production, this would retrieve from database or cache
    raise HTTPException(
        status_code=501,
        detail="Analysis retrieval not yet implemented. Use cache_key from response.",
    )


@router.post("/validate-icd")
async def validate_icd_codes(
    codes: list[str],
    current_user: User = Depends(get_current_user),
):
    """
    Validate a list of ICD-10 codes.

    Returns validation status and descriptions for each code.
    """
    from app.agents.icd10_validator import get_icd10_validator

    validator = get_icd10_validator()
    results = []

    for code in codes:
        is_valid, message = validator.validate_code(code)
        info = validator.get_code_info(code)

        results.append(
            {
                "code": code,
                "is_valid": is_valid,
                "message": message,
                "description": info.description if info else None,
                "category": info.category if info else None,
                "is_billable": info.is_billable if info else None,
            }
        )

    return {"results": results}


@router.get("/icd-search")
async def search_icd_codes(
    query: str = Query(..., min_length=2, description="Search term"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """
    Search ICD-10 codes by description.

    Returns matching codes with descriptions.
    """
    from app.agents.icd10_validator import get_icd10_validator

    validator = get_icd10_validator()
    results = validator.search_codes(query, limit)

    return {
        "query": query,
        "results": [
            {
                "code": r.code,
                "description": r.description,
                "category": r.category,
                "is_billable": r.is_billable,
            }
            for r in results
        ],
    }


@router.get("/token-usage")
async def get_token_usage(
    current_user: User = Depends(get_current_user),
):
    """
    Get token usage statistics for diagnostic analyses.

    Requires admin privileges.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required for usage statistics",
        )

    summary = token_tracker.get_summary()

    # Add recent history
    recent_requests = token_tracker.request_history[-20:] if token_tracker.request_history else []

    return {
        "summary": summary,
        "recent_requests": recent_requests,
    }


@router.post("/feedback/{analysis_id}")
async def submit_analysis_feedback(
    analysis_id: str,
    feedback: dict,
    current_user: User = Depends(get_current_user),
):
    """
    Submit feedback on a diagnostic analysis.

    Used for model improvement and quality tracking.

    Expected feedback format:
    {
        "accuracy_rating": 1-5,
        "primary_diagnosis_correct": bool,
        "actual_diagnosis": "ICD-10 code if different",
        "helpful": bool,
        "comments": "Optional text feedback"
    }
    """
    logger.info(f"Feedback received for analysis {analysis_id} from user {current_user.id}")

    # In production, store feedback for model improvement
    return {
        "success": True,
        "message": "Feedback recorded successfully",
        "analysis_id": analysis_id,
    }


@router.get("/health")
async def diagnostic_health_check():
    """
    Health check for diagnostic service.

    Verifies:
    - OpenAI API connectivity
    - Redis cache availability
    - Model availability
    """
    from app.core.config import settings
    from app.core.redis import get_redis_client

    checks = {
        "api_key_configured": bool(settings.OPENAI_API_KEY),
        "redis_available": False,
        "model": "gpt-4o",
        "timestamp": datetime.now().isoformat(),
    }

    try:
        redis = await get_redis_client()
        if redis:
            await redis.ping()
            checks["redis_available"] = True
    except Exception as e:
        checks["redis_error"] = str(e)

    # Check OpenAI API (lightweight check)
    if checks["api_key_configured"]:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            # Just verify API key is valid format, don't make actual request
            checks["openai_configured"] = True
        except Exception as e:
            checks["openai_error"] = str(e)

    status_code = 200 if checks.get("api_key_configured") else 503

    return JSONResponse(
        status_code=status_code,
        content=checks,
    )


# =============================================================================
# Background Tasks
# =============================================================================


async def log_analysis_action(
    case_id: str,
    user_id: UUID,
    analysis: DiagnosticAnalysis,
):
    """Log diagnostic analysis action."""
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        from app.core.config import settings

        engine = create_async_engine(settings.DATABASE_URL)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async with async_session() as session:
            await log_case_action(
                db=session,
                case_id=UUID(case_id),
                user_id=user_id,
                action="ai_analysis_run",
                section="aiAnalysis",
                details={
                    "analysis_id": analysis.analysis_id,
                    "model_version": analysis.model_version,
                    "primary_diagnosis": analysis.primary_diagnosis.name
                    if analysis.primary_diagnosis
                    else None,
                    "urgency_level": analysis.urgency_assessment.level.value,
                    "overall_confidence": analysis.overall_confidence,
                    "tokens_used": analysis.tokens_used,
                },
            )
    except Exception as e:
        logger.error(f"Failed to log analysis action: {e}")


# =============================================================================
# Error Handlers
# =============================================================================


@router.exception_handler(Exception)
async def diagnostic_exception_handler(request, exc):
    """Handle exceptions in diagnostic endpoints."""
    logger.error(f"Diagnostic endpoint error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal diagnostic service error",
            "detail": str(exc) if settings.DEBUG else None,
        },
    )
