"""
NEURAXIS - Diagnostic Agent Unit Tests
Tests with mock OpenAI responses
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agents.diagnostic import (
    ConfidenceCalibrator,
    DiagnosticAgent,
    DiagnosticResponseParser,
    TokenUsageTracker,
    create_diagnostic_agent,
)
from app.agents.icd10_validator import ICD10Validator, get_icd10_validator
from app.agents.schemas import (
    Diagnosis,
    DiagnosisConfidence,
    DiagnosticAnalysis,
    DiagnosticRequest,
    DiagnosticResponse,
    LabResultInput,
    MedicalHistoryInput,
    PatientContext,
    SymptomInput,
    UrgencyLevel,
    VitalSignsInput,
)

# =============================================================================
# Mock Data
# =============================================================================

MOCK_PATIENT_CONTEXT = PatientContext(
    age=45,
    gender="male",
    chief_complaint="Chest pain for 2 hours",
    symptoms=[
        SymptomInput(
            name="Crushing chest pain radiating to left arm",
            severity=8,
            duration="2",
            duration_unit="hours",
            is_primary=True,
        ),
        SymptomInput(
            name="Diaphoresis",
            severity=6,
        ),
        SymptomInput(
            name="Nausea",
            severity=4,
        ),
    ],
    vital_signs=VitalSignsInput(
        blood_pressure_systolic=160,
        blood_pressure_diastolic=95,
        heart_rate=98,
        oxygen_saturation=96,
        temperature=98.6,
    ),
    medical_history=MedicalHistoryInput(
        conditions=["Hypertension", "Type 2 Diabetes"],
        allergies=["Penicillin"],
        family_history=["Father had MI at age 52"],
    ),
    current_medications=["Metformin", "Lisinopril"],
)

MOCK_LLM_RESPONSE = {
    "patient_summary": "45-year-old male with cardiovascular risk factors presenting with acute onset crushing chest pain.",
    "reasoning_chain": [
        {
            "step_number": 1,
            "observation": "Crushing chest pain with left arm radiation",
            "inference": "Classic pattern for myocardial ischemia",
            "hypothesis_impact": "Strongly supports ACS diagnosis",
            "confidence_delta": 0.4,
        },
        {
            "step_number": 2,
            "observation": "Multiple cardiac risk factors",
            "inference": "High pre-test probability for coronary artery disease",
            "hypothesis_impact": "Further increases ACS likelihood",
            "confidence_delta": 0.2,
        },
    ],
    "differential_diagnosis": [
        {
            "name": "Acute STEMI",
            "icd10_code": "I21.3",
            "icd10_description": "ST elevation myocardial infarction of unspecified site",
            "probability": 0.55,
            "confidence_score": 0.75,
            "confidence_category": "high",
            "clinical_reasoning": "Classic presentation with crushing chest pain...",
            "supporting_evidence": [
                {
                    "type": "symptom",
                    "finding": "Crushing chest pain with radiation",
                    "significance": "Highly characteristic of MI",
                    "weight": 0.9,
                }
            ],
            "contradicting_evidence": [],
            "suggested_tests": [
                {
                    "test_name": "12-lead ECG",
                    "test_type": "diagnostic",
                    "rationale": "Assess for ST elevation",
                    "priority": "urgent",
                    "expected_findings": "ST elevation in contiguous leads",
                    "cpt_code": "93000",
                }
            ],
            "is_primary": True,
            "category": "cardiovascular",
        },
        {
            "name": "NSTEMI",
            "icd10_code": "I21.4",
            "icd10_description": "Non-ST elevation myocardial infarction",
            "probability": 0.25,
            "confidence_score": 0.7,
            "confidence_category": "high",
            "clinical_reasoning": "Similar presentation to STEMI...",
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "suggested_tests": [],
            "is_primary": False,
            "category": "cardiovascular",
        },
    ],
    "urgency_assessment": {
        "level": "critical",
        "score": 0.95,
        "reasoning": "Acute coronary syndrome requires immediate intervention",
        "red_flags": [
            {
                "finding": "Crushing chest pain",
                "severity": "critical",
                "recommended_action": "Activate cath lab",
                "time_sensitivity": "immediate",
            }
        ],
        "recommended_timeframe": "Immediate",
        "recommended_setting": "Emergency Department with PCI capability",
    },
    "immediate_actions": ["Activate STEMI protocol", "STAT ECG"],
    "additional_history_needed": [],
    "overall_confidence": 0.85,
    "data_quality_score": 0.9,
    "clinical_summary": "High probability acute coronary syndrome",
}


# =============================================================================
# Token Usage Tracker Tests
# =============================================================================


class TestTokenUsageTracker:
    """Tests for TokenUsageTracker."""

    def test_record_usage(self):
        """Test recording token usage."""
        tracker = TokenUsageTracker()

        record = tracker.record_usage(
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-4o",
            request_id="test-123",
        )

        assert tracker.total_prompt_tokens == 1000
        assert tracker.total_completion_tokens == 500
        assert tracker.total_requests == 1
        assert record["total_tokens"] == 1500
        assert "estimated_cost_usd" in record

    def test_get_summary(self):
        """Test getting usage summary."""
        tracker = TokenUsageTracker()

        tracker.record_usage(100, 50, "gpt-4o", "test-1")
        tracker.record_usage(200, 100, "gpt-4o", "test-2")

        summary = tracker.get_summary()

        assert summary["total_requests"] == 2
        assert summary["total_prompt_tokens"] == 300
        assert summary["total_completion_tokens"] == 150
        assert summary["total_tokens"] == 450

    def test_history_limit(self):
        """Test that history is limited to 1000 records."""
        tracker = TokenUsageTracker()

        # Add more than 1000 records
        for i in range(1100):
            tracker.record_usage(10, 5, "gpt-4o", f"test-{i}")

        assert len(tracker.request_history) == 1000


# =============================================================================
# Confidence Calibrator Tests
# =============================================================================


class TestConfidenceCalibrator:
    """Tests for ConfidenceCalibrator."""

    def test_calibrate_very_high_confidence(self):
        """Very high confidence should be slightly reduced."""
        calibrated = ConfidenceCalibrator.calibrate_confidence(
            raw_confidence=0.95,
            data_quality=0.9,
            num_supporting_evidence=5,
        )

        # Should be adjusted down slightly
        assert calibrated < 0.95
        assert calibrated > 0.85

    def test_calibrate_low_confidence(self):
        """Low confidence should be slightly increased."""
        calibrated = ConfidenceCalibrator.calibrate_confidence(
            raw_confidence=0.25,
            data_quality=0.9,
            num_supporting_evidence=3,
        )

        # Should be adjusted up slightly
        assert calibrated > 0.25

    def test_data_quality_impact(self):
        """Poor data quality should reduce confidence."""
        high_quality = ConfidenceCalibrator.calibrate_confidence(
            raw_confidence=0.7,
            data_quality=0.95,
            num_supporting_evidence=3,
        )

        low_quality = ConfidenceCalibrator.calibrate_confidence(
            raw_confidence=0.7,
            data_quality=0.3,
            num_supporting_evidence=3,
        )

        assert high_quality > low_quality

    def test_confidence_category(self):
        """Test confidence category assignment."""
        assert ConfidenceCalibrator.get_confidence_category(0.1) == DiagnosisConfidence.VERY_LOW
        assert ConfidenceCalibrator.get_confidence_category(0.3) == DiagnosisConfidence.LOW
        assert ConfidenceCalibrator.get_confidence_category(0.5) == DiagnosisConfidence.MODERATE
        assert ConfidenceCalibrator.get_confidence_category(0.7) == DiagnosisConfidence.HIGH
        assert ConfidenceCalibrator.get_confidence_category(0.9) == DiagnosisConfidence.VERY_HIGH


# =============================================================================
# ICD-10 Validator Tests
# =============================================================================


class TestICD10Validator:
    """Tests for ICD10Validator."""

    def test_validate_format_valid(self):
        """Test valid ICD-10 formats."""
        validator = ICD10Validator()

        assert validator.validate_format("I21.3") is True
        assert validator.validate_format("G43.909") is True
        assert validator.validate_format("A00") is True
        assert validator.validate_format("R07.9") is True

    def test_validate_format_invalid(self):
        """Test invalid ICD-10 formats."""
        validator = ICD10Validator()

        assert validator.validate_format("") is False
        assert validator.validate_format("123") is False
        assert validator.validate_format("INVALID") is False
        assert validator.validate_format("I21.") is False

    def test_validate_known_code(self):
        """Test validation of known codes."""
        validator = ICD10Validator()

        is_valid, description = validator.validate_code("I21.3")
        assert is_valid is True
        assert "ST elevation" in description

    def test_get_code_info(self):
        """Test getting code information."""
        validator = ICD10Validator()

        info = validator.get_code_info("I21.3")
        assert info is not None
        assert info.code == "I21.3"
        assert info.category == "Circulatory system"
        assert info.is_billable is True

    def test_search_codes(self):
        """Test code search functionality."""
        validator = ICD10Validator()

        results = validator.search_codes("chest pain", limit=5)
        assert len(results) > 0
        assert any("chest" in r.description.lower() for r in results)

    def test_suggest_code(self):
        """Test code suggestion for diagnosis."""
        validator = ICD10Validator()

        suggestions = validator.suggest_code("myocardial infarction")
        assert len(suggestions) > 0


# =============================================================================
# Response Parser Tests
# =============================================================================


class TestDiagnosticResponseParser:
    """Tests for DiagnosticResponseParser."""

    def test_parse_valid_response(self):
        """Test parsing a valid LLM response."""
        parser = DiagnosticResponseParser()

        analysis = parser.parse_response(
            raw_response=MOCK_LLM_RESPONSE,
            request_id="test-123",
            case_id="case-456",
            model_version="gpt-4o",
            processing_time_ms=2500,
            tokens_used=1500,
        )

        assert isinstance(analysis, DiagnosticAnalysis)
        assert analysis.analysis_id == "test-123"
        assert analysis.case_id == "case-456"
        assert len(analysis.differential_diagnosis) == 2
        assert analysis.primary_diagnosis is not None
        assert analysis.urgency_assessment.level == UrgencyLevel.CRITICAL

    def test_parse_reasoning_chain(self):
        """Test parsing reasoning chain."""
        parser = DiagnosticResponseParser()

        analysis = parser.parse_response(
            raw_response=MOCK_LLM_RESPONSE,
            request_id="test-123",
            case_id=None,
            model_version="gpt-4o",
            processing_time_ms=2000,
            tokens_used=1000,
        )

        assert len(analysis.reasoning_chain) == 2
        assert analysis.reasoning_chain[0].step_number == 1
        assert "chest pain" in analysis.reasoning_chain[0].observation.lower()

    def test_icd_code_validation_in_parser(self):
        """Test ICD code validation during parsing."""
        parser = DiagnosticResponseParser()

        analysis = parser.parse_response(
            raw_response=MOCK_LLM_RESPONSE,
            request_id="test-123",
            case_id=None,
            model_version="gpt-4o",
            processing_time_ms=2000,
            tokens_used=1000,
        )

        # All diagnoses should have valid ICD-10 codes
        for dx in analysis.differential_diagnosis:
            is_valid, _ = parser.icd_validator.validate_code(dx.icd10_code)
            assert is_valid or "Valid code" in dx.icd10_code


# =============================================================================
# Diagnostic Agent Tests
# =============================================================================


class TestDiagnosticAgent:
    """Tests for DiagnosticAgent with mocked LLM."""

    @pytest.fixture
    def mock_agent(self):
        """Create agent with mocked dependencies."""
        with patch("app.agents.diagnostic.ChatOpenAI") as mock_llm:
            agent = DiagnosticAgent(api_key="test-key")
            agent.redis_client = None  # Disable caching
            yield agent

    @pytest.mark.asyncio
    async def test_format_patient_context(self, mock_agent):
        """Test patient context formatting."""
        formatted = mock_agent._format_patient_context(MOCK_PATIENT_CONTEXT)

        assert formatted["age"] == 45
        assert formatted["gender"] == "male"
        assert "chest pain" in formatted["chief_complaint"].lower()
        assert "Crushing" in formatted["symptoms"]
        assert "160/95" in formatted["vital_signs"]

    @pytest.mark.asyncio
    async def test_generate_cache_key(self, mock_agent):
        """Test cache key generation."""
        request = DiagnosticRequest(
            patient=MOCK_PATIENT_CONTEXT,
            max_diagnoses=5,
        )

        key1 = mock_agent._generate_cache_key(request)
        key2 = mock_agent._generate_cache_key(request)

        assert key1 == key2  # Same request = same key
        assert key1.startswith("diagnostic:cache:")

    @pytest.mark.asyncio
    async def test_analyze_success(self, mock_agent):
        """Test successful analysis."""
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.content = json.dumps(MOCK_LLM_RESPONSE)
        mock_response.response_metadata = {
            "token_usage": {"prompt_tokens": 1000, "completion_tokens": 500}
        }

        mock_agent._call_llm = AsyncMock(
            return_value=(
                MOCK_LLM_RESPONSE,
                1000,
                500,
            )
        )

        request = DiagnosticRequest(
            patient=MOCK_PATIENT_CONTEXT,
            max_diagnoses=5,
        )

        response = await mock_agent.analyze(request, use_cache=False)

        assert response.success is True
        assert response.analysis is not None
        assert len(response.analysis.differential_diagnosis) > 0

    @pytest.mark.asyncio
    async def test_analyze_with_error(self, mock_agent):
        """Test analysis with LLM error."""
        mock_agent._call_llm = AsyncMock(side_effect=Exception("API Error"))

        request = DiagnosticRequest(
            patient=MOCK_PATIENT_CONTEXT,
            max_diagnoses=5,
        )

        response = await mock_agent.analyze(request, use_cache=False)

        assert response.success is False
        assert "API Error" in response.error


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestSchemaValidation:
    """Tests for Pydantic schema validation."""

    def test_symptom_input_validation(self):
        """Test symptom input validation."""
        # Valid symptom
        symptom = SymptomInput(
            name="Headache",
            severity=7,
            duration="3",
            duration_unit="days",
        )
        assert symptom.severity == 7

        # Invalid severity should raise error
        with pytest.raises(Exception):
            SymptomInput(name="Headache", severity=15)

    def test_vital_signs_validation(self):
        """Test vital signs validation."""
        vitals = VitalSignsInput(
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            heart_rate=72,
            temperature=98.6,
            oxygen_saturation=98,
        )

        assert vitals.blood_pressure_systolic == 120

    def test_patient_context_required_fields(self):
        """Test patient context required fields."""
        # Missing required fields should raise error
        with pytest.raises(Exception):
            PatientContext(age=45)  # Missing gender, chief_complaint, symptoms

    def test_diagnosis_confidence_bounds(self):
        """Test diagnosis confidence score bounds."""
        # Valid diagnosis
        dx = Diagnosis(
            name="Test",
            icd10_code="R00.0",
            icd10_description="Test description",
            probability=0.5,
            confidence_score=0.7,
            confidence_category=DiagnosisConfidence.HIGH,
            clinical_reasoning="Test reasoning",
            supporting_evidence=[],
            category="Test",
        )

        assert 0 <= dx.probability <= 1
        assert 0 <= dx.confidence_score <= 1


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestFactoryFunction:
    """Tests for agent factory function."""

    def test_create_diagnostic_agent(self):
        """Test creating agent with defaults."""
        with patch("app.agents.diagnostic.ChatOpenAI"):
            with patch.object(DiagnosticAgent, "__init__", lambda self, **kwargs: None):
                agent = create_diagnostic_agent()
                # Just verify it doesn't raise

    def test_create_diagnostic_agent_custom_params(self):
        """Test creating agent with custom parameters."""
        with patch("app.agents.diagnostic.ChatOpenAI"):
            with patch.object(DiagnosticAgent, "__init__", lambda self, **kwargs: None):
                agent = create_diagnostic_agent(
                    model="gpt-4-turbo",
                    temperature=0.2,
                )


# =============================================================================
# Prompt Template Tests
# =============================================================================


class TestPromptTemplates:
    """Tests for prompt template formatting."""

    def test_format_symptoms(self):
        """Test symptom formatting."""
        from app.agents.prompts.diagnostic_template import format_symptoms

        symptoms = [
            SymptomInput(name="Headache", severity=7, is_primary=True),
            SymptomInput(name="Nausea", severity=4),
        ]

        formatted = format_symptoms(symptoms)

        assert "Headache" in formatted
        assert "7/10" in formatted
        assert "[PRIMARY]" in formatted

    def test_format_vitals(self):
        """Test vitals formatting."""
        from app.agents.prompts.diagnostic_template import format_vitals

        vitals = VitalSignsInput(
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            heart_rate=72,
        )

        formatted = format_vitals(vitals)

        assert "120/80" in formatted
        assert "72 bpm" in formatted

    def test_format_labs(self):
        """Test lab results formatting."""
        from app.agents.prompts.diagnostic_template import format_labs

        labs = [
            LabResultInput(
                test_name="Glucose",
                value=126,
                unit="mg/dL",
                normal_min=70,
                normal_max=100,
                status="high",
            ),
        ]

        formatted = format_labs(labs)

        assert "Glucose" in formatted
        assert "126" in formatted
        assert "[HIGH]" in formatted

    def test_format_history(self):
        """Test medical history formatting."""
        from app.agents.prompts.diagnostic_template import format_history

        history = MedicalHistoryInput(
            conditions=["Diabetes", "Hypertension"],
            allergies=["Penicillin"],
            family_history=["Heart disease"],
        )

        formatted = format_history(history)

        assert "Diabetes" in formatted
        assert "Penicillin" in formatted
        assert "Heart disease" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
