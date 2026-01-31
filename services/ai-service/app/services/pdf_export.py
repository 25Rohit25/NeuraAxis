"""
NEURAXIS - PDF Export Service
Generate PDF exports for medical cases
"""

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.case import MedicalCase

# =============================================================================
# Styles
# =============================================================================


def get_styles():
    """Get customized styles for PDF generation."""
    styles = getSampleStyleSheet()

    # Add custom styles
    styles.add(
        ParagraphStyle(
            "CaseTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=20,
            textColor=colors.HexColor("#1e40af"),
        )
    )

    styles.add(
        ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading2"],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#374151"),
            borderWidth=0,
            borderPadding=4,
            borderColor=colors.HexColor("#e5e7eb"),
        )
    )

    styles.add(
        ParagraphStyle(
            "SubSection",
            parent=styles["Heading3"],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=6,
            textColor=colors.HexColor("#4b5563"),
        )
    )

    styles.add(
        ParagraphStyle(
            "Label",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#6b7280"),
        )
    )

    styles.add(
        ParagraphStyle(
            "Value",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#111827"),
        )
    )

    styles.add(
        ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#9ca3af"),
            spaceBefore=20,
        )
    )

    styles.add(
        ParagraphStyle(
            "Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#9ca3af"),
            alignment=TA_CENTER,
        )
    )

    return styles


# =============================================================================
# PDF Generator
# =============================================================================


async def generate_case_pdf(case: MedicalCase, options: dict) -> bytes:
    """Generate a PDF export of the medical case."""

    buffer = io.BytesIO()

    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter if options.get("is_print_optimized") else A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = get_styles()
    story = []

    # Header
    story.append(build_header(case, styles))
    story.append(Spacer(1, 20))

    # Patient information
    story.append(build_patient_section(case, styles))
    story.append(Spacer(1, 15))

    # Chief complaint
    if hasattr(case, "chief_complaint") and case.chief_complaint:
        story.append(build_chief_complaint_section(case, styles))
        story.append(Spacer(1, 15))

    # Vital signs
    if hasattr(case, "vitals") and case.vitals:
        story.append(build_vitals_section(case, styles))
        story.append(Spacer(1, 15))

    # Symptoms
    if hasattr(case, "symptoms") and case.symptoms:
        story.append(build_symptoms_section(case, styles))
        story.append(Spacer(1, 15))

    # Medical history
    if hasattr(case, "medical_history") and case.medical_history:
        story.append(build_history_section(case, styles))
        story.append(Spacer(1, 15))

    # AI Analysis (optional)
    if options.get("include_ai_analysis") and hasattr(case, "ai_analysis"):
        story.append(PageBreak())
        story.append(build_ai_analysis_section(case, styles))

    # Treatment plan
    if hasattr(case, "treatment_plan") and case.treatment_plan:
        story.append(PageBreak())
        story.append(build_treatment_section(case, styles))

    # Clinical notes
    if hasattr(case, "notes") and case.notes:
        story.append(PageBreak())
        story.append(build_notes_section(case, styles))

    # Images (optional)
    if options.get("include_images") and hasattr(case, "images") and case.images:
        story.append(PageBreak())
        story.append(build_images_section(case, styles))

    # Lab results
    if hasattr(case, "lab_results") and case.lab_results:
        story.append(PageBreak())
        story.append(build_lab_results_section(case, styles))

    # Footer disclaimer
    story.append(Spacer(1, 40))
    story.append(build_footer(case, styles))

    # Build PDF
    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()


# =============================================================================
# Section Builders
# =============================================================================


def build_header(case: MedicalCase, styles):
    """Build document header."""
    elements = []

    # Title
    elements.append(Paragraph(f"Medical Case Report", styles["CaseTitle"]))

    # Case info table
    case_data = [
        ["Case Number:", case.case_number or "N/A"],
        ["Status:", (case.status.value if case.status else "Pending").title()],
        ["Priority:", (case.urgency_level.value if case.urgency_level else "Moderate").title()],
        [
            "Created:",
            case.created_at.strftime("%B %d, %Y at %I:%M %p") if case.created_at else "N/A",
        ],
    ]

    table = Table(case_data, colWidths=[1.5 * inch, 3 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b7280")),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#111827")),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    elements.append(table)
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))

    return KeepTogether(elements)


