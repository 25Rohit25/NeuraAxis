"""
NEURAXIS - Drug Interaction API Routes
FastAPI endpoints for drug safety validation.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.agents.drug_interaction import DrugInteractionAgent, get_drug_interaction_agent
from app.agents.drug_interaction_schemas import (
    DrugInput,
    InteractionAlert,
    InteractionCheckRequest,
    InteractionCheckResponse,
    PatientProfile,
)
from app.core.security import get_current_user
from app.models.user import User
from app.services.rxnorm import get_rxnorm_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drug-interaction", tags=["drug-interaction"])


@router.post("/check", response_model=InteractionCheckResponse)
async def check_drug_interactions(
    request: InteractionCheckRequest,
    agent: DrugInteractionAgent = Depends(get_drug_interaction_agent),
    current_user: User = Depends(get_current_user),
):
    """
    Check for drug interactions and safety alerts.

    Validates:
    - Drug-Drug Interactions
    - Drug-Allergy checks
    - Drug-Condition checks
    - Duplicate therapy
    - Dosage adjustments (renal/age)
    - Pregnancy/Lactation risks
    """
    try:
        # Performance logging can be improved here
        response = await agent.check_interactions(request)
        return response
    except Exception as e:
        logger.error(f"Interaction check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resolve-drug")
async def resolve_drug_name(
    name: str = Query(..., min_length=2),
    current_user: User = Depends(get_current_user),
):
    """
    Resolve a drug name to its RxCUI and canonical name using RxNorm.
    Useful for autocomplete or pre-validation.
    """
    client = get_rxnorm_client()
    rxcui = await client.get_rxcui(name)

    if not rxcui:
        return {"found": False, "query": name}

    props = await client.get_drug_properties(rxcui)

    return {
        "found": True,
        "query": name,
        "rxcui": rxcui,
        "name": props.get("name"),
        "synonym": props.get("synonym"),
        "tty": props.get("tty"),
    }


@router.post("/check-list")
async def check_interaction_list(
    drug_names: List[str],
    age: int,
    gender: str,
    conditions: List[str] = Query(default=[]),
    allergies: List[str] = Query(default=[]),
    agent: DrugInteractionAgent = Depends(get_drug_interaction_agent),
    current_user: User = Depends(get_current_user),
):
    """
    Simplified endpoint to check a list of drug names strings.
    """
    drugs = [DrugInput(drug_name=d) for d in drug_names]
    profile = PatientProfile(age=age, gender=gender, conditions=conditions, allergies=allergies)
    request = InteractionCheckRequest(drugs_to_check=drugs, patient_profile=profile)

    return await agent.check_interactions(request)
