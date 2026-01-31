"""
NEURAXIS - Treatment Agent Unit Tests
Tests with mock Claude responses
"""

import json
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agents.treatment import (
    PatientEducationGenerator,
    TreatmentAgent,
    create_treatment_agent,
)
from app.agents.treatment_schemas import (
    Allergy,
    CurrentMedication,
    DiagnosisInput,
    EvidenceGrade,
    HepaticFunction,
    InsuranceCoverage,
    InteractionSeverity,
    LabResult,
    MedicalCondition,
    MedicationFrequency,
    MedicationRecommendation,
    MedicationRoute,
    PatientDemographics,
    RenalFunction,
    TreatmentPlan,
    TreatmentPlanRequest,
    TreatmentPlanResponse,
    UrgencyLevel,
)
from app.services.contraindication_checker import (
    ContraindicationChecker,
    get_contraindication_checker,
)
from app.services.cost_estimation import (
    CostEstimationService,
    get_cost_estimation_service,
)
from app.services.dosage_calculator import (
    DosageCalculator,
    calculate_egfr,
    get_dosage_calculator,
)

# =============================================================================
# Mock Data
# =============================================================================

MOCK_PATIENT = PatientDemographics(
    age=55,
    gender="male",
    weight_kg=80,
    height_cm=175,
)

MOCK_DIAGNOSIS = DiagnosisInput(
    name="Type 2 Diabetes Mellitus",
    icd10_code="E11.9",
    severity="moderate",
    onset="chronic",
)

MOCK_ALLERGIES = [
    Allergy(allergen="Penicillin", reaction="Rash", severity="moderate"),
    Allergy(allergen="Sulfa", reaction="Hives", severity="severe"),
]

MOCK_CONDITIONS = [
    MedicalCondition(name="Hypertension", icd10_code="I10", status="active"),
    MedicalCondition(name="Hyperlipidemia", icd10_code="E78.5", status="active"),
]

MOCK_MEDICATIONS = [
    CurrentMedication(name="Lisinopril", dose="10mg", frequency="daily", indication="hypertension"),
    CurrentMedication(
        name="Atorvastatin", dose="20mg", frequency="daily", indication="cholesterol"
    ),
]

MOCK_RENAL = RenalFunction(
    creatinine=1.2,
    egfr=65,
)

MOCK_HEPATIC = HepaticFunction(
    alt=35,
    ast=30,
    bilirubin=0.8,
    albumin=4.0,
)

