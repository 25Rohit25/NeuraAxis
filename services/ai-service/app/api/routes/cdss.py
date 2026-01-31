from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.services.cdss.default_rules import get_default_rules
from app.services.cdss.rules_engine import get_rules_engine
from app.services.cdss.schemas import EvaluationRequest, EvaluationResponse

router = APIRouter(tags=["cdss"])

# Initialize engine with defaults
engine = get_rules_engine()
engine.load_rules(get_default_rules())


@router.post("/evaluate-rules", response_model=EvaluationResponse)
async def evaluate_rules(request: EvaluationRequest):
    """
    Evaluate CDSS rules against patient context.
    """
    try:
        response = engine.evaluate(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule evaluation check failed: {str(e)}")


@router.get("/rules", response_model=list)
async def get_active_rules():
    """Return list of active definitions."""
    return engine.rules
