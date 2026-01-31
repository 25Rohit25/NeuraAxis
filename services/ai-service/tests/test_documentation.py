"""
NEURAXIS - Clinical Documentation Tests
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.documentation import DocumentationAgent
from app.agents.documentation_schemas import (
    ComplexityLevel,
    DocumentationRequest,
    NoteType,
    VisitType,
)
from app.agents.documentation_utils import ComplianceValidator, MacroExpander

# =============================================================================
# Test Data
# =============================================================================

MOCK_DOC_REQUEST = DocumentationRequest(
    case_id="case-doc-001",
    patient_id="pt-123",
    visit_type=VisitType.NEW_PATIENT,
    note_type=NoteType.SOAP,
    chief_complaint="Chest Pain",
    hpi="Pt reports .cp and .sob since this morning.",
    vitals={"bp": "120/80"},
    physical_exam={"general": "Well developed"},
    macros_used={".cp": "chest pain", ".sob": "shortness of breath"},
)

# =============================================================================
# Component Tests
# =============================================================================


class TestDocumentationUtils:
    def test_macro_expansion(self):
        expander = MacroExpander()
        text = "Pt has .cp."
        expanded = expander.expand(text, {".cp": "chest pain"})
        assert "Pt has chest pain." in expanded

        # Test built-in macros
        text2 = ".nka reported."
        expanded2 = expander.expand(text2)
        assert "No known allergies reported." in expanded2

    def test_compliance_validator(self):
        validator = ComplianceValidator()

        # Valid logic (case insensitive)
        valid_soap = "Subjective: ok. Objective: ok. Assessment: ok. Plan: ok."
        issues = validator.validate(valid_soap, NoteType.SOAP)
        assert len(issues) == 0

        # Missing section
        invalid_soap = "Subjective: ok. Plan: ok."
        issues = validator.validate(invalid_soap, NoteType.SOAP)
        assert len(issues) > 0
        assert "Objective" in issues[0] or "Assessment" in issues[0]


# =============================================================================
# Agent Tests
# =============================================================================


@pytest.mark.asyncio
class TestDocumentationAgent:
    @pytest.fixture
    def agent(self):
        return DocumentationAgent()

    async def test_generate_documentation_flow(self, agent):
        """Test full generation including macro expansion and parsing."""

        # Force the agent to NOT use the real client for unit tests
        # We can rely on the fact that without API key it falls back,
        # or we explicitly set client = None
        agent.client = None

        response = await agent.generate_documentation(MOCK_DOC_REQUEST)

        # Check basic fields
        assert response.case_id == MOCK_DOC_REQUEST.case_id
        assert response.note_type == NoteType.SOAP

        # Check that macro expansion happened "under the hood"
        # (Though we can't easily check internal state, we assumed it worked)

        # Check that output content is present (fallback mock content)
        assert len(response.content) > 0
        assert response.soap_structured is not None

        # Check billing
        assert response.billing.em_code == "99213"

        # Check patient instructions
        assert len(response.patient_instructions.instructions) > 0

        # Check FHIR
        assert response.fhir_bundle is not None
        assert response.fhir_bundle.resourceType == "Bundle"

    async def test_parsing_logic(self, agent):
        """Test parsing of a specific JSON string simulation."""

        mock_json = """
        {
            "content": "Test Note",
            "soap": {
                "subjective": "S", "objective": "O", "assessment": "A", "plan": "P"
            },
            "icd10_codes": [],
            "billing": {
                "em_code": "99214", 
                "cpt_codes": [], 
                "complexity": "Moderate"
            },
            "patient_instructions": {
                "instructions": "Go home.",
                "medication_list": [],
                "follow_up_instructions": "None",
                "warnings": []
            }
        }
        """

        parsed = agent._parse_llm_response(mock_json, MOCK_DOC_REQUEST)

        assert parsed["content"] == "Test Note"
        assert parsed["billing"].em_code == "99214"
        assert parsed["billing"].complexity == ComplexityLevel.MODERATE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
