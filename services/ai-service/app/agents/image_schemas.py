"""
NEURAXIS - Image Analysis Schemas
Data models for medical image processing and analysis
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field

# =============================================================================
# Enums
# =============================================================================


class ImageModality(str, Enum):
    XRAY = "X-ray"
    CT = "CT"
    MRI = "MRI"
    ULTRASOUND = "Ultrasound"
    DERMOSCOPY = "Dermoscopy"
    OTHER = "Other"


class BodyPart(str, Enum):
    CHEST = "Chest"
    BRAIN = "Brain"
    ABDOMEN = "Abdomen"
    SPINE = "Spine"
    EXTREMITY = "Extremity"
    OTHER = "Other"


class AbnormalityType(str, Enum):
    FRACTURE = "Fracture"
    TUMOR = "Tumor"
    PNEUMONIA = "Pneumonia"
    LESION = "Lesion"
    EDEMA = "Edema"
    HEMORRHAGE = "Hemorrhage"
    OTHER = "Other"


class Severity(str, Enum):
    NORMAL = "Normal"
    MILD = "Mild"
    MODERATE = "Moderate"
    SEVERE = "Severe"
    CRITICAL = "Critical"


# =============================================================================
# Models
# =============================================================================


class BoundingBox(BaseModel):
    """Coordinates for identifying regions of interest."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    label: Optional[str] = None
    confidence: float = 0.0


class Measurement(BaseModel):
    """Quantitative measurement from image."""

    type: str  # e.g. "diameter", "area", "volume", "density"
    value: float
    unit: str  # e.g. "mm", "mm^2", "HU"
    region: Optional[str] = None


class AbnormalityFinding(BaseModel):
    """Detailed finding of an abnormality."""

    type: AbnormalityType
    location: str
    description: str
    confidence: float
    severity: Severity
    bounding_box: Optional[BoundingBox] = None
    measurements: List[Measurement] = Field(default_factory=list)


class ImageMetadata(BaseModel):
    """Metadata extracted from DICOM or file header."""

    patient_id: Optional[str] = None
    study_date: Optional[str] = None
    modality: Optional[ImageModality] = None
    body_part: Optional[BodyPart] = None
    manufacturer: Optional[str] = None
    pixel_spacing: Optional[List[float]] = None  # [row_spacing, col_spacing]


class ImageAnalysisRequest(BaseModel):
    """Request to analyze an image."""

    case_id: str
    image_url: Optional[str] = None
    image_data_base64: Optional[str] = None  # Alternative to URL
    modality: ImageModality = ImageModality.XRAY
    body_part: BodyPart = BodyPart.CHEST
    clinical_context: Optional[str] = None
    compare_with_previous_id: Optional[str] = None


class SegmentationMask(BaseModel):
    """RLE or polygon representation of segmentation."""

    label: str
    counts: Optional[List[int]] = None  # Run-Length Encoding
    contours: Optional[List[List[float]]] = None  # Polygon points


class ImageAnalysisResponse(BaseModel):
    """Complete analysis result."""

    analysis_id: str
    case_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    modality: ImageModality
    metadata: ImageMetadata

    # Findings
    findings: List[AbnormalityFinding]
    impression: str
    recommendations: List[str]

    # Visuals
    heatmap_url: Optional[str] = None  # Overlay image
    annotated_image_url: Optional[str] = None
    segmentation_masks: List[SegmentationMask] = Field(default_factory=list)

    # Performance
    processing_time_ms: float
    model_version: str
    confidence_score: float


class ComparisonResult(BaseModel):
    """Comparison between two scans."""

    baseline_date: str
    current_date: str
    changes: List[str]  # e.g. "Lesion size increased by 20%"
    progression: str  # "Stable", "Improved", "Worsened"
