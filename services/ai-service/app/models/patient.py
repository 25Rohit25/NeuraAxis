"""
NEURAXIS - Patient SQLAlchemy Model
Comprehensive patient data model with audit fields
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    DOMESTIC_PARTNERSHIP = "domestic_partnership"


class BloodType(str, Enum):
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    UNKNOWN = "unknown"


class PatientStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DECEASED = "deceased"
    TRANSFERRED = "transferred"


class Patient(Base):
    """Patient model with comprehensive demographic and medical information."""

    __tablename__ = "patients"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Medical Record Number - unique identifier
    mrn: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    # Organization (for multi-tenancy)
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Demographics
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(SQLEnum(Gender), nullable=False)
    marital_status: Mapped[Optional[MaritalStatus]] = mapped_column(
        SQLEnum(MaritalStatus), nullable=True
    )

    # Contact Information
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_primary: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_secondary: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Address
    address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), default="United States")

    # Medical Information
    blood_type: Mapped[Optional[BloodType]] = mapped_column(SQLEnum(BloodType), nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(nullable=True)

    # Allergies and conditions stored as JSON arrays
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    chronic_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    current_medications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    past_surgeries: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    family_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Emergency Contact
    emergency_contact_name: Mapped[str] = mapped_column(String(200), nullable=False)
    emergency_contact_relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    emergency_contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    emergency_contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Insurance Information
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    insurance_policy_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_group_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    insurance_document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[PatientStatus] = mapped_column(
        SQLEnum(PatientStatus),
        default=PatientStatus.ACTIVE,
        nullable=False,
    )

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_patients_name_dob", "last_name", "first_name", "date_of_birth"),
        Index("ix_patients_org_status", "organization_id", "status"),
        UniqueConstraint(
            "organization_id",
            "first_name",
            "last_name",
            "date_of_birth",
            name="uq_patient_identity",
        ),
    )

    def __repr__(self) -> str:
        return f"<Patient {self.mrn}: {self.last_name}, {self.first_name}>"

    @property
    def full_name(self) -> str:
        """Return the patient's full name."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def age(self) -> int:
        """Calculate patient's age."""
        today = date.today()
        return (
            today.year
            - self.date_of_birth.year
            - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        )
