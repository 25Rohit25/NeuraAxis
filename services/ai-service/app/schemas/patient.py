"""
NEURAXIS - Patient Pydantic Schemas
Request/Response schemas for patient API endpoints
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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


# =============================================================================
# Step 1: Demographics Schema
# =============================================================================


class DemographicsCreate(BaseModel):
    """Step 1: Patient demographics information."""

    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender
    marital_status: Optional[MaritalStatus] = None

    # Contact
    email: Optional[EmailStr] = None
    phone_primary: str = Field(..., min_length=10, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)

    # Address
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=5, max_length=20)
    country: str = Field(default="United States", max_length=100)

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: date) -> date:
        today = date.today()
        if v > today:
            raise ValueError("Date of birth cannot be in the future")
        if v.year < 1900:
            raise ValueError("Date of birth must be after 1900")
        return v

    @field_validator("phone_primary", "phone_secondary")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        # Remove non-digit characters for validation
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v


# =============================================================================
# Step 2: Medical History Schema
# =============================================================================


class MedicalHistoryCreate(BaseModel):
    """Step 2: Patient medical history information."""

    blood_type: Optional[BloodType] = None
    height_cm: Optional[float] = Field(None, ge=30, le=300)
    weight_kg: Optional[float] = Field(None, ge=0.5, le=700)

    allergies: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    past_surgeries: list[str] = Field(default_factory=list)
    family_history: Optional[str] = Field(None, max_length=5000)

    @field_validator("allergies", "chronic_conditions", "current_medications", "past_surgeries")
    @classmethod
    def validate_list_items(cls, v: list[str]) -> list[str]:
        # Remove empty strings and strip whitespace
        return [item.strip() for item in v if item.strip()]


# =============================================================================
# Step 3: Emergency Contact Schema
# =============================================================================


class EmergencyContactCreate(BaseModel):
    """Step 3: Emergency contact and insurance information."""

    # Emergency Contact
    emergency_contact_name: str = Field(..., min_length=1, max_length=200)
    emergency_contact_relationship: str = Field(..., min_length=1, max_length=50)
    emergency_contact_phone: str = Field(..., min_length=10, max_length=20)
    emergency_contact_email: Optional[EmailStr] = None

    # Insurance (optional)
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_group_number: Optional[str] = Field(None, max_length=100)

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: str) -> str:
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v


# =============================================================================
# Combined Create Schema
# =============================================================================


class PatientCreate(BaseModel):
    """Complete patient creation schema combining all steps."""

    # Demographics (Step 1)
    first_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender
    marital_status: Optional[MaritalStatus] = None
    email: Optional[EmailStr] = None
    phone_primary: str = Field(..., min_length=10, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postal_code: str = Field(..., min_length=5, max_length=20)
    country: str = Field(default="United States", max_length=100)

    # Medical History (Step 2)
    blood_type: Optional[BloodType] = None
    height_cm: Optional[float] = Field(None, ge=30, le=300)
    weight_kg: Optional[float] = Field(None, ge=0.5, le=700)
    allergies: list[str] = Field(default_factory=list)
    chronic_conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    past_surgeries: list[str] = Field(default_factory=list)
    family_history: Optional[str] = Field(None, max_length=5000)

    # Emergency Contact (Step 3)
    emergency_contact_name: str = Field(..., min_length=1, max_length=200)
    emergency_contact_relationship: str = Field(..., min_length=1, max_length=50)
    emergency_contact_phone: str = Field(..., min_length=10, max_length=20)
    emergency_contact_email: Optional[EmailStr] = None

    # Insurance
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_group_number: Optional[str] = Field(None, max_length=100)
    insurance_document_url: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Update Schema
# =============================================================================


class PatientUpdate(BaseModel):
    """Patient update schema - all fields optional."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = Field(None, min_length=10, max_length=20)
    phone_secondary: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    postal_code: Optional[str] = Field(None, min_length=5, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    blood_type: Optional[BloodType] = None
    height_cm: Optional[float] = Field(None, ge=30, le=300)
    weight_kg: Optional[float] = Field(None, ge=0.5, le=700)
    allergies: Optional[list[str]] = None
    chronic_conditions: Optional[list[str]] = None
    current_medications: Optional[list[str]] = None
    past_surgeries: Optional[list[str]] = None
    family_history: Optional[str] = Field(None, max_length=5000)
    emergency_contact_name: Optional[str] = Field(None, min_length=1, max_length=200)
    emergency_contact_relationship: Optional[str] = Field(None, min_length=1, max_length=50)
    emergency_contact_phone: Optional[str] = Field(None, min_length=10, max_length=20)
    emergency_contact_email: Optional[EmailStr] = None
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_group_number: Optional[str] = Field(None, max_length=100)
    insurance_document_url: Optional[str] = Field(None, max_length=500)
    status: Optional[PatientStatus] = None


# =============================================================================
# Response Schemas
# =============================================================================


class PatientResponse(BaseModel):
    """Patient response schema."""

    id: UUID
    mrn: str
    organization_id: UUID

    # Demographics
    first_name: str
    middle_name: Optional[str]
    last_name: str
    full_name: str
    date_of_birth: date
    age: int
    gender: Gender
    marital_status: Optional[MaritalStatus]

    # Contact
    email: Optional[str]
    phone_primary: str
    phone_secondary: Optional[str]

    # Address
    address_line1: str
    address_line2: Optional[str]
    city: str
    state: str
    postal_code: str
    country: str

    # Medical
    blood_type: Optional[BloodType]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    allergies: list[str]
    chronic_conditions: list[str]
    current_medications: list[str]
    past_surgeries: list[str]
    family_history: Optional[str]

    # Emergency Contact
    emergency_contact_name: str
    emergency_contact_relationship: str
    emergency_contact_phone: str
    emergency_contact_email: Optional[str]

    # Insurance
    insurance_provider: Optional[str]
    insurance_policy_number: Optional[str]
    insurance_group_number: Optional[str]
    insurance_document_url: Optional[str]

    # Status
    status: PatientStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientSummary(BaseModel):
    """Condensed patient information for lists."""

    id: UUID
    mrn: str
    full_name: str
    date_of_birth: date
    age: int
    gender: Gender
    phone_primary: str
    status: PatientStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientList(BaseModel):
    """Paginated patient list response."""

    items: list[PatientSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Duplicate Detection Schema
# =============================================================================


class DuplicateCheckRequest(BaseModel):
    """Request for duplicate patient detection."""

    first_name: str
    last_name: str
    date_of_birth: date


class PotentialDuplicate(BaseModel):
    """Potential duplicate patient information."""

    id: UUID
    mrn: str
    full_name: str
    date_of_birth: date
    similarity_score: float = Field(..., ge=0, le=1)
    match_reason: str


class DuplicateCheckResponse(BaseModel):
    """Response for duplicate detection."""

    has_duplicates: bool
    potential_duplicates: list[PotentialDuplicate]
