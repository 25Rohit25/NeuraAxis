"""
NEURAXIS - Orchestrator Schemas
Shared state definitions for the multi-agent workflow.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Union

from pydantic import BaseModel, Field

from app.agents.drug_interaction_schemas import InteractionCheckRequest, InteractionCheckResponse
from app.agents.research_schemas import ResearchRequest, ResearchResponse
from app.agents.schemas import DiagnosticRequest, DiagnosticResponse
from app.agents.treatment_schemas import TreatmentPlanRequest, TreatmentPlanResponse

# =============================================================================
# Workflow State
# =============================================================================


class WorkflowState(BaseModel):
    """
    Shared state object passed between agents in the graph.
    equivalent to LangGraph's State.
    """

    # Case Context
    case_id: str
    user_id: str
    start_time: float

    # Inputs
    patient_data: Dict[str, Any]
    symptoms: List[str]
    medical_images: List[str] = Field(default_factory=list)
    initial_notes: str = ""

    # Agent Outputs (Intermediate State)
    diagnostic_result: Optional[DiagnosticResponse] = None
    research_result: Optional[ResearchResponse] = None
    image_analysis_result: Optional[Dict[str, Any]] = None
    treatment_plan: Optional[TreatmentPlanResponse] = None
    safety_cbeck: Optional[InteractionCheckResponse] = None
    documentation: Optional[str] = None
    documentation_result: Optional[Dict[str, Any]] = None

    # Orchestration meta-data
    errors: List[str] = Field(default_factory=list)
    completed_steps: List[str] = Field(default_factory=list)
    current_step: str = "init"
    tokens_used: int = 0
    total_cost: float = 0.0

    class Config:
        arbitrary_types_allowed = True


# =============================================================================
# API Request/Response
# =============================================================================


class CaseAnalysisRequest(BaseModel):
    """Initial request to start the workflow."""

    case_id: Optional[str] = None
    patient_age: int
    patient_gender: str
    chief_complaint: str
    symptoms: List[str]
    history: str = ""
    medications: List[str] = Field(default_factory=list)
    vital_signs: Dict[str, Any] = Field(default_factory=dict)
    lab_results: Dict[str, Any] = Field(default_factory=dict)
    image_urls: List[str] = Field(default_factory=list)


class WorkflowProgress(BaseModel):
    """Progress update for WebSocket."""

    case_id: str
    step: str
    status: str  # running, completed, error
    timestamp: float
    details: Optional[str] = None
    progress_percentage: int


class CaseAnalysisResult(BaseModel):
    """Final aggregated result."""

    case_id: str
    diagnosis: Dict[str, Any]
    treatment_plan: Dict[str, Any]
    safety_alerts: List[Dict[str, Any]]
    research_summary: Dict[str, Any]
    clinical_notes: str
    metadata: Dict[str, Any]
