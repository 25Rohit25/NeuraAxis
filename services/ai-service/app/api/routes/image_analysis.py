"""
NEURAXIS - Image Analysis API
Endpoints for processing medical images.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.agents.image_analysis import ImageAnalysisAgent, get_image_analysis_agent
from app.agents.image_schemas import ImageAnalysisRequest, ImageAnalysisResponse
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image-analysis", tags=["image-analysis"])


@router.post("/analyze", response_model=ImageAnalysisResponse)
async def analyze_medical_image(
    request: ImageAnalysisRequest,
    current_user: User = Depends(get_current_user),
    agent: ImageAnalysisAgent = Depends(get_image_analysis_agent),
):
    """
    Analyze X-ray, CT, or MRI images.

    Features:
    - Abnormality Detection (ResNet Classifiers)
    - Automated Report Generation (Gemini Vision)
    - Segmentation / Heatmap generation (SAM)
    - Metadata extraction (DICOM)
    """
    try:
        response = await agent.analyze_image(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Image analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal analysis error")
