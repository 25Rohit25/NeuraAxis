"""
NEURAXIS - Documentation Utilities
Helper services for documentation generation.
"""

import re
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from app.agents.documentation_schemas import DocumentationRequest, FHIRBundle, NoteType

# =============================================================================
# Macro Expander
# =============================================================================


class MacroExpander:
    """Handles text expansion logic."""

    DEFAULT_MACROS = {
        ".cc": "Chief Complaint",
        ".hpi": "History of Present Illness",
        ".ros": "Review of Systems",
        ".pe": "Physical Exam",
        ".pt": "Patient states",
        ".nka": "No known allergies",
        ".nkda": "No known drug allergies",
        ".wnl": "Within normal limits",
        ".sob": "Shortness of breath",
        ".cp": "Chest pain",
        ".dm": "Diabetes Mellitus",
        ".htn": "Hypertension",
    }

    def expand(self, text: str, user_macros: Dict[str, str] = None) -> str:
        if not text:
            return ""

        macros = self.DEFAULT_MACROS.copy()
        if user_macros:
            macros.update(user_macros)

        # Sort regex by length desc to handle overlapping prefixes
        sorted_keys = sorted(macros.keys(), key=len, reverse=True)
        pattern = re.compile("|".join(re.escape(k) for k in sorted_keys))

        return pattern.sub(lambda m: macros[m.group(0)], text)


# =============================================================================
# Compliance Validator
# =============================================================================


class ComplianceValidator:
    """Checks generated documentation for required elements."""

    REQUIRED_SECTIONS = {
        NoteType.SOAP: ["Subjective", "Objective", "Assessment", "Plan"],
        NoteType.H_AND_P: [
            "Chief Complaint",
            "History of Present Illness",
            "Review of Systems",
            "Physical Exam",
            "Assessment",
            "Plan",
        ],
        NoteType.DISCHARGE: [
            "Admission Date",
            "Discharge Date",
            "Discharge Diagnosis",
            "Course",
            "Instructions",
        ],
    }

    def validate(self, text: str, note_type: NoteType) -> List[str]:
        missing = []
        requirements = self.REQUIRED_SECTIONS.get(note_type, [])

        # Simple string check (case insensitive)
        text_lower = text.lower()

        for req in requirements:
            if req.lower() not in text_lower and f"{req.lower()}:" not in text_lower:
                missing.append(f"Missing required section: {req}")

        return missing


# =============================================================================
# FHIR Generator
# =============================================================================


class FHIRGenerator:
    """Generates basic FHIR Composition Resources."""

    def create_bundle(self, request: DocumentationRequest, content: str) -> FHIRBundle:
        now = datetime.now().isoformat()
        doc_id = str(uuid4())

        # 1. Composition Resource (The Document Header)
        composition = {
            "resourceType": "Composition",
            "id": doc_id,
            "status": "final",
            "type": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "11506-3",  # Progress note
                        "display": request.note_type.value,
                    }
                ]
            },
            "subject": {"reference": f"Patient/{request.patient_id}"},
            "date": now,
            "author": [{"display": "AI Assistant (Verified by Provider)"}],
            "title": f"{request.note_type.value} - {now[:10]}",
            "section": [
                {
                    "title": "Clinical Note",
                    "text": {
                        "status": "generated",
                        "div": f"<div xmlns='http://www.w3.org/1999/xhtml'>{content}</div>",
                    },
                }
            ],
        }

        entries = [{"resource": composition}]

        return FHIRBundle(entry=entries)


# =============================================================================
# Template Manager
# =============================================================================


class TemplateManager:
    TEMPLATES = {
        NoteType.SOAP: """
# SOAP NOTE
**Patient Name:** {patient_name}
**Date:** {date}

## SUBJECTIVE
**CC:** {chief_complaint}
**HPI:** {hpi}
**ROS:** {ros}

## OBJECTIVE
**Vitals:** {vitals}
**Physical Exam:** {physical_exam}
**Labs/Imaging:** {labs}

## ASSESSMENT
{diagnosis}

## PLAN
{treatment_plan}
        """,
        NoteType.H_AND_P: """
# HISTORY & PHYSICAL
**Patient Name:** {patient_name}
**Date:** {date}

## 1. CHIEF COMPLAINT
{chief_complaint}

## 2. HISTORY OF PRESENT ILLNESS
{hpi}

## 3. REVIEW OF SYSTEMS
{ros}

## 4. PHYSICAL EXAMINATION
{physical_exam}

## 5. DIAGNOSTIC DATA
{labs}

## 6. IMPRESSION/PLAN
{diagnosis}

{treatment_plan}
        """,
    }

    def get_template(self, note_type: NoteType) -> str:
        return self.TEMPLATES.get(note_type, self.TEMPLATES[NoteType.SOAP])