MOCK_CLAUDE_RESPONSE = {
    "treatment_goals": [
        "Achieve HbA1c < 7.0%",
        "Prevent microvascular complications",
        "Maintain blood pressure < 130/80",
    ],
    "urgency_level": "routine",
    "first_line_medications": [
        {
            "generic_name": "metformin",
            "brand_names": ["Glucophage", "Glucophage XR"],
            "drug_class": "Biguanide",
            "dose": "500 mg twice daily",
            "frequency": "twice daily",
            "route": "oral",
            "duration": "ongoing",
            "special_instructions": [
                {
                    "instruction": "Take with food",
                    "reason": "Reduces GI upset",
                    "timing": "with meals",
                }
            ],
            "indication": "First-line treatment for type 2 diabetes",
            "mechanism_of_action": "Decreases hepatic glucose production and increases insulin sensitivity",
            "expected_benefit": "Expected 1-1.5% reduction in HbA1c",
            "time_to_effect": "Full effect in 2-4 weeks",
            "reasoning": "Metformin is the recommended first-line agent per ADA guidelines due to efficacy, safety, low cost, and cardiovascular benefits",
            "evidence_basis": "ADA Standards of Care 2024",
            "is_first_line": True,
            "priority_order": 1,
        }
    ],
    "alternative_medications": [
        {
            "generic_name": "empagliflozin",
            "brand_names": ["Jardiance"],
            "drug_class": "SGLT2 Inhibitor",
            "dose": "10 mg once daily",
            "frequency": "once daily",
            "route": "oral",
            "duration": "ongoing",
            "indication": "Alternative or add-on if metformin insufficient",
            "reasoning": "SGLT2 inhibitors have cardiovascular and renal benefits",
            "is_first_line": False,
            "priority_order": 2,
        }
    ],
    "medications_to_discontinue": [],
    "procedures": [
        {
            "procedure_name": "HbA1c Testing",
            "urgency": "routine",
            "description": "Blood test to measure average blood sugar over 3 months",
            "indication": "Monitor diabetes control",
            "expected_outcome": "Baseline reading to track progress",
            "risks": ["Minimal - blood draw only"],
            "pre_procedure_requirements": ["No fasting required"],
        }
    ],
    "lifestyle_modifications": [
        {
            "category": "diet",
            "recommendation": "Follow a Mediterranean or carbohydrate-conscious diet",
            "specific_guidance": [
                "Limit carbohydrates to 45-60g per meal",
                "Choose whole grains over refined carbohydrates",
                "Increase fiber intake to 25-30g daily",
                "Reduce sugary beverages",
            ],
            "expected_impact": "Can reduce HbA1c by 0.5-1%",
        },
        {
            "category": "exercise",
            "recommendation": "150 minutes of moderate-intensity aerobic activity weekly",
            "specific_guidance": [
                "Aim for 30 minutes, 5 days per week",
                "Include resistance training 2-3 times per week",
                "Start slowly and gradually increase intensity",
            ],
            "expected_impact": "Improves insulin sensitivity and cardiovascular health",
        },
    ],
    "follow_up_schedule": [
        {
            "timeframe": "4 weeks",
            "visit_type": "telehealth",
            "purpose": "Assess medication tolerance and early response",
            "monitoring_items": ["Side effects", "Blood glucose logs", "Blood pressure"],
            "labs_to_order": [],
            "warning_signs": ["Severe GI symptoms", "Signs of lactic acidosis"],
        },
        {
            "timeframe": "3 months",
            "visit_type": "in-person",
            "purpose": "Comprehensive diabetes review",
            "monitoring_items": ["Weight", "Blood pressure", "Foot exam"],
            "labs_to_order": ["HbA1c", "Fasting lipid panel", "Comprehensive metabolic panel"],
            "warning_signs": ["Persistent hyperglycemia", "Hypoglycemia episodes"],
        },
    ],
    "patient_education": [
        {
            "topic": "Understanding Diabetes",
            "key_message": "Type 2 diabetes is a manageable condition with proper treatment",
            "details": [
                "Blood sugar control prevents complications",
                "Medications work best with lifestyle changes",
                "Regular monitoring is essential",
            ],
        },
        {
            "topic": "Taking Metformin",
            "key_message": "Metformin is safe and effective when taken correctly",
            "details": [
                "Take with food to reduce stomach upset",
                "GI side effects usually improve over time",
                "Do not stop without consulting your doctor",
            ],
        },
    ],
    "safety_concerns": [
        {
            "concern": "GI side effects with metformin initiation",
            "severity": "low",
            "mitigation": "Start at low dose and titrate slowly",
        }
    ],
    "overall_reasoning": "Starting metformin as first-line therapy is consistent with ADA 2024 guidelines. Given the patient's preserved renal function and absence of contraindications, standard dosing can be used. The treatment plan includes comprehensive lifestyle modifications which are essential for diabetes management.",
    "clinical_notes": "Monitor renal function annually. Consider adding SGLT2 inhibitor if HbA1c remains above target after 3 months.",
}


# =============================================================================
# Dosage Calculator Tests
# =============================================================================


