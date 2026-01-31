"""
NEURAXIS - Diagnostic Agent Prompt Templates
Medical reasoning prompts for GPT-4o diagnostic analysis
"""

from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

# =============================================================================
# System Prompt
# =============================================================================

DIAGNOSTIC_SYSTEM_PROMPT = """You are a highly skilled medical diagnostic AI assistant working alongside physicians. Your role is to analyze patient information and provide differential diagnoses using evidence-based medical reasoning.

## Your Capabilities
- Analyze symptoms, vital signs, lab results, and medical history
- Generate ranked differential diagnoses with probability estimates
- Provide detailed chain-of-thought reasoning
- Assign calibrated confidence scores
- Suggest appropriate diagnostic tests
- Assess clinical urgency

## Medical Reasoning Framework
You MUST follow this systematic approach:

1. **Chief Complaint Analysis**: Identify the primary concern and its characteristics (onset, location, duration, character, aggravating/alleviating factors, radiation, severity - OLDCARTS)

2. **Vital Sign Interpretation**: Assess for abnormalities and their clinical significance

3. **Symptom Pattern Recognition**: Identify symptom clusters and their pathophysiological significance

4. **Risk Factor Assessment**: Consider patient demographics, history, and risk factors

5. **Hypothesis Generation**: Generate initial differential diagnoses based on presentation

6. **Hypothesis Testing**: Evaluate each hypothesis against available evidence

7. **Probability Assignment**: Estimate likelihood based on:
   - Base rates (epidemiological probability)
   - Positive predictive value of findings
   - Negative predictive value of absent findings

8. **Urgency Determination**: Assess time-sensitivity based on potential for deterioration

## Confidence Score Guidelines
- 0.0-0.2: Very uncertain, many alternatives equally likely
- 0.2-0.4: Low confidence, significant uncertainty remains
- 0.4-0.6: Moderate confidence, diagnosis is plausible
- 0.6-0.8: High confidence, strong evidence supports diagnosis
- 0.8-1.0: Very high confidence, classical presentation

## Critical Safety Rules
1. ALWAYS recommend physician review - your analysis is decision support only
2. NEVER recommend specific medications or dosages
3. ALWAYS flag critical/emergent conditions prominently
4. When uncertain, express uncertainty clearly
5. Consider life-threatening conditions first (rule out the worst)
6. Flag any red flag symptoms immediately

## ICD-10 Code Requirements
- Provide accurate ICD-10-CM codes
- Use the most specific code applicable
- Include the official code description

## Output Format
You MUST respond with valid JSON matching the specified schema. Do not include any text outside the JSON object."""


# =============================================================================
# Few-Shot Examples
# =============================================================================

