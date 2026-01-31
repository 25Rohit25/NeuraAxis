"""
NEURAXIS - Diagnostic Agent Integration Tests
Tests with real OpenAI API (requires API key)
"""

import asyncio
import os
from datetime import datetime
from uuid import uuid4

import pytest

from app.agents.diagnostic import DiagnosticAgent, create_diagnostic_agent
from app.agents.schemas import (
    DiagnosticRequest,
    DiagnosticResponse,
    LabResultInput,
    MedicalHistoryInput,
    PatientContext,
    SymptomInput,
    UrgencyLevel,
    VitalSignsInput,
)

# Skip integration tests if no API key
SKIP_INTEGRATION = not os.environ.get("OPENAI_API_KEY")
SKIP_REASON = "OPENAI_API_KEY environment variable not set"


# =============================================================================
# Test Cases
# =============================================================================

# Cardiac case - should return high urgency with ACS differential
CARDIAC_CASE = PatientContext(
    age=58,
    gender="male",
    chief_complaint="Severe chest pain and shortness of breath for 1 hour",
    symptoms=[
        SymptomInput(
            name="Crushing substernal chest pain radiating to left arm and jaw",
            severity=9,
            duration="1",
            duration_unit="hour",
            location="substernal",
            onset="sudden",
            is_primary=True,
        ),
        SymptomInput(
            name="Shortness of breath",
            severity=7,
        ),
        SymptomInput(
            name="Profuse sweating",
            severity=6,
        ),
        SymptomInput(
            name="Nausea",
            severity=5,
        ),
    ],
    vital_signs=VitalSignsInput(
        blood_pressure_systolic=165,
        blood_pressure_diastolic=100,
        heart_rate=108,
        respiratory_rate=22,
        oxygen_saturation=94,
        temperature=98.8,
    ),
    medical_history=MedicalHistoryInput(
        conditions=["Hypertension", "Hyperlipidemia", "Type 2 Diabetes", "Obesity"],
        allergies=[],
        medications=["Metformin 500mg BID", "Atorvastatin 40mg daily", "Lisinopril 20mg daily"],
        family_history=["Father died of MI at 55", "Brother has CAD"],
        social_history={"smoking": "30 pack-years", "alcohol": "occasional"},
    ),
    current_medications=["Metformin", "Atorvastatin", "Lisinopril"],
    onset_description="Sudden onset while at rest watching TV",
)

# Migraine case - should return low urgency with migraine as primary
MIGRAINE_CASE = PatientContext(
    age=32,
    gender="female",
    chief_complaint="Severe headache for 6 hours with visual disturbance",
    symptoms=[
        SymptomInput(
            name="Throbbing unilateral headache, right temporal region",
            severity=8,
            duration="6",
            duration_unit="hours",
            location="right temporal",
            is_primary=True,
        ),
        SymptomInput(
            name="Visual aura - saw zigzag lines before headache started",
            severity=5,
            duration="20",
            duration_unit="minutes",
        ),
        SymptomInput(
            name="Sensitivity to light",
            severity=7,
        ),
        SymptomInput(
            name="Sensitivity to sound",
            severity=6,
        ),
        SymptomInput(
            name="Nausea without vomiting",
            severity=4,
        ),
    ],
    vital_signs=VitalSignsInput(
        blood_pressure_systolic=118,
        blood_pressure_diastolic=72,
        heart_rate=68,
        temperature=98.4,
        oxygen_saturation=99,
    ),
    medical_history=MedicalHistoryInput(
        conditions=["History of similar headaches since age 18"],
        allergies=["Sulfa drugs"],
        family_history=["Mother has migraines"],
    ),
    onset_description="Started with visual disturbance, followed by headache 20 minutes later",
)

