"""
NEURAXIS - Treatment Planning Agent
AI-powered treatment recommendations using Claude Sonnet 4
"""

import json
import logging
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.treatment_schemas import (
    ContraindicationWarning,
    CoverageStatus,
    DosageCalculation,
    DrugInteraction,
    FollowUpSchedule,
    LifestyleModification,
    MedicationCost,
    MedicationFrequency,
    MedicationRecommendation,
    MedicationRoute,
    PatientEducationPoint,
    ProcedureRecommendation,
    SafetyCheck,
    SpecialInstruction,
    TreatmentPlan,
    TreatmentPlanRequest,
    TreatmentPlanResponse,
    UrgencyLevel,
)
from app.core.config import settings
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
    get_dosage_calculator,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Treatment Planning Prompt
# =============================================================================

TREATMENT_PLANNING_PROMPT = """You are an expert clinical pharmacologist and treatment planning specialist. Your role is to generate comprehensive, evidence-based treatment recommendations for patients.

## PATIENT INFORMATION

**Diagnosis:** {diagnosis_name} (ICD-10: {icd10_code})
- Severity: {severity}
- Onset: {onset}

**Demographics:**
- Age: {age} years
- Gender: {gender}
- Weight: {weight} kg
- Height: {height} cm
- BMI: {bmi}
- BSA: {bsa} m²

**Allergies:**
{allergies}

**Current Medical Conditions:**
{conditions}

**Current Medications:**
{current_medications}

**Laboratory Results:**
{lab_results}

**Kidney Function:**
{renal_function}

**Liver Function:**
{hepatic_function}

**Insurance:**
{insurance}

**Research Findings:**
{research_findings}

## TASK

Generate a comprehensive treatment plan following these guidelines:

1. **First-Line Medications**: Recommend the most effective initial treatment
   - Include generic name, brand names, drug class
   - Calculate appropriate dosage (consider weight, age, organ function)
   - Specify frequency, route, duration
   - Provide special instructions (timing, food interactions)
   - Explain reasoning and evidence basis

2. **Alternative Treatments**: If first-line fails or is contraindicated
   - At least 2 alternatives per first-line medication
   - Explain when to switch

3. **Procedures/Interventions**: Any needed tests or procedures

4. **Lifestyle Modifications**: Diet, exercise, behavioral changes

5. **Follow-Up Schedule**: When to return, what to monitor

6. **Patient Education**: Key points patient should understand

7. **Safety Validation**:
   - CHECK ALL MEDICATIONS AGAINST PROVIDED ALLERGIES
   - Validate dosages are within safe ranges
   - Check for drug-drug interactions with current medications
   - Verify no contraindications with existing conditions

## IMPORTANT SAFETY RULES
- NEVER recommend a medication the patient is allergic to
- ALWAYS adjust doses for renal/hepatic impairment
- CHECK for drug-drug interactions
- Consider patient age for dosing
- Flag any high-risk recommendations

## RESPONSE FORMAT

Respond with valid JSON only, using this exact structure:

{{
    "treatment_goals": ["Goal 1", "Goal 2"],
    "urgency_level": "routine|urgent|emergent",
    "first_line_medications": [
        {{
            "generic_name": "medication name",
            "brand_names": ["Brand1", "Brand2"],
            "drug_class": "class name",
            "dose": "calculated dose",
            "frequency": "once daily|twice daily|etc",
            "route": "oral|IV|etc",
            "duration": "7 days|ongoing|etc",
            "special_instructions": [
                {{"instruction": "Take with food", "reason": "Reduces GI upset", "timing": "with meals"}}
            ],
            "indication": "why this drug",
            "mechanism_of_action": "how it works",
            "expected_benefit": "expected outcome",
            "time_to_effect": "when to expect results",
            "reasoning": "detailed clinical reasoning",
            "evidence_basis": "guideline or study reference",
            "is_first_line": true,
            "priority_order": 1
        }}
    ],
    "alternative_medications": [
        {{
            "generic_name": "alternative med",
            "brand_names": [],
            "drug_class": "class",
            "dose": "dose",
            "frequency": "frequency",
            "route": "route",
            "duration": "duration",
            "indication": "when to use instead",
            "reasoning": "why this is alternative",
            "is_first_line": false,
            "priority_order": 2
        }}
    ],
    "medications_to_discontinue": ["med1 - reason", "med2 - reason"],
    "procedures": [
        {{
            "procedure_name": "name",
            "urgency": "routine|urgent|emergent",
            "description": "what it involves",
            "indication": "why needed",
            "expected_outcome": "what to expect",
            "risks": ["risk1"],
            "pre_procedure_requirements": ["req1"]
        }}
    ],
    "lifestyle_modifications": [
        {{
            "category": "diet|exercise|smoking|alcohol|sleep|stress",
            "recommendation": "main recommendation",
            "specific_guidance": ["specific tip 1", "specific tip 2"],
            "expected_impact": "how it helps"
        }}
    ],
    "follow_up_schedule": [
        {{
            "timeframe": "2 weeks",
            "visit_type": "in-person|telehealth",
            "purpose": "why this visit",
            "monitoring_items": ["what to check"],
            "labs_to_order": ["lab tests"],
            "warning_signs": ["when to come back sooner"]
        }}
    ],
    "patient_education": [
        {{
            "topic": "topic name",
            "key_message": "main point",
            "details": ["detail 1", "detail 2"]
        }}
    ],
    "safety_concerns": [
        {{
            "concern": "description",
            "severity": "high|medium|low",
            "mitigation": "how to address"
        }}
    ],
    "overall_reasoning": "Summary of treatment approach and clinical rationale",
    "clinical_notes": "Additional notes for healthcare provider"
}}

Remember: Patient safety is paramount. When in doubt, recommend the safer option."""