FEW_SHOT_EXAMPLES = [
    {
        "input": """
Patient: 45-year-old male
Chief Complaint: Chest pain for 2 hours
Symptoms:
- Crushing chest pain, severity 8/10, radiating to left arm
- Diaphoresis
- Nausea
- Shortness of breath
Vital Signs:
- BP: 160/95 mmHg
- HR: 98 bpm
- SpO2: 96%
Medical History:
- Hypertension
- Diabetes Type 2
- Family history of MI (father at 52)
""",
        "output": """{
  "patient_summary": "45-year-old male with cardiovascular risk factors presenting with acute onset crushing chest pain radiating to left arm, associated with diaphoresis, nausea, and dyspnea. Classic presentation concerning for acute coronary syndrome.",
  
  "reasoning_chain": [
    {
      "step_number": 1,
      "observation": "Crushing chest pain with left arm radiation, severity 8/10, sudden onset 2 hours ago",
      "inference": "Pattern strongly suggests cardiac origin. Radiation pattern follows dermatomes supplied by same spinal segments as heart (T1-T4).",
      "hypothesis_impact": "Strongly increases probability of acute coronary syndrome (ACS)",
      "confidence_delta": 0.4
    },
    {
      "step_number": 2,
      "observation": "Associated diaphoresis and nausea",
      "inference": "Autonomic symptoms indicate significant physiological stress. Vagal activation common in inferior MI.",
      "hypothesis_impact": "Further supports ACS, may suggest inferior wall involvement",
      "confidence_delta": 0.15
    },
    {
      "step_number": 3,
      "observation": "Multiple cardiac risk factors: HTN, DM2, male, age 45, positive family history",
      "inference": "Framingham risk factors significantly increase pre-test probability of coronary artery disease",
      "hypothesis_impact": "Markedly increases likelihood of ACS as etiology",
      "confidence_delta": 0.2
    },
    {
      "step_number": 4,
      "observation": "Elevated BP 160/95, HR 98, SpO2 96%",
      "inference": "Hypertensive response may indicate catecholamine surge from pain/stress. Mild tachycardia consistent with sympathetic activation. O2 sat slightly low.",
      "hypothesis_impact": "Supports acute stress state consistent with ACS",
      "confidence_delta": 0.05
    }
  ],
  
  "differential_diagnosis": [
    {
      "name": "Acute ST-Elevation Myocardial Infarction (STEMI)",
      "icd10_code": "I21.3",
      "icd10_description": "ST elevation (STEMI) myocardial infarction of unspecified site",
      "probability": 0.55,
      "confidence_score": 0.75,
      "confidence_category": "high",
      "clinical_reasoning": "Classic presentation with crushing chest pain radiating to left arm, diaphoresis, nausea, and dyspnea in a patient with multiple cardiovascular risk factors. This constellation of findings has high positive predictive value for acute MI. The symptom duration of 2 hours is within the typical window for STEMI presentation.",
      "supporting_evidence": [
        {"type": "symptom", "finding": "Crushing chest pain with left arm radiation", "significance": "Highly characteristic of myocardial ischemia", "weight": 0.9},
        {"type": "symptom", "finding": "Diaphoresis", "significance": "Autonomic response to cardiac ischemia", "weight": 0.7},
        {"type": "symptom", "finding": "Nausea", "significance": "Vagal response, common in MI", "weight": 0.5},
        {"type": "history", "finding": "HTN, DM2, family history of premature CAD", "significance": "Major risk factors for ACS", "weight": 0.8}
      ],
      "contradicting_evidence": [],
      "suggested_tests": [
        {"test_name": "12-lead ECG", "test_type": "diagnostic", "rationale": "Immediate assessment for ST elevation or depression", "priority": "urgent", "expected_findings": "ST elevation in contiguous leads would confirm STEMI", "cpt_code": "93000"},
        {"test_name": "Troponin I/T", "test_type": "lab", "rationale": "Cardiac biomarker for myocardial necrosis", "priority": "urgent", "expected_findings": "Elevated levels confirm myocardial injury", "cpt_code": "84484"},
        {"test_name": "CK-MB", "test_type": "lab", "rationale": "Additional cardiac biomarker", "priority": "urgent", "expected_findings": "Elevated with MI", "cpt_code": "82553"}
      ],
      "is_primary": true,
      "category": "cardiovascular"
    },
    {
      "name": "Non-ST-Elevation Myocardial Infarction (NSTEMI)",
      "icd10_code": "I21.4",
      "icd10_description": "Non-ST elevation (NSTEMI) myocardial infarction",
      "probability": 0.25,
      "confidence_score": 0.7,
      "confidence_category": "high",
      "clinical_reasoning": "Same clinical presentation as STEMI but would show ST depression or T-wave inversions rather than ST elevation. Cannot differentiate from STEMI without ECG, but presentation is classic for ACS spectrum.",
      "supporting_evidence": [
        {"type": "symptom", "finding": "Typical anginal symptoms", "significance": "Classic ACS presentation", "weight": 0.85}
      ],
      "contradicting_evidence": [],
      "suggested_tests": [],
      "is_primary": false,
      "category": "cardiovascular"
    },
    {
      "name": "Unstable Angina",
      "icd10_code": "I20.0",
      "icd10_description": "Unstable angina",
      "probability": 0.12,
      "confidence_score": 0.65,
      "confidence_category": "moderate",
      "clinical_reasoning": "Similar presentation to MI but without biomarker elevation. The severity of symptoms makes this less likely than frank infarction.",
      "supporting_evidence": [
        {"type": "symptom", "finding": "Chest pain at rest", "significance": "Characteristic of unstable angina", "weight": 0.7}
      ],
      "contradicting_evidence": [
        {"type": "symptom", "finding": "Severe symptoms with diaphoresis", "significance": "Suggests more than unstable angina", "weight": 0.3}
      ],
      "suggested_tests": [],
      "is_primary": false,
      "category": "cardiovascular"
    }
  ],
  
  "urgency_assessment": {
    "level": "critical",
    "score": 0.95,
    "reasoning": "Presentation consistent with acute coronary syndrome requiring immediate intervention. Time is myocardium - every minute of delay increases infarct size and mortality risk.",
    "red_flags": [
      {"finding": "Crushing chest pain with radiation", "severity": "critical", "recommended_action": "Activate cardiac catheterization lab", "time_sensitivity": "immediate"},
      {"finding": "Diaphoresis with chest pain", "severity": "high", "recommended_action": "IV access, continuous monitoring", "time_sensitivity": "immediate"}
    ],
    "recommended_timeframe": "Immediate intervention required - minutes matter",
    "recommended_setting": "Emergency Department with PCI capability"
  },
  
  "immediate_actions": [
    "Activate STEMI/ACS protocol",
    "Obtain STAT 12-lead ECG",
    "Establish IV access",
    "Administer aspirin 324mg if not contraindicated",
    "Continuous cardiac monitoring",
    "Prepare for possible emergent cardiac catheterization"
  ],
  
  "overall_confidence": 0.85,
  "data_quality_score": 0.9,
  
  "disclaimer": "This AI-generated analysis is for clinical decision support only. It does not replace professional medical judgment. All findings must be reviewed and validated by a qualified physician. Given the critical nature of this presentation, immediate physician evaluation is essential."
}""",
    },
    {
        "input": """
Patient: 28-year-old female
Chief Complaint: Headache for 3 days
Symptoms:
- Throbbing headache, one-sided (right), severity 7/10
- Sensitivity to light
- Nausea without vomiting
- Preceded by visual disturbance (zig-zag lines) for 20 minutes
Vital Signs:
- BP: 118/76 mmHg
- HR: 72 bpm
- Temp: 98.6°F
Medical History:
- Similar headaches in past, usually with menses
- Mother has migraines
""",
        "output": """{
  "patient_summary": "28-year-old female with recurrent unilateral throbbing headaches associated with photophobia, nausea, and visual aura. History of similar episodes, often menstrual-related, with positive family history. Classic presentation for migraine with aura.",
  
  "reasoning_chain": [
    {
      "step_number": 1,
      "observation": "Unilateral throbbing headache, severity 7/10",
      "inference": "Throbbing/pulsatile quality suggests vascular component. Unilateral location is characteristic of migraine.",
      "hypothesis_impact": "Strongly supports migraine diagnosis",
      "confidence_delta": 0.35
    },
    {
      "step_number": 2,
      "observation": "Visual aura (zig-zag lines) preceding headache by 20 minutes",
      "inference": "Classic visual aura of migraine - fortification spectra caused by cortical spreading depression. Duration consistent with typical aura.",
      "hypothesis_impact": "Virtually diagnostic of migraine with aura",
      "confidence_delta": 0.35
    },
    {
      "step_number": 3,
      "observation": "Photophobia and nausea",
      "inference": "Associated features that fulfill migraine diagnostic criteria",
      "hypothesis_impact": "Further supports migraine",
      "confidence_delta": 0.1
    },
    {
      "step_number": 4,
      "observation": "Recurrent similar episodes, menstrual association, maternal history of migraines",
      "inference": "Pattern of recurrence, hormonal trigger, and genetic predisposition all classic for migraine",
      "hypothesis_impact": "Confirms chronic migraine pattern",
      "confidence_delta": 0.1
    }
  ],
  
  "differential_diagnosis": [
    {
      "name": "Migraine with Aura",
      "icd10_code": "G43.109",
      "icd10_description": "Migraine with aura, not intractable, without status migrainosus",
      "probability": 0.88,
      "confidence_score": 0.9,
      "confidence_category": "very_high",
      "clinical_reasoning": "Patient meets ICHD-3 criteria for migraine with aura: unilateral, pulsating, moderate-severe intensity, aggravation by activity, and associated with nausea and photophobia. Visual aura preceding headache by appropriate duration. Recurrent episodes with hormonal association and positive family history strongly support diagnosis.",
      "supporting_evidence": [
        {"type": "symptom", "finding": "Unilateral throbbing headache", "significance": "Cardinal feature of migraine", "weight": 0.8},
        {"type": "symptom", "finding": "Visual aura (fortification spectra)", "significance": "Pathognomonic for migraine with aura", "weight": 0.95},
        {"type": "symptom", "finding": "Photophobia and nausea", "significance": "Associated features fulfilling criteria", "weight": 0.7},
        {"type": "history", "finding": "Recurrent episodes, menstrual association", "significance": "Classic pattern for migraine", "weight": 0.8},
        {"type": "family_history", "finding": "Mother with migraines", "significance": "Strong genetic component", "weight": 0.6}
      ],
      "contradicting_evidence": [],
      "suggested_tests": [
        {"test_name": "Neurological examination", "test_type": "physical_exam", "rationale": "Confirm normal neurological status", "priority": "routine", "expected_findings": "Normal examination between attacks", "cpt_code": null}
      ],
      "is_primary": true,
      "category": "neurological"
    },
    {
      "name": "Tension-type Headache",
      "icd10_code": "G44.209",
      "icd10_description": "Tension-type headache, unspecified, not intractable",
      "probability": 0.05,
      "confidence_score": 0.75,
      "confidence_category": "high",
      "clinical_reasoning": "Much less likely given unilateral throbbing nature, presence of aura, photophobia, and nausea - features not typical of tension headache which is usually bilateral, pressing/tightening, and without prominent associated features.",
      "supporting_evidence": [],
      "contradicting_evidence": [
        {"type": "symptom", "finding": "Unilateral throbbing quality", "significance": "Not typical of tension headache", "weight": 0.8},
        {"type": "symptom", "finding": "Visual aura", "significance": "Not seen in tension headache", "weight": 0.9}
      ],
      "suggested_tests": [],
      "is_primary": false,
      "category": "neurological"
    }
  ],
  
  "urgency_assessment": {
    "level": "low",
    "score": 0.15,
    "reasoning": "Classic migraine with aura in a young woman with prior similar episodes and normal vital signs. No red flags for secondary headache. Recurrent pattern suggests primary headache disorder.",
    "red_flags": [],
    "recommended_timeframe": "Outpatient evaluation within days to weeks",
    "recommended_setting": "Primary care or neurology outpatient"
  },
  
  "immediate_actions": [
    "Consider acute migraine treatment if not already administered",
    "Ensure patient has quiet, dark environment",
    "Counsel on warning signs requiring emergent evaluation"
  ],
  
  "additional_history_needed": [
    "Frequency of headaches per month",
    "Current preventive and abortive treatments tried",
    "Response to prior treatments",
    "Impact on daily functioning",
    "Complete menstrual headache pattern"
  ],
  
  "overall_confidence": 0.9,
  "data_quality_score": 0.85,
  
  "disclaimer": "This AI-generated analysis is for clinical decision support only. It does not replace professional medical judgment. All findings must be reviewed and validated by a qualified physician."
}""",
    },
]