# Respiratory infection case - should return medium urgency
RESPIRATORY_CASE = PatientContext(
    age=45,
    gender="male",
    chief_complaint="Cough, fever, and body aches for 5 days",
    symptoms=[
        SymptomInput(
            name="Productive cough with yellow-green sputum",
            severity=7,
            duration="5",
            duration_unit="days",
            is_primary=True,
        ),
        SymptomInput(
            name="Fever and chills",
            severity=6,
            duration="4",
            duration_unit="days",
        ),
        SymptomInput(
            name="Body aches and fatigue",
            severity=5,
        ),
        SymptomInput(
            name="Shortness of breath on exertion",
            severity=4,
        ),
    ],
    vital_signs=VitalSignsInput(
        blood_pressure_systolic=128,
        blood_pressure_diastolic=82,
        heart_rate=92,
        respiratory_rate=20,
        temperature=101.8,
        oxygen_saturation=95,
    ),
    lab_results=[
        LabResultInput(
            test_name="WBC",
            value=14.2,
            unit="K/uL",
            normal_min=4.5,
            normal_max=11.0,
            status="high",
        ),
        LabResultInput(
            test_name="CRP",
            value=48,
            unit="mg/L",
            normal_min=0,
            normal_max=10,
            status="high",
        ),
    ],
    medical_history=MedicalHistoryInput(
        conditions=["COPD - mild", "Former smoker"],
    ),
    onset_description="Gradual onset over 5 days, progressively worsening",
)


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.skipif(SKIP_INTEGRATION, reason=SKIP_REASON)
class TestDiagnosticAgentIntegration:
    """Integration tests with real OpenAI API."""

    @pytest.fixture(scope="class")
    def agent(self):
        """Create real diagnostic agent."""
        return create_diagnostic_agent(
            model="gpt-4o",
            temperature=0.1,
        )

    @pytest.mark.asyncio
    async def test_cardiac_case_analysis(self, agent):
        """Test analysis of cardiac case."""
        request = DiagnosticRequest(
            case_id=str(uuid4()),
            patient=CARDIAC_CASE,
            include_reasoning_chain=True,
            max_diagnoses=5,
        )

        response = await agent.analyze(request, use_cache=False)

        # Basic assertions
        assert response.success is True
        assert response.analysis is not None

        analysis = response.analysis

        # Should identify acute coronary syndrome
        assert len(analysis.differential_diagnosis) > 0

        primary_dx = analysis.primary_diagnosis
        assert primary_dx is not None

        # Check for cardiac-related diagnosis
        cardiac_keywords = [
            "myocardial",
            "infarction",
            "coronary",
            "ACS",
            "STEMI",
            "NSTEMI",
            "angina",
        ]
        has_cardiac_dx = any(
            any(kw.lower() in dx.name.lower() for kw in cardiac_keywords)
            for dx in analysis.differential_diagnosis
        )
        assert has_cardiac_dx, "Should identify cardiac condition"

        # Should be high/critical urgency
        assert analysis.urgency_assessment.level in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]

        # Should have ICD-10 codes
        for dx in analysis.differential_diagnosis:
            assert dx.icd10_code
            assert dx.icd10_code.startswith("I") or dx.icd10_code.startswith("R")

        # Should have reasoning chain
        assert len(analysis.reasoning_chain) > 0

        # Check confidence scores are in valid range
        for dx in analysis.differential_diagnosis:
            assert 0 <= dx.probability <= 1
            assert 0 <= dx.confidence_score <= 1

        # Should recommend immediate tests
        has_ecg_test = any(
            any(
                "ECG" in test.test_name.upper() or "EKG" in test.test_name.upper()
                for test in dx.suggested_tests
            )
            for dx in analysis.differential_diagnosis
        )
        assert has_ecg_test, "Should recommend ECG for cardiac case"

        # Print summary for manual review
        print(f"\n{'=' * 60}")
        print(f"CARDIAC CASE ANALYSIS")
        print(f"{'=' * 60}")
        print(f"Primary Diagnosis: {primary_dx.name}")
        print(f"ICD-10: {primary_dx.icd10_code}")
        print(f"Probability: {primary_dx.probability:.0%}")
        print(f"Confidence: {primary_dx.confidence_score:.0%}")
        print(f"Urgency: {analysis.urgency_assessment.level.value}")
        print(f"Processing Time: {analysis.processing_time_ms}ms")
        print(f"Tokens Used: {analysis.tokens_used}")

    @pytest.mark.asyncio
    async def test_migraine_case_analysis(self, agent):
        """Test analysis of migraine case."""
        request = DiagnosticRequest(
            patient=MIGRAINE_CASE,
            include_reasoning_chain=True,
            max_diagnoses=5,
        )

        response = await agent.analyze(request, use_cache=False)

        assert response.success is True
        assert response.analysis is not None

        analysis = response.analysis

        # Should identify migraine
        migraine_keywords = ["migraine", "headache"]
        has_migraine_dx = any(
            any(kw.lower() in dx.name.lower() for kw in migraine_keywords)
            for dx in analysis.differential_diagnosis
        )
        assert has_migraine_dx, "Should identify migraine"

        # Should be low/medium urgency (not critical)
        assert analysis.urgency_assessment.level in [UrgencyLevel.LOW, UrgencyLevel.MEDIUM]

        # Print summary
        print(f"\n{'=' * 60}")
        print(f"MIGRAINE CASE ANALYSIS")
        print(f"{'=' * 60}")
        print(f"Primary Diagnosis: {analysis.primary_diagnosis.name}")
        print(f"ICD-10: {analysis.primary_diagnosis.icd10_code}")
        print(f"Urgency: {analysis.urgency_assessment.level.value}")

    @pytest.mark.asyncio
    async def test_respiratory_case_analysis(self, agent):
        """Test analysis of respiratory infection case."""
        request = DiagnosticRequest(
            patient=RESPIRATORY_CASE,
            include_reasoning_chain=True,
            max_diagnoses=5,
            include_suggested_tests=True,
        )

        response = await agent.analyze(request, use_cache=False)

        assert response.success is True
        assert response.analysis is not None

        analysis = response.analysis

        # Should identify respiratory infection
        respiratory_keywords = ["pneumonia", "bronchitis", "respiratory", "infection"]
        has_respiratory_dx = any(
            any(kw.lower() in dx.name.lower() for kw in respiratory_keywords)
            for dx in analysis.differential_diagnosis
        )
        assert has_respiratory_dx, "Should identify respiratory condition"

        # Should consider the lab results
        assert analysis.data_quality_score > 0.7, "Good data quality with labs"

        # Print summary
        print(f"\n{'=' * 60}")
        print(f"RESPIRATORY CASE ANALYSIS")
        print(f"{'=' * 60}")
        print(f"Primary Diagnosis: {analysis.primary_diagnosis.name}")
        print(f"ICD-10: {analysis.primary_diagnosis.icd10_code}")
        print(f"Urgency: {analysis.urgency_assessment.level.value}")

    @pytest.mark.asyncio
    async def test_caching_works(self, agent):
        """Test that caching returns same analysis."""
        request = DiagnosticRequest(
            patient=MIGRAINE_CASE,
            max_diagnoses=3,
        )

        # First request - should not be cached
        response1 = await agent.analyze(request, use_cache=True)
        assert response1.success is True
        assert response1.cached is False

        # Second request - should be cached (if Redis available)
        response2 = await agent.analyze(request, use_cache=True)
        assert response2.success is True

        # If caching works, second should be cached
        # (may not be if Redis is unavailable)
        if response2.cached:
            print("✓ Caching working correctly")
            assert response2.cache_key == response1.cache_key

    @pytest.mark.asyncio
    async def test_response_structure_complete(self, agent):
        """Test that response has all expected fields."""
        request = DiagnosticRequest(
            patient=CARDIAC_CASE,
            include_reasoning_chain=True,
            max_diagnoses=5,
            include_icd_codes=True,
            include_suggested_tests=True,
        )

        response = await agent.analyze(request, use_cache=False)

        assert response.success is True
        analysis = response.analysis

        # Check all required fields
        assert analysis.analysis_id
        assert analysis.model_version
        assert analysis.analysis_timestamp
        assert analysis.patient_summary
        assert analysis.differential_diagnosis
        assert analysis.primary_diagnosis
        assert analysis.reasoning_chain
        assert analysis.urgency_assessment
        assert analysis.overall_confidence >= 0
        assert analysis.data_quality_score >= 0
        assert analysis.disclaimer
        assert analysis.requires_physician_review is True

        # Check diagnosis structure
        dx = analysis.differential_diagnosis[0]
        assert dx.name
        assert dx.icd10_code
        assert dx.probability >= 0
        assert dx.confidence_score >= 0
        assert dx.clinical_reasoning
        assert dx.category

    @pytest.mark.asyncio
    async def test_safety_disclaimer_present(self, agent):
        """Test that safety disclaimer is always present."""
        request = DiagnosticRequest(
            patient=CARDIAC_CASE,
            max_diagnoses=3,
        )

        response = await agent.analyze(request, use_cache=False)

        assert response.success is True

        # Disclaimer must always be present
        assert response.analysis.disclaimer
        assert "physician" in response.analysis.disclaimer.lower()
        assert "not replace" in response.analysis.disclaimer.lower()
        assert response.analysis.requires_physician_review is True

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self, agent):
        """Test that token usage is tracked."""
        request = DiagnosticRequest(
            patient=MIGRAINE_CASE,
            max_diagnoses=3,
        )

        response = await agent.analyze(request, use_cache=False)

        assert response.success is True

        # Token usage should be tracked
        if response.analysis.tokens_used:
            assert response.analysis.tokens_used > 0

        # Get usage summary
        usage = await agent.get_token_usage()
        assert usage["total_requests"] > 0


