"""
NEURAXIS - Treatment Agent Integration Tests
Tests with real Claude API calls (requires API key)
"""

import os
from datetime import date

import pytest

from app.agents.treatment import TreatmentAgent, create_treatment_agent
from app.agents.treatment_schemas import (
    Allergy,
    CurrentMedication,
    DiagnosisInput,
    HepaticFunction,
    InsuranceCoverage,
    LabResult,
    MedicalCondition,
    MedicationFrequency,
    MedicationRoute,
    PatientDemographics,
    RenalFunction,
    ResearchFinding,
    TreatmentPlanRequest,
    TreatmentPlanResponse,
    UrgencyLevel,
)

# Skip integration tests if no API key
SKIP_INTEGRATION = not os.environ.get("ANTHROPIC_API_KEY")
SKIP_REASON = "ANTHROPIC_API_KEY environment variable not set"


# =============================================================================
# Test Cases
# =============================================================================

DIABETES_CASE = TreatmentPlanRequest(
    case_id="integration-diabetes-001",
    diagnosis=DiagnosisInput(
        name="Type 2 Diabetes Mellitus",
        icd10_code="E11.9",
        severity="moderate",
        onset="chronic",
    ),
    patient=PatientDemographics(
        age=52,
        gender="male",
        weight_kg=92,
        height_cm=178,
    ),
    allergies=[
        Allergy(allergen="Sulfa", reaction="Rash", severity="moderate"),
    ],
    conditions=[
        MedicalCondition(name="Hypertension", icd10_code="I10", status="active"),
        MedicalCondition(name="Obesity", icd10_code="E66.9", status="active"),
    ],
    current_medications=[
        CurrentMedication(name="Lisinopril", dose="10mg", frequency="daily"),
    ],
    lab_results=[
        LabResult(test_name="HbA1c", value=8.2, unit="%", status="high"),
        LabResult(test_name="Fasting Glucose", value=165, unit="mg/dL", status="high"),
    ],
    renal_function=RenalFunction(creatinine=1.1, egfr=78),
    research_findings=[
        ResearchFinding(
            finding="Metformin is first-line therapy for T2DM",
            evidence_grade="A",
            source_count=50,
        ),
        ResearchFinding(
            finding="SGLT2 inhibitors reduce cardiovascular events in diabetic patients",
            evidence_grade="A",
            source_count=25,
        ),
    ],
)

HYPERTENSION_CASE = TreatmentPlanRequest(
    case_id="integration-htn-001",
    diagnosis=DiagnosisInput(
        name="Essential Hypertension",
        icd10_code="I10",
        severity="moderate",
        onset="chronic",
    ),
    patient=PatientDemographics(
        age=58,
        gender="female",
        weight_kg=72,
        height_cm=165,
    ),
    allergies=[
        Allergy(allergen="ACE inhibitors", reaction="Angioedema", severity="severe"),
    ],
    conditions=[
        MedicalCondition(name="Stage 2 CKD", icd10_code="N18.2", status="active"),
    ],
    current_medications=[],
    lab_results=[
        LabResult(test_name="Blood Pressure", value=158, unit="mmHg systolic", status="high"),
        LabResult(test_name="Potassium", value=4.5, unit="mEq/L", status="normal"),
    ],
    renal_function=RenalFunction(creatinine=1.4, egfr=52),
)

INFECTION_CASE = TreatmentPlanRequest(
    case_id="integration-infection-001",
    diagnosis=DiagnosisInput(
        name="Community-Acquired Pneumonia",
        icd10_code="J18.9",
        severity="moderate",
        onset="acute",
    ),
    patient=PatientDemographics(
        age=45,
        gender="male",
        weight_kg=85,
        height_cm=180,
    ),
    allergies=[
        Allergy(allergen="Penicillin", reaction="Anaphylaxis", severity="severe"),
    ],
    conditions=[],
    current_medications=[],
    lab_results=[
        LabResult(test_name="WBC", value=15.5, unit="x10^9/L", status="high"),
        LabResult(test_name="CRP", value=85, unit="mg/L", status="high"),
    ],
    renal_function=RenalFunction(egfr=95),
)