# =============================================================================
# Main Prompt Templates
# =============================================================================


def get_diagnostic_prompt_template() -> ChatPromptTemplate:
    """Get the main diagnostic prompt template."""

    # Create few-shot example template
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{output}"),
        ]
    )

    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=FEW_SHOT_EXAMPLES,
    )

    # Main template
    return ChatPromptTemplate.from_messages(
        [
            ("system", DIAGNOSTIC_SYSTEM_PROMPT),
            few_shot_prompt,
            (
                "human",
                """Analyze the following patient case and provide a comprehensive diagnostic assessment.

## Patient Information
**Age**: {age} years old
**Gender**: {gender}
**Chief Complaint**: {chief_complaint}

## Presenting Symptoms
{symptoms}

## Vital Signs
{vital_signs}

## Laboratory Results
{lab_results}

## Medical History
{medical_history}

## Current Medications
{current_medications}

## Onset and Course
{onset_description}

## Additional Notes
{additional_notes}

---

Provide your diagnostic analysis in the following JSON format:
{{
  "patient_summary": "Brief clinical summary",
  "reasoning_chain": [
    {{
      "step_number": 1,
      "observation": "Clinical finding",
      "inference": "Medical inference",
      "hypothesis_impact": "Effect on differential",
      "confidence_delta": 0.0
    }}
  ],
  "differential_diagnosis": [
    {{
      "name": "Diagnosis name",
      "icd10_code": "Code",
      "icd10_description": "Description",
      "probability": 0.0,
      "confidence_score": 0.0,
      "confidence_category": "moderate",
      "clinical_reasoning": "Detailed reasoning",
      "supporting_evidence": [],
      "contradicting_evidence": [],
      "suggested_tests": [],
      "is_primary": false,
      "category": "Category"
    }}
  ],
  "urgency_assessment": {{
    "level": "low|medium|high|critical",
    "score": 0.0,
    "reasoning": "Explanation",
    "red_flags": [],
    "recommended_timeframe": "Timeframe",
    "recommended_setting": "Setting"
  }},
  "immediate_actions": [],
  "additional_history_needed": [],
  "overall_confidence": 0.0,
  "data_quality_score": 0.0,
  "disclaimer": "Standard disclaimer"
}}

Respond ONLY with the JSON object. Ensure all probability and confidence scores are between 0 and 1.""",
            ),
        ]
    )


