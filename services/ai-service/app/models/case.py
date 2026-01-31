"""
NEURAXIS - Medical Case Model
SQLAlchemy models for medical cases
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CaseStatus(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class MedicalCase(Base):
    """Medical case model."""

    __tablename__ = "medical_cases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_number = Column(String(20), unique=True, nullable=False, index=True)

    # Patient reference
    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    patient = relationship("Patient", back_populates="cases")

    # Status
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.PENDING, nullable=False)
    urgency_level = Column(SQLEnum(UrgencyLevel), default=UrgencyLevel.MODERATE, nullable=False)

    # Chief complaint
    chief_complaint = Column(Text, nullable=False)
    complaint_duration = Column(String(50))
    complaint_duration_unit = Column(String(20))
    complaint_onset = Column(String(20))
    complaint_severity = Column(Integer)
    complaint_location = Column(String(100))
    complaint_character = Column(String(200))
    aggravating_factors = Column(JSON)  # List of strings
    relieving_factors = Column(JSON)  # List of strings

    # Vitals snapshot
    vitals_bp_systolic = Column(Integer)
    vitals_bp_diastolic = Column(Integer)
    vitals_heart_rate = Column(Integer)
    vitals_temperature = Column(Float)
    vitals_temp_unit = Column(String(1))
    vitals_o2_saturation = Column(Integer)
    vitals_respiratory_rate = Column(Integer)
    vitals_weight = Column(Float)
    vitals_weight_unit = Column(String(3))
    vitals_height = Column(Float)
    vitals_height_unit = Column(String(2))
    vitals_pain_level = Column(Integer)
    vitals_recorded_at = Column(DateTime(timezone=True))

    # Assessment
    clinical_impression = Column(Text)
    differential_diagnosis = Column(JSON)  # List of strings
    recommended_tests = Column(JSON)  # List of strings
    treatment_plan = Column(Text)
    follow_up_instructions = Column(Text)

    # AI analysis
    ai_suggestions = Column(JSON)
    ai_confidence = Column(Float)

    # Audit
    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_to = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    symptoms = relationship("CaseSymptom", back_populates="case", cascade="all, delete-orphan")
    medications = relationship(
        "CaseMedication", back_populates="case", cascade="all, delete-orphan"
    )
    images = relationship("CaseImage", back_populates="case", cascade="all, delete-orphan")
    history_items = relationship(
        "CaseHistoryItem", back_populates="case", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_cases_patient_status", "patient_id", "status"),
        Index("ix_cases_created_at", "created_at"),
        Index("ix_cases_urgency", "urgency_level"),
    )


class CaseSymptom(Base):
    """Case symptom model."""

    __tablename__ = "case_symptoms"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(PGUUID(as_uuid=True), ForeignKey("medical_cases.id"), nullable=False)

    code = Column(String(20))
    name = Column(String(200), nullable=False)
    category = Column(String(50))
    severity = Column(Integer, nullable=False)
    duration = Column(String(50))
    notes = Column(Text)
    is_ai_suggested = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("MedicalCase", back_populates="symptoms")


class CaseMedication(Base):
    """Medication recorded with case."""

    __tablename__ = "case_medications"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(PGUUID(as_uuid=True), ForeignKey("medical_cases.id"), nullable=False)

    name = Column(String(200), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    route = Column(String(50))
    start_date = Column(DateTime(timezone=True))
    prescribed_by = Column(String(200))
    is_active = Column(Boolean, default=True)
    is_from_patient_record = Column(Boolean, default=False)
    compliance = Column(String(20))  # taking, not_taking, inconsistent

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("MedicalCase", back_populates="medications")


class CaseImage(Base):
    """Image/document attached to case."""

    __tablename__ = "case_images"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(PGUUID(as_uuid=True), ForeignKey("medical_cases.id"), nullable=False)

    type = Column(String(20))  # photo, xray, scan, document, other
    body_part = Column(String(100))
    description = Column(Text)
    file_name = Column(String(255))
    file_size = Column(Integer)
    file_type = Column(String(50))
    url = Column(String(500))
    thumbnail_url = Column(String(500))

    uploaded_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("MedicalCase", back_populates="images")


class CaseHistoryItem(Base):
    """Medical history items recorded with case."""

    __tablename__ = "case_history_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    case_id = Column(PGUUID(as_uuid=True), ForeignKey("medical_cases.id"), nullable=False)

    type = Column(String(20))  # condition, allergy, surgery, family
    name = Column(String(200), nullable=False)
    status = Column(String(20))
    severity = Column(String(20))
    diagnosis_date = Column(DateTime(timezone=True))
    relationship = Column(String(50))  # For family history
    notes = Column(Text)
    is_from_patient_record = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    case = relationship("MedicalCase", back_populates="history_items")


class CaseDraft(Base):
    """Draft cases for auto-save functionality."""

    __tablename__ = "case_drafts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    patient_id = Column(PGUUID(as_uuid=True), ForeignKey("patients.id"), nullable=True)
    patient_name = Column(String(200))
    chief_complaint = Column(Text)
    current_step = Column(Integer, default=0)
    data = Column(JSON, nullable=False)

    created_by = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (Index("ix_case_drafts_user", "created_by", "updated_at"),)


class SymptomDatabase(Base):
    """Medical symptom database for search/autocomplete."""

    __tablename__ = "symptom_database"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    common_severity = Column(Integer)
    related_symptoms = Column(JSON)  # List of symptom codes
    synonyms = Column(JSON)  # List of alternative names
    icd_codes = Column(JSON)  # List of ICD-10 codes

    is_active = Column(Boolean, default=True)

    __table_args__ = (Index("ix_symptom_name_search", "name"),)