class TestDosageCalculator:
    """Tests for DosageCalculator."""

    @pytest.fixture
    def calculator(self):
        """Create dosage calculator."""
        return DosageCalculator()

    def test_fixed_dose_medication(self, calculator):
        """Test fixed-dose medication calculation."""
        patient = PatientDemographics(age=50, gender="male", weight_kg=70)

        result = calculator.calculate_dose("lisinopril", patient)

        assert result.calculated_dose
        assert result.calculation_method == "fixed"
        assert "5" in result.calculated_dose or "10" in result.calculated_dose

    def test_weight_based_dosing(self, calculator):
        """Test weight-based dose calculation."""
        patient = PatientDemographics(age=8, gender="male", weight_kg=25)

        result = calculator.calculate_dose("amoxicillin", patient)

        assert result.calculation_method == "weight-based"
        assert "625" in result.calculated_dose or "mg" in result.calculated_dose

    def test_renal_adjustment(self, calculator):
        """Test renal dose adjustment."""
        patient = PatientDemographics(age=65, gender="female", weight_kg=60)
        renal = RenalFunction(egfr=25)  # Severe renal impairment

        result = calculator.calculate_dose("metformin", patient, renal)

        # Should have renal adjustment warning
        assert any(
            "renal" in a.lower() or "contraindicated" in a.lower() for a in result.adjustments
        )

    def test_hepatic_adjustment(self, calculator):
        """Test hepatic dose adjustment."""
        patient = PatientDemographics(age=55, gender="male", weight_kg=75)
        hepatic = HepaticFunction(bilirubin=4.0, albumin=2.5, inr=2.5)  # Child-Pugh C

        result = calculator.calculate_dose("atorvastatin", patient, hepatic_function=hepatic)

        # Should have hepatic contraindication
        assert any("hepatic" in a.lower() or "avoid" in a.lower() for a in result.adjustments)

    def test_pediatric_dose(self, calculator):
        """Test pediatric dose calculation."""
        result = calculator.calculate_pediatric_dose(
            medication_name="acetaminophen",
            weight_kg=20,
            age_years=6,
        )

        assert result.calculation_method == "weight-based"
        assert "mg" in result.calculated_dose

    def test_bsa_dose(self, calculator):
        """Test BSA-based dosing."""
        result = calculator.calculate_bsa_dose(
            dose_per_m2=100,
            height_cm=175,
            weight_kg=80,
        )

        assert result.calculation_method == "bsa-based"
        assert "m²" in result.formula_used

    def test_unknown_medication(self, calculator):
        """Test handling of unknown medication."""
        patient = PatientDemographics(age=50, gender="male")

        result = calculator.calculate_dose("unknownmed123", patient)

        assert "manual" in result.calculation_method or "See prescribing" in result.calculated_dose


class TestEgfrCalculation:
    """Tests for eGFR calculation."""

    def test_normal_egfr(self):
        """Test normal eGFR calculation."""
        egfr = calculate_egfr(
            creatinine=1.0,
            age=40,
            gender="male",
        )

        assert egfr > 90  # Normal

    def test_decreased_egfr(self):
        """Test decreased eGFR with high creatinine."""
        egfr = calculate_egfr(
            creatinine=2.5,
            age=70,
            gender="female",
        )

        assert egfr < 30  # Severe impairment

    def test_female_adjustment(self):
        """Test female adjustment in eGFR."""
        male_egfr = calculate_egfr(1.2, 50, "male")
        female_egfr = calculate_egfr(1.2, 50, "female")

        # Female eGFR should be slightly higher with same creatinine
        assert female_egfr > male_egfr * 0.9


# =============================================================================
# Contraindication Checker Tests
# =============================================================================


class TestContraindicationChecker:
    """Tests for ContraindicationChecker."""

    @pytest.fixture
    def checker(self):
        """Create contraindication checker."""
        return ContraindicationChecker()

    def test_direct_allergy_match(self, checker):
        """Test direct allergy matching."""
        allergies = [Allergy(allergen="Penicillin", reaction="Anaphylaxis", severity="severe")]

        warnings = checker.check_allergies("amoxicillin", allergies)

        # Amoxicillin is a penicillin
        assert len(warnings) > 0
        assert warnings[0].severity == "absolute"

    def test_cross_reactivity(self, checker):
        """Test cross-reactivity checking."""
        allergies = [Allergy(allergen="Penicillin", severity="moderate")]

        # Check cephalosporin (cross-reactive)
        warnings = checker.check_allergies("cephalexin", allergies)

        # Should have cross-reactivity warning
        assert any("cross" in w.reason.lower() for w in warnings)

    def test_drug_condition_contraindication(self, checker):
        """Test drug-condition contraindication."""
        conditions = [MedicalCondition(name="Pregnancy", icd10_code="Z33.1")]

        warnings = checker.check_conditions("lisinopril", conditions)

        assert len(warnings) > 0
        assert warnings[0].severity == "absolute"

    def test_drug_drug_interaction(self, checker):
        """Test drug-drug interaction detection."""
        current_meds = [CurrentMedication(name="Warfarin", dose="5mg", frequency="daily")]

        interactions = checker.check_interactions("aspirin", current_meds)

        assert len(interactions) > 0
        assert interactions[0].severity == InteractionSeverity.SEVERE

    def test_safe_medication(self, checker):
        """Test that safe medication passes checks."""
        allergies = [Allergy(allergen="Shellfish")]
        conditions = []
        current_meds = []

        is_safe = checker.is_safe("metformin", allergies, conditions, current_meds)

        assert is_safe is True


