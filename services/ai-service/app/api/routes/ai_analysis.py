"""
NEURAXIS - AI Symptom Analysis API
AI-powered symptom analysis and differential diagnosis
"""

import os
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ai", tags=["ai-analysis"])

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


# =============================================================================
# Pydantic Schemas
# =============================================================================


class SymptomInput(BaseModel):
    name: str
    severity: int = Field(ge=1, le=10)
    duration: Optional[str] = None


class ChiefComplaintInput(BaseModel):
    complaint: str
    duration: str
    onset: str
    severity: int
    location: Optional[str] = None
    character: Optional[str] = None
    aggravating_factors: Optional[List[str]] = None
    relieving_factors: Optional[List[str]] = None


class VitalsInput(BaseModel):
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    heart_rate: int
    temperature: float
    temperature_unit: str
    oxygen_saturation: int
    respiratory_rate: int
    pain_level: Optional[int] = None


class MedicalHistoryInput(BaseModel):
    conditions: Optional[List[Dict[str, Any]]] = None
    allergies: Optional[List[Dict[str, Any]]] = None
    surgeries: Optional[List[Dict[str, Any]]] = None


class AnalyzeCaseInput(BaseModel):
    chief_complaint: ChiefComplaintInput
    symptoms: List[SymptomInput]
    vitals: Optional[VitalsInput] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    medical_history: Optional[MedicalHistoryInput] = None


class RelatedSymptomsInput(BaseModel):
    chief_complaint: ChiefComplaintInput
    current_symptoms: List[str]
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None


class DifferentialDiagnosis(BaseModel):
    diagnosis: str
    probability: float
    supporting_symptoms: List[str]
    suggested_tests: List[str]


class UrgencyAssessment(BaseModel):
    level: str  # low, moderate, high, critical
    reasoning: str
    red_flags: List[str]


class RelatedSymptom(BaseModel):
    symptom: str
    relevance: float
    reason: str


class AnalysisResponse(BaseModel):
    differential_diagnosis: List[DifferentialDiagnosis]
    urgency_assessment: UrgencyAssessment
    related_symptoms: List[RelatedSymptom]
    suggested_questions: List[str]
    confidence: float


# =============================================================================
# AI Analysis Functions
# =============================================================================


async def call_openai(messages: List[Dict[str, str]], temperature: float = 0.3) -> str:
    """Call OpenAI API with messages."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": OPENAI_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 2000,
            },
            timeout=60.0,
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {response.text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]


def build_case_context(input_data: AnalyzeCaseInput) -> str:
    """Build clinical context from input data."""
    context_parts = []

    # Patient demographics
    if input_data.patient_age or input_data.patient_gender:
        demo = []
        if input_data.patient_age:
            demo.append(f"{input_data.patient_age} years old")
        if input_data.patient_gender:
            demo.append(input_data.patient_gender)
        context_parts.append(f"Patient: {', '.join(demo)}")

    # Chief complaint
    cc = input_data.chief_complaint
    complaint_text = f"Chief Complaint: {cc.complaint}"
    complaint_text += f" (Duration: {cc.duration}, Onset: {cc.onset}, Severity: {cc.severity}/10)"
    if cc.location:
        complaint_text += f", Location: {cc.location}"
    if cc.character:
        complaint_text += f", Character: {cc.character}"
    if cc.aggravating_factors:
        complaint_text += f", Aggravating: {', '.join(cc.aggravating_factors)}"
    if cc.relieving_factors:
        complaint_text += f", Relieving: {', '.join(cc.relieving_factors)}"
    context_parts.append(complaint_text)

    # Symptoms
    if input_data.symptoms:
        symptom_list = [
            f"{s.name} (severity: {s.severity}/10"
            + (f", duration: {s.duration}" if s.duration else "")
            + ")"
            for s in input_data.symptoms
        ]
        context_parts.append(f"Symptoms: {', '.join(symptom_list)}")

    # Vitals
    if input_data.vitals:
        v = input_data.vitals
        vitals_text = f"Vitals: BP {v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg, "
        vitals_text += f"HR {v.heart_rate} bpm, Temp {v.temperature}°{v.temperature_unit}, "
        vitals_text += f"SpO2 {v.oxygen_saturation}%, RR {v.respiratory_rate}/min"
        if v.pain_level:
            vitals_text += f", Pain {v.pain_level}/10"
        context_parts.append(vitals_text)

    # Medical history
    if input_data.medical_history:
        mh = input_data.medical_history
        if mh.conditions:
            conditions = [c.get("condition", c.get("name", "Unknown")) for c in mh.conditions]
            context_parts.append(f"Past Medical History: {', '.join(conditions)}")
        if mh.allergies:
            allergies = [a.get("allergen", "Unknown") for a in mh.allergies]
            context_parts.append(f"Allergies: {', '.join(allergies)}")

    return "\n".join(context_parts)


async def analyze_case_with_ai(input_data: AnalyzeCaseInput) -> AnalysisResponse:
    """Perform AI analysis on case data."""

    context = build_case_context(input_data)

    system_prompt = """You are an expert medical AI assistant helping physicians with clinical decision support.
Analyze the patient presentation and provide:
1. Differential diagnosis with probability estimates (most likely diagnoses)
2. Urgency assessment (low/moderate/high/critical) with reasoning
3. Red flags that require immediate attention
4. Related symptoms to inquire about
5. Suggested diagnostic tests