# =============================================================================
# Formatting Helpers
# =============================================================================


def format_symptoms(symptoms: list) -> str:
    """Format symptoms list for prompt."""
    if not symptoms:
        return "No symptoms reported"

    lines = []
    for i, symptom in enumerate(symptoms, 1):
        line = f"{i}. {symptom.name}"
        if hasattr(symptom, "severity"):
            line += f" (Severity: {symptom.severity}/10)"
        if hasattr(symptom, "duration") and symptom.duration:
            line += f" - Duration: {symptom.duration} {symptom.duration_unit or ''}"
        if hasattr(symptom, "location") and symptom.location:
            line += f" - Location: {symptom.location}"
        if hasattr(symptom, "is_primary") and symptom.is_primary:
            line += " [PRIMARY]"
        lines.append(line)

    return "\n".join(lines)


def format_vitals(vitals) -> str:
    """Format vital signs for prompt."""
    if not vitals:
        return "No vital signs recorded"

    parts = []
    if vitals.blood_pressure_systolic and vitals.blood_pressure_diastolic:
        parts.append(f"BP: {vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic} mmHg")
    if vitals.heart_rate:
        parts.append(f"HR: {vitals.heart_rate} bpm")
    if vitals.respiratory_rate:
        parts.append(f"RR: {vitals.respiratory_rate}/min")
    if vitals.temperature:
        parts.append(f"Temp: {vitals.temperature}°{vitals.temperature_unit}")
    if vitals.oxygen_saturation:
        parts.append(f"SpO2: {vitals.oxygen_saturation}%")

    return " | ".join(parts) if parts else "No vital signs recorded"


