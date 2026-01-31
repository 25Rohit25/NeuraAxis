"""
NEURAXIS - Clinical Documentation API
Endpoints for generating medical notes and billing documents.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.agents.documentation import DocumentationAgent, get_documentation_agent
from app.agents.documentation_schemas import DocumentationRequest, DocumentationResponse
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documentation", tags=["documentation"])


@router.post("/generate", response_model=DocumentationResponse)
async def generate_clinical_docs(
    request: DocumentationRequest,
    current_user: User = Depends(get_current_user),
    agent: DocumentationAgent = Depends(get_documentation_agent),
):
    """
    Generate comprehensive clinical documentation using GenAI.

    Capabilities:
    - SOAP Notes, H&P, Discharge Summaries
    - ICD-10 & CPT Code Suggestions (with reasoning)
    - Patient Instructions (Layperson language)
    - FHIR Document Bundles
    - Compliance Checking against documentation standards
    """
    try:
        response = await agent.generate_documentation(request)
        return response
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal generation error")