Be thorough but concise. Focus on clinically relevant information.
Always consider patient safety first. Flag any concerning presentations.

IMPORTANT: This is a decision support tool. All diagnoses require physician verification.
Never provide definitive diagnoses - always frame as differential possibilities.
"""

    user_prompt = f"""Analyze this patient presentation:

{context}

Provide your analysis in the following JSON format:
{{
    "differential_diagnosis": [
        {{
            "diagnosis": "Diagnosis name",
            "probability": 0.0-1.0,
            "supporting_symptoms": ["symptom1", "symptom2"],
            "suggested_tests": ["test1", "test2"]
        }}
    ],
    "urgency_assessment": {{
        "level": "low|moderate|high|critical",
        "reasoning": "Brief explanation",
        "red_flags": ["red flag 1", "red flag 2"]
    }},
    "related_symptoms": [
        {{
            "symptom": "Symptom to ask about",
            "relevance": 0.0-1.0,
            "reason": "Why this symptom is relevant"
        }}
    ],
    "suggested_questions": ["Question 1", "Question 2"],
    "confidence": 0.0-1.0
}}

Provide only valid JSON in your response."""

    try:
        response_text = await call_openai(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        # Parse JSON response
        import json

        # Clean response (remove markdown code blocks if present)
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())

        return AnalysisResponse(
            differential_diagnosis=[
                DifferentialDiagnosis(**d) for d in data.get("differential_diagnosis", [])
            ],
            urgency_assessment=UrgencyAssessment(
                **data.get(
                    "urgency_assessment",
                    {
                        "level": "moderate",
                        "reasoning": "Unable to determine urgency",
                        "red_flags": [],
                    },
                )
            ),
            related_symptoms=[RelatedSymptom(**s) for s in data.get("related_symptoms", [])],
            suggested_questions=data.get("suggested_questions", []),
            confidence=data.get("confidence", 0.7),
        )

    except json.JSONDecodeError as e:
        # Return fallback response on parse error
        return AnalysisResponse(
            differential_diagnosis=[],
            urgency_assessment=UrgencyAssessment(
                level="moderate",
                reasoning="AI analysis encountered an error. Manual review required.",
                red_flags=[],
            ),
            related_symptoms=[],
            suggested_questions=[],
            confidence=0.0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis error: {str(e)}")


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/analyze-case", response_model=AnalysisResponse)
async def analyze_case(input_data: AnalyzeCaseInput):
    """
    Analyze a medical case using AI.
    Returns differential diagnosis, urgency assessment, and recommendations.
    """
    return await analyze_case_with_ai(input_data)


@router.post("/related-symptoms")
async def get_related_symptoms(input_data: RelatedSymptomsInput):
    """
    Get AI-suggested related symptoms based on current presentation.
    """

    context_parts = [
        f"Chief Complaint: {input_data.chief_complaint.complaint}",
        f"Duration: {input_data.chief_complaint.duration}, Onset: {input_data.chief_complaint.onset}",
    ]

    if input_data.current_symptoms:
        context_parts.append(f"Current symptoms: {', '.join(input_data.current_symptoms)}")

    if input_data.patient_age:
        context_parts.append(f"Patient age: {input_data.patient_age}")

    if input_data.patient_gender:
        context_parts.append(f"Patient gender: {input_data.patient_gender}")

    context = "\n".join(context_parts)

    system_prompt = """You are a medical AI assistant. Given a patient's chief complaint and current symptoms,
suggest related symptoms that would be clinically relevant to inquire about.
Focus on symptoms that help differentiate between possible diagnoses.
"""

    user_prompt = f"""Based on this presentation, suggest 5-8 related symptoms to ask about:

{context}

Provide response as JSON:
{{
    "suggestions": [
        {{
            "symptom": "Symptom name",
            "relevance": 0.0-1.0,
            "reason": "Brief clinical reason"
        }}
    ]
}}

Only suggest symptoms NOT already in the current symptoms list.
Provide only valid JSON."""

    try:
        response_text = await call_openai(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        import json

        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        data = json.loads(cleaned.strip())

        return {"suggestions": data.get("suggestions", [])}

    except Exception as e:
        return {"suggestions": []}


@router.post("/urgency-check")
async def quick_urgency_check(
    chief_complaint: str,
    symptoms: List[str],
    patient_age: Optional[int] = None,
):
    """
    Quick urgency level check for triage purposes.
    """

    context = f"Chief complaint: {chief_complaint}\nSymptoms: {', '.join(symptoms)}"
    if patient_age:
        context += f"\nAge: {patient_age}"

    system_prompt = """You are a triage AI. Quickly assess urgency level based on symptoms.
Focus on identifying critical presentations that need immediate attention.
"""

    user_prompt = f"""Assess urgency for:

{context}

Respond with JSON:
{{
    "urgency": "low|moderate|high|critical",
    "reasoning": "Brief explanation",
    "immediate_action_needed": true|false,
    "red_flags": ["any immediate concerns"]
}}

Be conservative - when in doubt, suggest higher urgency.
Provide only valid JSON."""

    try:
        response_text = await call_openai(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )  # Lower temperature for safety-critical

        import json

        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]

        return json.loads(cleaned.strip())

    except Exception:
        # Default to high urgency on error for safety
        return {
            "urgency": "high",
            "reasoning": "Unable to analyze - manual triage required",
            "immediate_action_needed": False,
            "red_flags": ["AI analysis failed - requires manual review"],
        }
