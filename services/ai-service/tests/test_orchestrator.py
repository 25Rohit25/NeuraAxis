"""
NEURAXIS - Orchestrator Tests
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agents.drug_interaction_schemas import InteractionCheckResponse
from app.agents.orchestrator import CaseAnalysisRequest, Orchestrator, WorkflowState
from app.agents.schemas import Diagnosis, DiagnosticResponse, UrgencyLevel
from app.agents.treatment_schemas import (
    MedicationRecommendation,
    TreatmentPlan,
    TreatmentPlanResponse,
)

# =============================================================================
# Test Data
# =============================================================================

MOCK_REQUEST = CaseAnalysisRequest(
    patient_age=50,
    patient_gender="male",
    chief_complaint="Chest pain",
    symptoms=["Chest pain", "Shortness of breath"],
    history="Hypertension",
    medications=["Lisinopril"],
)

MOCK_DIAGNOSIS = DiagnosticResponse(
    success=True,
    primary_diagnosis=Diagnosis(name="Angina Pectoris", icd10_code="I20.9", confidence=0.9),
    urgency_assessment=MagicMock(level=UrgencyLevel.URGENT),  # Simplified
)

MOCK_TREATMENT = TreatmentPlanResponse(
    success=True,
    plan=TreatmentPlan(
        plan_id="plan-1",
        diagnosis_summary="Angina",
        first_line_medications=[
            MedicationRecommendation(
                generic_name="Nitroglycerin",
                dose="0.4mg",
                frequency="prn",
                route="sublingual",
                indication="Chest pain",
                is_first_line=True,
            )
        ],
    ),
)

MOCK_SAFETY = InteractionCheckResponse(
    alerts=[], drug_summaries={}, processing_time_ms=10, timestamp="123"
)

# =============================================================================
# Tests
# =============================================================================


@pytest.mark.asyncio
class TestOrchestrator:
    @pytest.fixture
    def orchestrator(self):
        return Orchestrator()

    async def test_full_workflow_success(self, orchestrator):
        """Test happy path execution of the workflow."""

        # Mock ALL the get_*_agent functions
        with (
            patch("app.agents.orchestrator.get_diagnostic_agent") as mock_diag_get,
            patch("app.agents.orchestrator.get_research_agent") as mock_research_get,
            patch("app.agents.orchestrator.get_treatment_agent") as mock_treatment_get,
            patch("app.agents.orchestrator.get_drug_interaction_agent") as mock_safety_get,
        ):
            # Setup Agent Mocks
            mock_diag = AsyncMock()
            mock_diag.analyze.return_value = MOCK_DIAGNOSIS
            mock_diag_get.return_value = mock_diag

            mock_research = AsyncMock()
            mock_research.research.return_value = MagicMock(dict=lambda: {})  # Simple mock
            mock_research_get.return_value = mock_research

            mock_treatment = AsyncMock()
            mock_treatment.generate_plan.return_value = MOCK_TREATMENT
            mock_treatment_get.return_value = mock_treatment

            mock_safety = AsyncMock()
            mock_safety.check_interactions.return_value = MOCK_SAFETY
            mock_safety_get.return_value = mock_safety

            # Run
            final_state = await orchestrator.run_analysis(MOCK_REQUEST)

            # Assertions
            assert "diagnostic" in final_state.completed_steps
            assert "treatment" in final_state.completed_steps
            assert "safety" in final_state.completed_steps

            assert final_state.diagnostic_result == MOCK_DIAGNOSIS
            assert final_state.treatment_plan == MOCK_TREATMENT
            assert final_state.safety_cbeck == MOCK_SAFETY

            # Verify data flow
            # Treatment should have received diagnosis "Angina Pectoris"
            # We can check the call args of mock_treatment.generate_plan
            call_args = mock_treatment.generate_plan.call_args[0][0]
            assert call_args.diagnosis.name == "Angina Pectoris"

    async def test_workflow_error_handling(self, orchestrator):
        """Test that workflow handles component failure gracefully."""

        with patch("app.agents.orchestrator.get_diagnostic_agent") as mock_diag_get:
            mock_diag = AsyncMock()
            mock_diag.analyze.side_effect = Exception("Diagnostic service down")
            mock_diag_get.return_value = mock_diag

            # We assume other agents might fail or not run if diag fails
            # In our logic, treatment depends on diag.

            final_state = await orchestrator.run_analysis(MOCK_REQUEST)

            assert "Diagnostic service down" in str(final_state.errors)
            assert "treatment" not in final_state.completed_steps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