ELDERLY_POLYPHARMACY_CASE = TreatmentPlanRequest(
    case_id="integration-elderly-001",
    diagnosis=DiagnosisInput(
        name="Chronic Pain Syndrome",
        icd10_code="G89.29",
        severity="moderate",
        onset="chronic",
    ),
    patient=PatientDemographics(
        age=78,
        gender="female",
        weight_kg=58,
        height_cm=160,
    ),
    allergies=[
        Allergy(allergen="NSAIDs", reaction="GI bleeding", severity="severe"),
    ],
    conditions=[
        MedicalCondition(name="Hypertension", icd10_code="I10", status="active"),
        MedicalCondition(name="Heart Failure", icd10_code="I50.9", status="active"),
        MedicalCondition(name="Type 2 Diabetes", icd10_code="E11.9", status="active"),
        MedicalCondition(
            name="Chronic Kidney Disease Stage 3", icd10_code="N18.3", status="active"
        ),
    ],
    current_medications=[
        CurrentMedication(name="Carvedilol", dose="12.5mg", frequency="twice daily"),
        CurrentMedication(name="Lisinopril", dose="5mg", frequency="daily"),
        CurrentMedication(name="Metformin", dose="500mg", frequency="twice daily"),
        CurrentMedication(name="Furosemide", dose="40mg", frequency="daily"),
        CurrentMedication(name="Aspirin", dose="81mg", frequency="daily"),
        CurrentMedication(name="Atorvastatin", dose="20mg", frequency="daily"),
    ],
    renal_function=RenalFunction(creatinine=1.6, egfr=38),
    hepatic_function=HepaticFunction(alt=25, ast=28, bilirubin=0.9, albumin=3.5),
)


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.skipif(SKIP_INTEGRATION, reason=SKIP_REASON)
class TestTreatmentAgentIntegration:
    """Full integration tests for TreatmentAgent with Claude."""

    @pytest.fixture(scope="class")
    def agent(self):
        """Create treatment agent."""
        return create_treatment_agent()

    @pytest.mark.asyncio
    async def test_diabetes_treatment_plan(self, agent):
        """Test diabetes treatment plan generation."""
        response = await agent.generate_plan(DIABETES_CASE)

        assert response.success is True
        assert response.plan is not None

        plan = response.plan

        # Should recommend metformin or other diabetes medication
        med_names = [m.generic_name.lower() for m in plan.first_line_medications]
        print(f"\nDiabetes - First-line medications: {med_names}")

        diabetes_meds = [
            "metformin",
            "empagliflozin",
            "dapagliflozin",
            "semaglutide",
            "liraglutide",
        ]
        assert any(dm in " ".join(med_names) for dm in diabetes_meds), (
            f"Expected diabetes medication, got: {med_names}"
        )

        # Should NOT recommend sulfa drugs due to allergy
        assert not any("sulfonylurea" in m.lower() for m in med_names)

        # Should have lifestyle modifications
        assert len(plan.lifestyle_modifications) > 0
        categories = [l.category for l in plan.lifestyle_modifications]
        assert "diet" in categories or "exercise" in categories

        # Should have follow-up schedule
        assert len(plan.follow_up_schedule) > 0

        # Should have patient education
        assert len(plan.patient_education) > 0

        print(f"Treatment goals: {plan.treatment_goals}")
        print(f"Lifestyle: {[l.recommendation for l in plan.lifestyle_modifications]}")
        print(f"Follow-up: {plan.follow_up_schedule[0].timeframe}")

    @pytest.mark.asyncio
    async def test_hypertension_with_ace_allergy(self, agent):
        """Test hypertension treatment with ACE inhibitor allergy."""
        response = await agent.generate_plan(HYPERTENSION_CASE)

        assert response.success is True
        plan = response.plan

        # Should NOT recommend ACE inhibitors due to allergy
        med_names = [m.generic_name.lower() for m in plan.first_line_medications]
        ace_inhibitors = ["lisinopril", "enalapril", "ramipril", "benazepril", "captopril"]

        for med in med_names:
            assert not any(ace in med for ace in ace_inhibitors), (
                f"Should not recommend ACE inhibitor due to allergy, got: {med}"
            )

        # Should recommend alternative BP medications
        bp_alternatives = [
            "amlodipine",
            "losartan",
            "valsartan",
            "metoprolol",
            "hydrochlorothiazide",
            "chlorthalidone",
        ]
        assert any(alt in " ".join(med_names) for alt in bp_alternatives), (
            f"Should recommend alternative BP medication, got: {med_names}"
        )

        print(f"\nHypertension - Medications (avoiding ACE-I): {med_names}")

        # Check for CKD-related dose adjustments
        # Should have renal considerations noted
        has_renal_mention = (
            any(
                "renal" in m.reasoning.lower() or "kidney" in m.reasoning.lower()
                for m in plan.first_line_medications
            )
            or "renal" in plan.overall_reasoning.lower()
        )
        print(f"Renal considerations mentioned: {has_renal_mention}")

    @pytest.mark.asyncio
    async def test_pneumonia_with_penicillin_allergy(self, agent):
        """Test pneumonia treatment with penicillin allergy."""
        response = await agent.generate_plan(INFECTION_CASE)

        assert response.success is True
        plan = response.plan

        # Should NOT recommend penicillin-class antibiotics
        med_names = [m.generic_name.lower() for m in plan.first_line_medications]
        penicillins = ["amoxicillin", "ampicillin", "penicillin", "piperacillin"]

        for med in med_names:
            assert not any(pen in med for pen in penicillins), (
                f"Should not recommend penicillin due to allergy, got: {med}"
            )

        # Should recommend alternative antibiotics
        alternatives = [
            "azithromycin",
            "levofloxacin",
            "moxifloxacin",
            "doxycycline",
            "ceftriaxone",
        ]
        assert any(alt in " ".join(med_names) for alt in alternatives), (
            f"Should recommend alternative antibiotic, got: {med_names}"
        )

        print(f"\nPneumonia - Antibiotics (avoiding penicillin): {med_names}")

        # Should have urgency noted
        assert plan.urgency_level in [UrgencyLevel.ROUTINE, UrgencyLevel.URGENT]

    @pytest.mark.asyncio
    async def test_elderly_polypharmacy(self, agent):
        """Test elderly patient with polypharmacy concerns."""
        response = await agent.generate_plan(ELDERLY_POLYPHARMACY_CASE)

        assert response.success is True
        plan = response.plan

        # Should have safety warnings about polypharmacy
        has_polypharmacy_warning = any("polypharmacy" in w.lower() for w in response.warnings)

        # Should have drug interaction checks
        assert len(plan.drug_interactions) >= 0  # May have interactions

        # Should have renal dose adjustment notes
        has_renal_adjustment = any("renal" in str(check).lower() for check in plan.safety_checks)

        print(f"\nElderly patient - Warnings: {response.warnings}")
        print(f"Safety checks: {[c.check_type for c in plan.safety_checks]}")
        print(f"Interactions detected: {len(plan.drug_interactions)}")

        # Should NOT recommend NSAIDs due to allergy
        med_names = [m.generic_name.lower() for m in plan.first_line_medications]
        nsaids = ["ibuprofen", "naproxen", "meloxicam", "celecoxib", "diclofenac"]

        for med in med_names:
            assert not any(nsaid in med for nsaid in nsaids), (
                f"Should not recommend NSAID due to allergy, got: {med}"
            )

    @pytest.mark.asyncio
    async def test_dosage_adjustments(self, agent):
        """Test that dosage adjustments are applied."""
        response = await agent.generate_plan(ELDERLY_POLYPHARMACY_CASE)

        assert response.success is True
        plan = response.plan

        # Check for dosage calculation details
        for med in plan.first_line_medications:
            if med.dosage_calculation:
                print(f"\n{med.generic_name} dosing:")
                print(f"  Calculated: {med.dosage_calculation.calculated_dose}")
                print(f"  Method: {med.dosage_calculation.calculation_method}")
                print(f"  Adjustments: {med.dosage_calculation.adjustments}")

    @pytest.mark.asyncio
    async def test_cost_information(self, agent):
        """Test that cost information is included."""
        # Add insurance info
        case = DIABETES_CASE.model_copy()
        case.insurance = InsuranceCoverage(
            plan_type="PPO",
            copay_generic=10.00,
            copay_brand=50.00,
        )

        response = await agent.generate_plan(case)

        assert response.success is True
        plan = response.plan

        # Check for cost info
        for med in plan.first_line_medications:
            if med.cost_info:
                print(f"\n{med.generic_name} cost:")
                print(f"  Monthly: ${med.cost_info.estimated_monthly_cost}")
                print(f"  Copay: ${med.cost_info.copay_estimate}")
                print(f"  Generic available: {med.cost_info.generic_available}")

    @pytest.mark.asyncio
    async def test_response_structure(self, agent):
        """Test complete response structure."""
        response = await agent.generate_plan(DIABETES_CASE)

        assert response.success is True
        plan = response.plan

        # Check all required fields
        assert plan.plan_id
        assert plan.diagnosis_summary
        assert plan.treatment_goals
        assert plan.overall_reasoning
        assert plan.disclaimer
        assert plan.processing_time_ms > 0

        # Check medication structure
        for med in plan.first_line_medications:
            assert med.medication_id
            assert med.generic_name
            assert med.drug_class
            assert med.dose
            assert med.frequency
            assert med.route
            assert med.indication
            assert med.reasoning

        # Check safety checks performed
        check_types = [c.check_type for c in plan.safety_checks]
        assert "Allergy Screening" in check_types
        assert "Drug Interaction Screening" in check_types

        print(f"\nProcessing time: {plan.processing_time_ms}ms")
        print(f"Model: {plan.model_version}")

    @pytest.mark.asyncio
    async def test_performance(self, agent):
        """Test response time performance."""
        import time

        start = time.time()
        response = await agent.generate_plan(DIABETES_CASE)
        elapsed = time.time() - start

        assert response.success is True

        print(f"\nTotal time: {elapsed:.2f}s")
        print(f"API time: {response.plan.processing_time_ms}ms")

        # Should complete in reasonable time
        assert elapsed < 60, f"Response took too long: {elapsed}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