# =============================================================================
# Treatment Agent
# =============================================================================


class TreatmentAgent:
    """
    AI-powered treatment planning agent using Claude Sonnet 4.

    Features:
    - Comprehensive treatment recommendations
    - Dosage calculations with adjustments
    - Safety validation (allergies, interactions, contraindications)
    - Cost estimation
    - Patient education content
    """

    MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 8000

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", None)
        self.model = model or self.MODEL

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Initialize helper services
        self.dosage_calculator = get_dosage_calculator()
        self.contraindication_checker = get_contraindication_checker()
        self.cost_service = get_cost_estimation_service()

        logger.info(f"TreatmentAgent initialized with model: {self.model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def _call_claude(self, prompt: str) -> dict:
        """
        Call Claude API with retry logic.

        Args:
            prompt: Formatted prompt

        Returns:
            Parsed JSON response
        """
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text

        # Parse JSON response
        try:
            # Find JSON in response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content

            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            logger.debug(f"Raw response: {content}")
            raise

    async def generate_plan(
        self,
        request: TreatmentPlanRequest,
    ) -> TreatmentPlanResponse:
        """
        Generate comprehensive treatment plan.

        Args:
            request: Treatment plan request with patient data

        Returns:
            TreatmentPlanResponse with plan or error
        """
        plan_id = str(uuid4())
        start_time = time.time()
        warnings: list[str] = []

        logger.info(f"Generating treatment plan - ID: {plan_id}")

        try:
            # Pre-flight safety checks
            pre_check_warnings = self._pre_flight_checks(request)
            warnings.extend(pre_check_warnings)

            # Format prompt
            prompt = self._format_prompt(request)

            # Call Claude
            response_data = await self._call_claude(prompt)

            # Parse medications
            first_line_meds = self._parse_medications(
                response_data.get("first_line_medications", []),
                request,
                is_first_line=True,
            )

            alternative_meds = self._parse_medications(
                response_data.get("alternative_medications", []),
                request,
                is_first_line=False,
            )

            # Run safety validation
            all_contraindications: list[ContraindicationWarning] = []
            all_interactions: list[DrugInteraction] = []
            safety_checks: list[SafetyCheck] = []

            for med in first_line_meds + alternative_meds:
                contraindications, interactions = self.contraindication_checker.check_all(
                    med.generic_name,
                    request.allergies,
                    request.conditions,
                    request.current_medications,
                )
                all_contraindications.extend(contraindications)
                all_interactions.extend(interactions)

            # Add safety checks
            safety_checks.extend(
                self._generate_safety_checks(
                    first_line_meds,
                    all_contraindications,
                    all_interactions,
                    request,
                )
            )

            # Flag blocked medications with warnings
            for ci in all_contraindications:
                if ci.severity == "absolute":
                    warnings.append(f"⚠️ {ci.medication} contraindicated: {ci.reason}")

            # Parse procedures
            procedures = [
                ProcedureRecommendation(
                    procedure_name=p.get("procedure_name", ""),
                    urgency=UrgencyLevel(p.get("urgency", "routine")),
                    description=p.get("description", ""),
                    indication=p.get("indication", ""),
                    expected_outcome=p.get("expected_outcome", ""),
                    risks=p.get("risks", []),
                    pre_procedure_requirements=p.get("pre_procedure_requirements", []),
                )
                for p in response_data.get("procedures", [])
            ]

            # Parse lifestyle modifications
            lifestyle = [
                LifestyleModification(
                    category=l.get("category", ""),
                    recommendation=l.get("recommendation", ""),
                    specific_guidance=l.get("specific_guidance", []),
                    expected_impact=l.get("expected_impact", ""),
                )
                for l in response_data.get("lifestyle_modifications", [])
            ]

            # Parse follow-up schedule
            follow_up = [
                FollowUpSchedule(
                    timeframe=f.get("timeframe", ""),
                    visit_type=f.get("visit_type", "in-person"),
                    purpose=f.get("purpose", ""),
                    monitoring_items=f.get("monitoring_items", []),
                    labs_to_order=f.get("labs_to_order", []),
                    warning_signs=f.get("warning_signs", []),
                )
                for f in response_data.get("follow_up_schedule", [])
            ]

            # Parse patient education
            education = [
                PatientEducationPoint(
                    topic=e.get("topic", ""),
                    key_message=e.get("key_message", ""),
                    details=e.get("details", []),
                )
                for e in response_data.get("patient_education", [])
            ]

            # Build treatment plan
            processing_time_ms = int((time.time() - start_time) * 1000)

            plan = TreatmentPlan(
                plan_id=plan_id,
                case_id=request.case_id,
                diagnosis_summary=f"{request.diagnosis.name} ({request.diagnosis.icd10_code})",
                treatment_goals=response_data.get("treatment_goals", []),
                first_line_medications=first_line_meds,
                alternative_medications=alternative_meds,
                medications_to_discontinue=response_data.get("medications_to_discontinue", []),
                procedures=procedures,
                lifestyle_modifications=lifestyle,
                follow_up_schedule=follow_up,
                patient_education=education,
                contraindications_checked=all_contraindications,
                drug_interactions=all_interactions,
                safety_checks=safety_checks,
                urgency_level=UrgencyLevel(response_data.get("urgency_level", "routine")),
                overall_reasoning=response_data.get("overall_reasoning", ""),
                clinical_notes=response_data.get("clinical_notes"),
                model_version=self.model,
                processing_time_ms=processing_time_ms,
            )

            logger.info(
                f"Treatment plan generated - ID: {plan_id}, "
                f"Meds: {len(first_line_meds)}, Time: {processing_time_ms}ms"
            )

            return TreatmentPlanResponse(
                success=True,
                plan=plan,
                warnings=warnings,
            )

        except Exception as e:
            logger.error(f"Treatment plan generation failed: {e}", exc_info=True)
            return TreatmentPlanResponse(
                success=False,
                error=str(e),
                warnings=warnings,
            )

    def _format_prompt(self, request: TreatmentPlanRequest) -> str:
        """Format the treatment planning prompt."""
        patient = request.patient

        # Format allergies
        if request.allergies:
            allergies = "\n".join(
                [
                    f"- {a.allergen} (Reaction: {a.reaction or 'unknown'}, Severity: {a.severity})"
                    for a in request.allergies
                ]
            )
        else:
            allergies = "No known allergies"

        # Format conditions
        if request.conditions:
            conditions = "\n".join(
                [
                    f"- {c.name} ({c.icd10_code or 'no code'}) - {c.status}"
                    for c in request.conditions
                ]
            )
        else:
            conditions = "No significant medical history"

        # Format current medications
        if request.current_medications:
            current_medications = "\n".join(
                [
                    f"- {m.name} {m.dose} {m.frequency} for {m.indication or 'unspecified'}"
                    for m in request.current_medications
                ]
            )
        else:
            current_medications = "No current medications"

        # Format lab results
        if request.lab_results:
            lab_results = "\n".join(
                [
                    f"- {l.test_name}: {l.value} {l.unit} ({l.status or 'pending'})"
                    for l in request.lab_results
                ]
            )
        else:
            lab_results = "No recent lab results"

        # Format renal function
        if request.renal_function:
            renal_function = (
                f"Creatinine: {request.renal_function.creatinine or 'N/A'} mg/dL, "
                f"eGFR: {request.renal_function.egfr or 'N/A'} mL/min, "
                f"CKD Stage: {request.renal_function.ckd_stage or 'N/A'}"
            )
        else:
            renal_function = "Not available"

        # Format hepatic function
        if request.hepatic_function:
            hepatic_function = (
                f"ALT: {request.hepatic_function.alt or 'N/A'} U/L, "
                f"AST: {request.hepatic_function.ast or 'N/A'} U/L, "
                f"Bilirubin: {request.hepatic_function.bilirubin or 'N/A'} mg/dL, "
                f"Child-Pugh: {request.hepatic_function.child_pugh_score or 'N/A'}"
            )
        else:
            hepatic_function = "Not available"

        # Format insurance
        if request.insurance:
            insurance = (
                f"Plan: {request.insurance.plan_type or 'Unknown'}, "
                f"Generic Copay: ${request.insurance.copay_generic or 'N/A'}, "
                f"Brand Copay: ${request.insurance.copay_brand or 'N/A'}"
            )
        else:
            insurance = "No insurance information"

        # Format research findings
        if request.research_findings:
            research_findings = "\n".join(
                [f"- [{r.evidence_grade}] {r.finding}" for r in request.research_findings]
            )
        else:
            research_findings = "No specific research findings provided"

        return TREATMENT_PLANNING_PROMPT.format(
            diagnosis_name=request.diagnosis.name,
            icd10_code=request.diagnosis.icd10_code,
            severity=request.diagnosis.severity or "unspecified",
            onset=request.diagnosis.onset or "unspecified",
            age=patient.age,
            gender=patient.gender,
            weight=patient.weight_kg or "unknown",
            height=patient.height_cm or "unknown",
            bmi=patient.bmi or "N/A",
            bsa=patient.bsa or "N/A",
            allergies=allergies,
            conditions=conditions,
            current_medications=current_medications,
            lab_results=lab_results,
            renal_function=renal_function,
            hepatic_function=hepatic_function,
            insurance=insurance,
            research_findings=research_findings,
        )

    def _parse_medications(
        self,
        meds_data: list[dict],
        request: TreatmentPlanRequest,
        is_first_line: bool,
    ) -> list[MedicationRecommendation]:
        """Parse medication recommendations and add dosage/cost info."""
        medications = []

        for i, med in enumerate(meds_data):
            generic_name = med.get("generic_name", "")

            # Calculate dosage
            dosage_calc = self.dosage_calculator.calculate_dose(
                medication_name=generic_name,
                patient=request.patient,
                renal_function=request.renal_function,
                hepatic_function=request.hepatic_function,
            )

            # Get cost info
            cost_info = self.cost_service.get_cost_info(
                generic_name,
                request.insurance,
            )

            # Parse special instructions
            special_instructions = [
                SpecialInstruction(
                    instruction=si.get("instruction", ""),
                    reason=si.get("reason"),
                    timing=si.get("timing"),
                )
                for si in med.get("special_instructions", [])
            ]

            # Parse frequency
            freq_str = med.get("frequency", "once daily").lower()
            frequency_map = {
                "once daily": MedicationFrequency.ONCE_DAILY,
                "twice daily": MedicationFrequency.TWICE_DAILY,
                "three times daily": MedicationFrequency.THREE_TIMES_DAILY,
                "four times daily": MedicationFrequency.FOUR_TIMES_DAILY,
                "every 4 hours": MedicationFrequency.EVERY_4_HOURS,
                "every 6 hours": MedicationFrequency.EVERY_6_HOURS,
                "every 8 hours": MedicationFrequency.EVERY_8_HOURS,
                "every 12 hours": MedicationFrequency.EVERY_12_HOURS,
                "as needed": MedicationFrequency.AS_NEEDED,
                "once weekly": MedicationFrequency.ONCE_WEEKLY,
            }
            frequency = frequency_map.get(freq_str, MedicationFrequency.ONCE_DAILY)

            # Parse route
            route_str = med.get("route", "oral").lower()
            route_map = {
                "oral": MedicationRoute.ORAL,
                "iv": MedicationRoute.IV,
                "intravenous": MedicationRoute.IV,
                "im": MedicationRoute.IM,
                "intramuscular": MedicationRoute.IM,
                "sc": MedicationRoute.SC,
                "subcutaneous": MedicationRoute.SC,
                "topical": MedicationRoute.TOPICAL,
                "inhaled": MedicationRoute.INHALED,
            }
            route = route_map.get(route_str, MedicationRoute.ORAL)

            medications.append(
                MedicationRecommendation(
                    medication_id=f"med_{uuid4().hex[:8]}",
                    generic_name=generic_name,
                    brand_names=med.get("brand_names", []),
                    drug_class=med.get("drug_class", ""),
                    dose=med.get("dose", dosage_calc.calculated_dose),
                    dosage_calculation=dosage_calc,
                    frequency=frequency,
                    route=route,
                    duration=med.get("duration"),
                    special_instructions=special_instructions,
                    cost_info=cost_info,
                    indication=med.get("indication", ""),
                    mechanism_of_action=med.get("mechanism_of_action"),
                    expected_benefit=med.get("expected_benefit", ""),
                    time_to_effect=med.get("time_to_effect"),
                    reasoning=med.get("reasoning", ""),
                    evidence_basis=med.get("evidence_basis"),
                    is_first_line=is_first_line,
                    priority_order=med.get("priority_order", i + 1),
                )
            )

        return medications

    def _pre_flight_checks(
        self,
        request: TreatmentPlanRequest,
    ) -> list[str]:
        """Perform pre-flight safety checks."""
        warnings = []

        # Check for critical allergies
        high_risk_allergens = ["penicillin", "sulfa", "aspirin", "nsaid"]
        for allergy in request.allergies:
            if allergy.allergen.lower() in high_risk_allergens:
                if allergy.severity == "severe":
                    warnings.append(f"⚠️ Severe {allergy.allergen} allergy documented")

        # Check renal function
        if request.renal_function and request.renal_function.egfr:
            if request.renal_function.egfr < 30:
                warnings.append(
                    f"⚠️ Severe renal impairment (eGFR {request.renal_function.egfr}) - "
                    "dose adjustments required"
                )

        # Check hepatic function
        if request.hepatic_function:
            cp = request.hepatic_function.child_pugh_score
            if cp in ["B", "C"]:
                warnings.append(
                    f"⚠️ Hepatic impairment (Child-Pugh {cp}) - dose adjustments required"
                )

        # Check for polypharmacy
        if len(request.current_medications) >= 10:
            warnings.append(
                f"⚠️ Polypharmacy risk: {len(request.current_medications)} current medications"
            )

        # Check age-related concerns
        if request.patient.age >= 65:
            warnings.append("ℹ️ Geriatric patient - consider age-appropriate dosing")
        elif request.patient.age < 18:
            warnings.append("ℹ️ Pediatric patient - weight-based dosing required")

        return warnings

    def _generate_safety_checks(
        self,
        medications: list[MedicationRecommendation],
        contraindications: list[ContraindicationWarning],
        interactions: list[DrugInteraction],
        request: TreatmentPlanRequest,
    ) -> list[SafetyCheck]:
        """Generate safety check results."""
        checks = []

        # Allergy check
        allergy_issues = [c for c in contraindications if "allergy" in c.reason.lower()]
        checks.append(
            SafetyCheck(
                check_type="Allergy Screening",
                passed=len(allergy_issues) == 0,
                details=f"Checked {len(medications)} medications against {len(request.allergies)} allergies",
                action_required=allergy_issues[0].reason if allergy_issues else None,
            )
        )

        # Drug interaction check
        severe_interactions = [
            i for i in interactions if i.severity.value in ["contraindicated", "severe"]
        ]
        checks.append(
            SafetyCheck(
                check_type="Drug Interaction Screening",
                passed=len(severe_interactions) == 0,
                details=f"Found {len(interactions)} interactions, {len(severe_interactions)} severe",
                action_required=severe_interactions[0].management if severe_interactions else None,
            )
        )

        # Renal dose adjustment
        if request.renal_function and request.renal_function.egfr:
            needs_adjustment = request.renal_function.egfr < 60
            checks.append(
                SafetyCheck(
                    check_type="Renal Dose Adjustment",
                    passed=True,
                    details=f"eGFR {request.renal_function.egfr} - {'adjustments applied' if needs_adjustment else 'no adjustment needed'}",
                )
            )

        # Hepatic dose adjustment
        if request.hepatic_function and request.hepatic_function.child_pugh_score:
            cp = request.hepatic_function.child_pugh_score
            needs_adjustment = cp in ["B", "C"]
            checks.append(
                SafetyCheck(
                    check_type="Hepatic Dose Adjustment",
                    passed=True,
                    details=f"Child-Pugh {cp} - {'adjustments applied' if needs_adjustment else 'no adjustment needed'}",
                )
            )

        # Condition contraindication check
        condition_issues = [
            c
            for c in contraindications
            if c.severity == "absolute" and "allergy" not in c.reason.lower()
        ]
        checks.append(
            SafetyCheck(
                check_type="Condition Contraindication Check",
                passed=len(condition_issues) == 0,
                details=f"Checked against {len(request.conditions)} conditions",
                action_required=condition_issues[0].reason if condition_issues else None,
            )
        )

        return checks


# =============================================================================
# Patient Education Generator
# =============================================================================


class PatientEducationGenerator:
    """Generate patient-friendly education content."""

    EDUCATION_TEMPLATES = {
        "medication_adherence": PatientEducationPoint(
            topic="Taking Your Medications",
            key_message="Taking medications exactly as prescribed is crucial for your treatment success.",
            details=[
                "Take medications at the same time each day",
                "Don't skip doses even if you feel better",
                "Use a pill organizer or phone reminder",
                "Keep a list of all your medications",
                "Don't stop medications without talking to your doctor",
            ],
        ),
        "side_effects": PatientEducationPoint(
            topic="Managing Side Effects",
            key_message="Some side effects are normal and may improve over time.",
            details=[
                "Report any unusual symptoms to your healthcare provider",
                "Don't stop medications without medical advice",
                "Some side effects resolve after first few weeks",
                "Keep track of when side effects occur",
            ],
        ),
        "follow_up": PatientEducationPoint(
            topic="Follow-Up Appointments",
            key_message="Regular follow-up helps ensure your treatment is working.",
            details=[
                "Keep all scheduled appointments",
                "Bring a list of questions to your visit",
                "Report how you've been feeling",
                "Bring your medication bottles",
            ],
        ),
        "lifestyle": PatientEducationPoint(
            topic="Lifestyle Changes",
            key_message="Lifestyle modifications can significantly improve your condition.",
            details=[
                "Follow dietary recommendations",
                "Stay physically active as recommended",
                "Get adequate sleep",
                "Manage stress effectively",
                "Avoid smoking and excessive alcohol",
            ],
        ),
        "warning_signs": PatientEducationPoint(
            topic="Warning Signs",
            key_message="Know when to seek immediate medical attention.",
            details=[
                "Call your doctor or go to ER for severe symptoms",
                "Don't ignore worsening symptoms",
                "Keep emergency contact numbers handy",
            ],
        ),
    }

    def get_education_for_diagnosis(
        self,
        diagnosis_category: str,
    ) -> list[PatientEducationPoint]:
        """Get relevant education points for diagnosis."""
        education = [
            self.EDUCATION_TEMPLATES["medication_adherence"],
            self.EDUCATION_TEMPLATES["side_effects"],
            self.EDUCATION_TEMPLATES["follow_up"],
        ]

        # Add condition-specific education
        if "diabetes" in diagnosis_category.lower():
            education.extend(
                [
                    PatientEducationPoint(
                        topic="Blood Sugar Monitoring",
                        key_message="Regular monitoring helps you and your doctor manage diabetes.",
                        details=[
                            "Check blood sugar as directed",
                            "Keep a log of your readings",
                            "Know your target blood sugar range",
                            "Watch for signs of low blood sugar",
                        ],
                    ),
                    PatientEducationPoint(
                        topic="Diabetes Diet",
                        key_message="What you eat directly affects your blood sugar.",
                        details=[
                            "Count carbohydrates",
                            "Choose whole grains over refined",
                            "Eat regular meals",
                            "Limit sugary drinks",
                        ],
                    ),
                ]
            )

        elif "hypertension" in diagnosis_category.lower():
            education.extend(
                [
                    PatientEducationPoint(
                        topic="Blood Pressure Monitoring",
                        key_message="Home monitoring helps track your progress.",
                        details=[
                            "Check blood pressure at the same time daily",
                            "Rest for 5 minutes before measuring",
                            "Keep a log to share with your doctor",
                            "Know your target blood pressure",
                        ],
                    ),
                    PatientEducationPoint(
                        topic="DASH Diet",
                        key_message="The DASH diet can lower blood pressure naturally.",
                        details=[
                            "Reduce sodium intake to less than 2300mg/day",
                            "Eat more fruits and vegetables",
                            "Choose low-fat dairy products",
                            "Limit saturated and total fat",
                        ],
                    ),
                ]
            )

        return education


# =============================================================================
# Factory
# =============================================================================


def create_treatment_agent(
    api_key: str | None = None,
    model: str | None = None,
) -> TreatmentAgent:
    """Create configured treatment agent."""
    return TreatmentAgent(api_key=api_key, model=model)