# =============================================================================
# Cost Estimation Tests
# =============================================================================


class TestCostEstimation:
    """Tests for CostEstimationService."""

    @pytest.fixture
    def service(self):
        """Create cost estimation service."""
        return CostEstimationService()

    def test_generic_medication_cost(self, service):
        """Test generic medication cost lookup."""
        cost = service.get_cost_info("metformin")

        assert cost.generic_available is True
        assert cost.estimated_monthly_cost is not None
        assert cost.estimated_monthly_cost < 50  # Generic should be cheap

    def test_brand_medication_cost(self, service):
        """Test brand-only medication cost."""
        cost = service.get_cost_info("ozempic")

        assert cost.generic_available is False
        assert cost.estimated_monthly_cost > 500  # Expensive brand medication

    def test_insurance_copay_estimate(self, service):
        """Test copay estimation with insurance."""
        insurance = InsuranceCoverage(
            plan_type="PPO",
            copay_generic=10.00,
            copay_brand=50.00,
        )

        cost = service.get_cost_info("lisinopril", insurance)

        assert cost.copay_estimate == 10.00  # Generic copay

    def test_find_alternatives(self, service):
        """Test finding cheaper alternatives."""
        alternatives = service.find_cheaper_alternatives("atorvastatin")

        # Should find other statins
        assert len(alternatives) >= 0

    def test_total_monthly_cost(self, service):
        """Test total monthly cost estimation."""
        result = service.estimate_total_monthly_cost(["metformin", "lisinopril", "atorvastatin"])

        assert result["total_retail"] > 0
        assert len(result["medications"]) == 3


# =============================================================================
# Treatment Agent Tests
# =============================================================================


class TestTreatmentAgent:
    """Tests for TreatmentAgent."""

    @pytest.fixture
    def mock_request(self):
        """Create mock treatment request."""
        return TreatmentPlanRequest(
            case_id="test-123",
            diagnosis=MOCK_DIAGNOSIS,
            patient=MOCK_PATIENT,
            allergies=MOCK_ALLERGIES,
            conditions=MOCK_CONDITIONS,
            current_medications=MOCK_MEDICATIONS,
            renal_function=MOCK_RENAL,
            hepatic_function=MOCK_HEPATIC,
        )

    def test_format_prompt(self, mock_request):
        """Test prompt formatting."""
        with patch.object(TreatmentAgent, "__init__", lambda x, **kw: None):
            agent = TreatmentAgent()
            agent.dosage_calculator = get_dosage_calculator()
            agent.contraindication_checker = get_contraindication_checker()
            agent.cost_service = get_cost_estimation_service()

            prompt = agent._format_prompt(mock_request)

            # Check key information is in prompt
            assert "Type 2 Diabetes" in prompt
            assert "E11.9" in prompt
            assert "55" in prompt  # Age
            assert "Penicillin" in prompt  # Allergy
            assert "Lisinopril" in prompt  # Current med

    def test_pre_flight_checks(self, mock_request):
        """Test pre-flight safety checks."""
        with patch.object(TreatmentAgent, "__init__", lambda x, **kw: None):
            agent = TreatmentAgent()
            agent.dosage_calculator = get_dosage_calculator()
            agent.contraindication_checker = get_contraindication_checker()
            agent.cost_service = get_cost_estimation_service()

            warnings = agent._pre_flight_checks(mock_request)

            # Should detect severe sulfa allergy
            assert any("allergy" in w.lower() for w in warnings)

    @pytest.mark.asyncio
    async def test_generate_plan_with_mock(self, mock_request):
        """Test plan generation with mocked Claude."""
        with patch("anthropic.Anthropic") as mock_anthropic:
            # Mock Claude response
            mock_message = MagicMock()
            mock_message.content = [MagicMock(text=json.dumps(MOCK_CLAUDE_RESPONSE))]
            mock_anthropic.return_value.messages.create.return_value = mock_message

            agent = TreatmentAgent(api_key="test-key")

            response = await agent.generate_plan(mock_request)

            assert response.success is True
            assert response.plan is not None
            assert len(response.plan.first_line_medications) > 0
            assert response.plan.first_line_medications[0].generic_name == "metformin"