@pytest.mark.skipif(SKIP_INTEGRATION, reason=SKIP_REASON)
class TestDiagnosticAPIIntegration:
    """Integration tests for the API endpoints."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient

        from app.main import app

        return TestClient(app)

    def test_diagnose_endpoint(self, client):
        """Test main diagnose endpoint."""
        request_data = {
            "patient": {
                "age": 45,
                "gender": "male",
                "chief_complaint": "Chest pain",
                "symptoms": [{"name": "Chest pain", "severity": 8, "is_primary": True}],
            },
            "max_diagnoses": 3,
        }

        response = client.post(
            "/api/diagnose",
            json=request_data,
            headers={"Authorization": "Bearer test-token"},
        )

        # May fail due to auth, but should get appropriate response
        assert response.status_code in [200, 401, 403]

    def test_icd_validation_endpoint(self, client):
        """Test ICD-10 validation endpoint."""
        response = client.post(
            "/api/diagnose/validate-icd",
            json={"codes": ["I21.3", "G43.909", "INVALID"]},
            headers={"Authorization": "Bearer test-token"},
        )

        # May fail due to auth, but should get appropriate response
        assert response.status_code in [200, 401, 403]

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/api/diagnose/health")

        assert response.status_code == 200
        data = response.json()
        assert "api_key_configured" in data


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