def build_patient_section(case: MedicalCase, styles):
    """Build patient information section."""
    elements = []

    elements.append(Paragraph("Patient Information", styles["SectionTitle"]))

    patient = case.patient
    if not patient:
        elements.append(Paragraph("No patient information available", styles["Value"]))
        return KeepTogether(elements)

    # Calculate age
    age = "N/A"
    if hasattr(patient, "date_of_birth") and patient.date_of_birth:
        today = datetime.now()
        born = patient.date_of_birth
        age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    patient_data = [
        ["Name:", f"{patient.first_name} {patient.last_name}"],
        ["MRN:", patient.mrn or "N/A"],
        [
            "Date of Birth:",
            patient.date_of_birth.strftime("%B %d, %Y") if patient.date_of_birth else "N/A",
        ],
        ["Age/Gender:", f"{age} years / {(patient.gender or 'Unknown').title()}"],
        ["Contact:", patient.phone_primary or "N/A"],
    ]

    if hasattr(patient, "blood_type") and patient.blood_type:
        patient_data.append(["Blood Type:", patient.blood_type])

    table = Table(patient_data, colWidths=[1.5 * inch, 4 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b7280")),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    elements.append(table)
    return KeepTogether(elements)


def build_chief_complaint_section(case: MedicalCase, styles):
    """Build chief complaint section."""
    elements = []

    elements.append(Paragraph("Chief Complaint", styles["SectionTitle"]))

    cc = case.chief_complaint
    if isinstance(cc, dict):
        elements.append(Paragraph(cc.get("complaint", "N/A"), styles["Value"]))

        details = []
        if cc.get("duration"):
            details.append(f"Duration: {cc['duration']} {cc.get('duration_unit', '')}")
        if cc.get("onset"):
            details.append(f"Onset: {cc['onset']}")
        if cc.get("severity"):
            details.append(f"Severity: {cc['severity']}/10")

        if details:
            elements.append(Paragraph(" | ".join(details), styles["Label"]))
    else:
        elements.append(Paragraph(str(cc) if cc else "N/A", styles["Value"]))

    return KeepTogether(elements)


def build_vitals_section(case: MedicalCase, styles):
    """Build vital signs section."""
    elements = []

    elements.append(Paragraph("Vital Signs", styles["SectionTitle"]))

    vitals = case.vitals
    if isinstance(vitals, dict):
        vitals_data = [
            ["Blood Pressure", "Heart Rate", "Temperature", "SpO2", "Resp Rate"],
            [
                f"{vitals.get('systolic', '--')}/{vitals.get('diastolic', '--')} mmHg",
                f"{vitals.get('heart_rate', '--')} bpm",
                f"{vitals.get('temperature', '--')}°{vitals.get('temp_unit', 'F')}",
                f"{vitals.get('oxygen_saturation', '--')}%",
                f"{vitals.get('respiratory_rate', '--')}/min",
            ],
        ]

        table = Table(vitals_data, colWidths=[1.3 * inch] * 5)
        table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#6b7280")),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f9fafb")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(table)

    return KeepTogether(elements)


def build_symptoms_section(case: MedicalCase, styles):
    """Build symptoms section."""
    elements = []

    elements.append(Paragraph("Symptoms", styles["SectionTitle"]))

    symptoms = case.symptoms
    if symptoms:
        for symptom in symptoms:
            name = getattr(
                symptom,
                "name",
                symptom.get("name", "Unknown") if isinstance(symptom, dict) else str(symptom),
            )
            severity = getattr(
                symptom,
                "severity",
                symptom.get("severity", "N/A") if isinstance(symptom, dict) else "N/A",
            )
            elements.append(Paragraph(f"• {name} (Severity: {severity}/10)", styles["Value"]))
    else:
        elements.append(Paragraph("No symptoms recorded", styles["Value"]))

    return KeepTogether(elements)


def build_history_section(case: MedicalCase, styles):
    """Build medical history section."""
    elements = []

    elements.append(Paragraph("Medical History", styles["SectionTitle"]))

    history = case.medical_history
    if isinstance(history, dict):
        # Conditions
        if history.get("conditions"):
            elements.append(Paragraph("Conditions:", styles["SubSection"]))
            for c in history["conditions"]:
                name = c.get("condition", "Unknown")
                status = c.get("status", "")
                elements.append(Paragraph(f"• {name} ({status})", styles["Value"]))

        # Allergies
        if history.get("allergies"):
            elements.append(Paragraph("Allergies:", styles["SubSection"]))
            for a in history["allergies"]:
                allergen = a.get("allergen", "Unknown")
                severity = a.get("severity", "")
                elements.append(Paragraph(f"• {allergen} - {severity}", styles["Value"]))

    return KeepTogether(elements)


def build_ai_analysis_section(case: MedicalCase, styles):
    """Build AI analysis section."""
    elements = []

    elements.append(Paragraph("AI Clinical Analysis", styles["SectionTitle"]))

    analysis = case.ai_analysis
    if not analysis or not isinstance(analysis, dict):
        elements.append(Paragraph("No AI analysis available", styles["Value"]))
        return KeepTogether(elements)

    # Confidence
    confidence = analysis.get("confidence", 0)
    elements.append(Paragraph(f"Overall Confidence: {confidence * 100:.0f}%", styles["Value"]))
    elements.append(Spacer(1, 10))

    # Urgency assessment
    urgency = analysis.get("urgency_assessment", {})
    if urgency:
        elements.append(Paragraph("Urgency Assessment:", styles["SubSection"]))
        level = urgency.get("level", "Unknown").upper()
        elements.append(Paragraph(f"Level: {level}", styles["Value"]))
        if urgency.get("reasoning"):
            elements.append(Paragraph(urgency["reasoning"], styles["Value"]))

        # Red flags
        red_flags = urgency.get("red_flags", [])
        if red_flags:
            elements.append(Paragraph("Red Flags:", styles["Label"]))
            for flag in red_flags:
                elements.append(Paragraph(f"⚠ {flag}", styles["Value"]))

    elements.append(Spacer(1, 10))

    # Differential diagnosis
    dd = analysis.get("differential_diagnosis", [])
    if dd:
        elements.append(Paragraph("Differential Diagnosis:", styles["SubSection"]))

        dd_data = [["Diagnosis", "Probability", "ICD-10"]]
        for dx in dd[:5]:
            dd_data.append(
                [
                    dx.get("diagnosis", "Unknown"),
                    f"{dx.get('probability', 0) * 100:.0f}%",
                    dx.get("icd_code", "N/A"),
                ]
            )

        table = Table(dd_data, colWidths=[3 * inch, 1 * inch, 1 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        elements.append(table)

    # Disclaimer
    elements.append(Spacer(1, 15))
    disclaimer = analysis.get(
        "disclaimer",
        "This AI analysis is provided for clinical decision support only and should not replace professional medical judgment.",
    )
    elements.append(Paragraph(f"Disclaimer: {disclaimer}", styles["Disclaimer"]))

    return KeepTogether(elements)


def build_treatment_section(case: MedicalCase, styles):
    """Build treatment plan section."""
    elements = []

    elements.append(Paragraph("Treatment Plan", styles["SectionTitle"]))

    plan = case.treatment_plan
    if not plan:
        elements.append(Paragraph("No treatment plan defined", styles["Value"]))
        return KeepTogether(elements)

    # Diagnosis
    diagnosis = getattr(plan, "diagnosis", None) or (
        plan.get("diagnosis") if isinstance(plan, dict) else None
    )
    if diagnosis:
        elements.append(Paragraph("Diagnosis:", styles["SubSection"]))
        for dx in diagnosis:
            if isinstance(dx, dict):
                desc = dx.get("description", "Unknown")
                code = dx.get("code", "")
                dtype = dx.get("type", "").title()
                elements.append(Paragraph(f"• {desc} [{code}] - {dtype}", styles["Value"]))

    # Medications
    medications = getattr(plan, "medications", None) or (
        plan.get("medications") if isinstance(plan, dict) else None
    )
    if medications:
        elements.append(Paragraph("Medications:", styles["SubSection"]))

        med_data = [["Medication", "Dosage", "Frequency", "Route"]]
        for med in medications:
            if isinstance(med, dict):
                med_data.append(
                    [
                        med.get("medication", "N/A"),
                        med.get("dosage", "N/A"),
                        med.get("frequency", "N/A"),
                        med.get("route", "N/A"),
                    ]
                )

        if len(med_data) > 1:
            table = Table(med_data, colWidths=[2 * inch, 1.2 * inch, 1.2 * inch, 1 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            elements.append(table)

    return KeepTogether(elements)


def build_notes_section(case: MedicalCase, styles):
    """Build clinical notes section."""
    elements = []

    elements.append(Paragraph("Clinical Notes", styles["SectionTitle"]))

    notes = case.notes
    if not notes:
        elements.append(Paragraph("No clinical notes", styles["Value"]))
        return KeepTogether(elements)

    for note in notes:
        title = getattr(note, "title", "Clinical Note")
        author = getattr(note, "author", None)
        author_name = f"Dr. {author.last_name}" if author else "Unknown"
        created = getattr(note, "created_at", None)
        created_str = created.strftime("%B %d, %Y") if created else "N/A"

        elements.append(Paragraph(f"{title}", styles["SubSection"]))
        elements.append(Paragraph(f"By {author_name} on {created_str}", styles["Label"]))

        content = getattr(note, "content", "")
        # Strip HTML tags if present (simple approach)
        import re

        content = re.sub("<[^<]+?>", "", content)
        elements.append(Paragraph(content, styles["Value"]))
        elements.append(Spacer(1, 10))

    return KeepTogether(elements)


def build_images_section(case: MedicalCase, styles):
    """Build medical images section."""
    elements = []

    elements.append(Paragraph("Medical Images", styles["SectionTitle"]))

    images = case.images
    if not images:
        elements.append(Paragraph("No images attached", styles["Value"]))
        return KeepTogether(elements)

    elements.append(Paragraph(f"{len(images)} image(s) attached to this case", styles["Value"]))

    # Note: Actual image embedding would require downloading images
    # For now, just list them
    for img in images:
        img_type = getattr(img, "type", "Unknown")
        body_part = getattr(img, "body_part", "")
        desc = getattr(img, "description", "")
        elements.append(
            Paragraph(
                f"• {img_type.title()}{' - ' + body_part if body_part else ''}{': ' + desc if desc else ''}",
                styles["Value"],
            )
        )

    return KeepTogether(elements)


def build_lab_results_section(case: MedicalCase, styles):
    """Build lab results section."""
    elements = []

    elements.append(Paragraph("Laboratory Results", styles["SectionTitle"]))

    results = case.lab_results
    if not results:
        elements.append(Paragraph("No lab results available", styles["Value"]))
        return KeepTogether(elements)

    lab_data = [["Test", "Result", "Normal Range", "Status"]]

    for lab in results:
        if isinstance(lab, dict):
            status = lab.get("status", "normal")
            lab_data.append(
                [
                    lab.get("test_name", "Unknown"),
                    f"{lab.get('value', 'N/A')} {lab.get('unit', '')}",
                    f"{lab.get('normal_min', '')}-{lab.get('normal_max', '')} {lab.get('unit', '')}",
                    status.upper() if status in ["high", "low", "critical"] else status.title(),
                ]
            )

    if len(lab_data) > 1:
        table = Table(lab_data, colWidths=[2 * inch, 1.3 * inch, 1.5 * inch, 0.8 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        elements.append(table)

    return KeepTogether(elements)


def build_footer(case: MedicalCase, styles):
    """Build document footer."""
    elements = []

    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e5e7eb")))
    elements.append(Spacer(1, 10))
    elements.append(
        Paragraph(f"Generated by NeuraAxis Medical Platform on {timestamp}", styles["Footer"])
    )
    elements.append(
        Paragraph(
            "This document contains confidential medical information. Handle in accordance with HIPAA regulations.",
            styles["Footer"],
        )
    )

    return KeepTogether(elements)