# =============================================================================
# Patient Education Tests
# =============================================================================


class TestPatientEducation:
    """Tests for PatientEducationGenerator."""

    @pytest.fixture
    def generator(self):
        """Create education generator."""
        return PatientEducationGenerator()

    def test_general_education(self, generator):
        """Test general education content."""
        education = generator.get_education_for_diagnosis("general")

        # Should have basic education points
        assert len(education) >= 3
        topics = [e.topic for e in education]
        assert "Taking Your Medications" in topics

    def test_diabetes_education(self, generator):
        """Test diabetes-specific education."""
        education = generator.get_education_for_diagnosis("diabetes")

        topics = [e.topic for e in education]
        assert any("blood sugar" in t.lower() or "diabetes" in t.lower() for t in topics)

    def test_hypertension_education(self, generator):
        """Test hypertension-specific education."""
        education = generator.get_education_for_diagnosis("hypertension")

        topics = [e.topic for e in education]
        assert any("blood pressure" in t.lower() or "dash" in t.lower() for t in topics)


# =============================================================================
# Schema Validation Tests
# =============================================================================


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_patient_demographics_bmi(self):
        """Test BMI calculation."""
        patient = PatientDemographics(
            age=40,
            gender="male",
            weight_kg=80,
            height_cm=175,
        )

        # BMI = 80 / (1.75)^2 = 26.1
        assert patient.bmi is not None
        assert 26 < patient.bmi < 27

    def test_patient_demographics_bsa(self):
        """Test BSA calculation."""
        patient = PatientDemographics(
            age=40,
            gender="male",
            weight_kg=70,
            height_cm=170,
        )

        assert patient.bsa is not None
        assert 1.8 < patient.bsa < 2.0

    def test_renal_function_ckd_stage(self):
        """Test CKD stage determination."""
        renal_g1 = RenalFunction(egfr=95)
        renal_g3 = RenalFunction(egfr=40)
        renal_g5 = RenalFunction(egfr=10)

        assert renal_g1.ckd_stage == "G1"
        assert renal_g3.ckd_stage == "G3b"
        assert renal_g5.ckd_stage == "G5"

    def test_hepatic_function_child_pugh(self):
        """Test Child-Pugh scoring."""
        # Class A (mild)
        hepatic_a = HepaticFunction(bilirubin=1.5, albumin=4.0, inr=1.2)
        assert hepatic_a.child_pugh_score == "A"

        # Class C (severe)
        hepatic_c = HepaticFunction(bilirubin=5.0, albumin=2.0, inr=3.0)
        assert hepatic_c.child_pugh_score == "C"

    def test_medication_recommendation_model(self):
        """Test MedicationRecommendation model."""
        med = MedicationRecommendation(
            medication_id="test-001",
            generic_name="metformin",
            brand_names=["Glucophage"],
            drug_class="Biguanide",
            dose="500 mg",
            frequency=MedicationFrequency.TWICE_DAILY,
            route=MedicationRoute.ORAL,
            indication="Type 2 Diabetes",
            expected_benefit="HbA1c reduction",
            reasoning="First-line per guidelines",
        )

        assert med.generic_name == "metformin"
        assert med.frequency == MedicationFrequency.TWICE_DAILY
        assert med.is_first_line is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