def format_labs(labs: list) -> str:
    """Format lab results for prompt."""
    if not labs:
        return "No laboratory results available"

    lines = []
    for lab in labs:
        line = f"- {lab.test_name}: {lab.value} {lab.unit}"
        if lab.normal_min is not None and lab.normal_max is not None:
            line += f" (Normal: {lab.normal_min}-{lab.normal_max})"
        if lab.status:
            line += f" [{lab.status.upper()}]"
        lines.append(line)

    return "\n".join(lines)


def format_history(history) -> str:
    """Format medical history for prompt."""
    if not history:
        return "No medical history available"

    parts = []

    if history.conditions:
        parts.append(f"**Conditions**: {', '.join(history.conditions)}")
    if history.allergies:
        parts.append(f"**Allergies**: {', '.join(history.allergies)}")
    if history.medications:
        parts.append(f"**Medications**: {', '.join(history.medications)}")
    if history.surgeries:
        parts.append(f"**Surgeries**: {', '.join(history.surgeries)}")
    if history.family_history:
        parts.append(f"**Family History**: {', '.join(history.family_history)}")

    return "\n".join(parts) if parts else "No significant medical history"


def format_medications(medications: list) -> str:
    """Format current medications for prompt."""
    if not medications:
        return "No current medications"
    return ", ".join(medications)
