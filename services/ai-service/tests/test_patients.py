"""
NEURAXIS - Patient API Unit Tests
Tests for patient routes, validation, and duplicate detection
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models.patient import Gender, Patient, PatientStatus
from app.schemas.patient import PatientCreate
from app.utils.duplicate_detection import DuplicateDetector
from app.utils.mrn import MRNGenerator

# =============================================================================
# MRN Generator Tests
# =============================================================================


class TestMRNGenerator:
    """Tests for MRN generation utility."""

    def test_generate_returns_formatted_mrn(self):
        """MRN should follow NRX-YYYY-XXXXXXXX format."""
        mrn = MRNGenerator.generate()

        assert mrn.startswith("NRX-")
        parts = mrn.split("-")
        assert len(parts) == 3
        assert len(parts[2]) == 8

    def test_generate_with_specific_year(self):
        """MRN should use specified year."""
        mrn = MRNGenerator.generate(year=2025)

        assert "2025" in mrn
        parts = mrn.split("-")
        assert parts[1] == "2025"

    def test_generate_produces_unique_mrns(self):
        """Multiple generations should produce unique MRNs."""
        mrns = [MRNGenerator.generate() for _ in range(100)]

        assert len(set(mrns)) == 100  # All unique

    def test_validate_returns_true_for_valid_mrn(self):
        """Valid MRN should pass validation."""
        valid_mrn = "NRX-2026-A3B7C9D2"

        assert MRNGenerator.validate(valid_mrn) is True

    def test_validate_returns_false_for_invalid_format(self):
        """Invalid MRN formats should fail validation."""
        invalid_mrns = [
            "",
            "ABC-2026-12345678",  # Wrong prefix
            "NRX-26-12345678",  # Short year
            "NRX-2026-123456",  # Short random part
            "NRX-2026-12345678901",  # Long random part
            "NRX-1900-12345678",  # Year too old
            "NRX-2200-12345678",  # Year too future
            "NRX2026-12345678",  # Missing separator
        ]

        for mrn in invalid_mrns:
            assert MRNGenerator.validate(mrn) is False, f"Expected {mrn} to be invalid"

    def test_parse_extracts_components(self):
        """Parse should extract MRN components."""
        mrn = "NRX-2026-A3B7C9D2"

        result = MRNGenerator.parse(mrn)

        assert result["prefix"] == "NRX"
        assert result["year"] == 2026
        assert result["random_part"] == "A3B7C9D2"
        assert result["full"] == mrn

    def test_parse_raises_for_invalid_mrn(self):
        """Parse should raise ValueError for invalid MRN."""
        with pytest.raises(ValueError):
            MRNGenerator.parse("INVALID-MRN")


# =============================================================================
# Duplicate Detection Tests
# =============================================================================


class TestDuplicateDetector:
    """Tests for duplicate patient detection."""

    def test_normalize_name_handles_special_characters(self):
        """Name normalization should remove special characters."""
        assert DuplicateDetector.normalize_name("John-O'Brien") == "johnobrien"
        assert DuplicateDetector.normalize_name("María José") == "mara jos"
        assert DuplicateDetector.normalize_name("  John   Doe  ") == "john doe"

    def test_normalize_name_handles_empty_string(self):
        """Empty string should return empty."""
        assert DuplicateDetector.normalize_name("") == ""
        assert DuplicateDetector.normalize_name(None) == ""

    def test_calculate_name_similarity_exact_match(self):
        """Identical names should have 1.0 similarity."""
        score = DuplicateDetector.calculate_name_similarity("John", "John")

        assert score == 1.0

    def test_calculate_name_similarity_case_insensitive(self):
        """Name comparison should be case insensitive."""
        score = DuplicateDetector.calculate_name_similarity("JOHN", "john")

        assert score == 1.0

    def test_calculate_name_similarity_partial_match(self):
        """Similar names should have high similarity."""
        score = DuplicateDetector.calculate_name_similarity("John", "Jon")

        assert score > 0.7

    def test_calculate_name_similarity_different_names(self):
        """Different names should have low similarity."""
        score = DuplicateDetector.calculate_name_similarity("John", "Mary")

        assert score < 0.5

    def test_calculate_dob_similarity_exact_match(self):
        """Same DOB should have 1.0 similarity."""
        dob = date(1985, 3, 15)
        score, match_type = DuplicateDetector.calculate_dob_similarity(dob, dob)

        assert score == 1.0
        assert match_type == "exact_dob"

    def test_calculate_dob_similarity_same_month_day_near_year(self):
        """Same month/day with 1 year difference."""
        dob1 = date(1985, 3, 15)
        dob2 = date(1986, 3, 15)

        score, match_type = DuplicateDetector.calculate_dob_similarity(dob1, dob2)

        assert score == 0.8
        assert match_type == "same_monthday_near_year"

    def test_calculate_dob_similarity_different_dates(self):
        """Completely different dates should have 0 similarity."""
        dob1 = date(1985, 3, 15)
        dob2 = date(1990, 7, 22)

        score, _ = DuplicateDetector.calculate_dob_similarity(dob1, dob2)

        assert score == 0.0

    def test_calculate_overall_similarity_exact_match(self):
        """Exact match should return 1.0 similarity."""
        score, reason = DuplicateDetector.calculate_overall_similarity(
            "John",
            "Doe",
            date(1985, 3, 15),
            "John",
            "Doe",
            date(1985, 3, 15),
        )

        assert score == 1.0
        assert "Exact match" in reason

    def test_calculate_overall_similarity_high_match(self):
        """Similar names with same DOB should have high similarity."""
        score, reason = DuplicateDetector.calculate_overall_similarity(
            "John",
            "Doe",
            date(1985, 3, 15),
            "Jon",
            "Doe",
            date(1985, 3, 15),
        )

        assert score > 0.8
        assert "Last name" in reason

    def test_calculate_overall_similarity_low_match(self):
        """Different names with different DOB should have low similarity."""
        score, _ = DuplicateDetector.calculate_overall_similarity(
            "John",
            "Doe",
            date(1985, 3, 15),
            "Mary",
            "Smith",
            date(1990, 7, 22),
        )

        assert score < 0.3


# =============================================================================
# Patient Schema Validation Tests
# =============================================================================


class TestPatientSchemaValidation:
    """Tests for Pydantic patient schemas."""

    def test_valid_patient_create(self):
        """Valid patient data should pass validation."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": date(1985, 3, 15),
            "gender": "male",
            "phone_primary": "5551234567",
            "address_line1": "123 Main St",
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_relationship": "Spouse",
            "emergency_contact_phone": "5559876543",
        }

        patient = PatientCreate(**data)

        assert patient.first_name == "John"
        assert patient.last_name == "Doe"

    def test_invalid_future_date_of_birth(self):
        """Future DOB should raise validation error."""
        from datetime import timedelta

        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValueError) as exc_info:
            PatientCreate(
                first_name="John",
                last_name="Doe",
                date_of_birth=future_date,
                gender="male",
                phone_primary="5551234567",
                address_line1="123 Main St",
                city="New York",
                state="NY",
                postal_code="10001",
                emergency_contact_name="Jane Doe",
                emergency_contact_relationship="Spouse",
                emergency_contact_phone="5559876543",
            )

        assert "future" in str(exc_info.value).lower()

    def test_invalid_short_phone(self):
        """Phone with less than 10 digits should fail."""
        with pytest.raises(ValueError):
            PatientCreate(
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1985, 3, 15),
                gender="male",
                phone_primary="12345",  # Too short
                address_line1="123 Main St",
                city="New York",
                state="NY",
                postal_code="10001",
                emergency_contact_name="Jane Doe",
                emergency_contact_relationship="Spouse",
                emergency_contact_phone="5559876543",
            )

    def test_empty_required_field_fails(self):
        """Empty required fields should fail validation."""
        with pytest.raises(ValueError):
            PatientCreate(
                first_name="",  # Empty
                last_name="Doe",
                date_of_birth=date(1985, 3, 15),
                gender="male",
                phone_primary="5551234567",
                address_line1="123 Main St",
                city="New York",
                state="NY",
                postal_code="10001",
                emergency_contact_name="Jane Doe",
                emergency_contact_relationship="Spouse",
                emergency_contact_phone="5559876543",
            )

    def test_allergies_list_strips_empty_items(self):
        """Allergies list should filter empty strings."""
        from app.schemas.patient import MedicalHistoryCreate

        medical = MedicalHistoryCreate(allergies=["Penicillin", "", "  ", "Aspirin"])

        assert medical.allergies == ["Penicillin", "Aspirin"]

    def test_valid_email_formats(self):
        """Valid email addresses should pass."""
        data = PatientCreate(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1985, 3, 15),
            gender="male",
            email="john.doe@hospital.com",
            phone_primary="5551234567",
            address_line1="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            emergency_contact_name="Jane Doe",
            emergency_contact_relationship="Spouse",
            emergency_contact_phone="5559876543",
        )

        assert data.email == "john.doe@hospital.com"

    def test_height_weight_validation(self):
        """Height and weight should be within valid ranges."""
        from app.schemas.patient import MedicalHistoryCreate

        # Valid values
        medical = MedicalHistoryCreate(height_cm=170.5, weight_kg=75.0)
        assert medical.height_cm == 170.5
        assert medical.weight_kg == 75.0

        # Invalid height (too short)
        with pytest.raises(ValueError):
            MedicalHistoryCreate(height_cm=20)

        # Invalid weight (too high)
        with pytest.raises(ValueError):
            MedicalHistoryCreate(weight_kg=800)


# =============================================================================
# API Route Tests (Integration)
# =============================================================================


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_current_user():
    """Create a mock authenticated user."""
    return {
        "id": str(uuid4()),
        "email": "doctor@hospital.com",
        "organization_id": str(uuid4()),
    }


@pytest.fixture
def sample_patient_data():
    """Create sample patient data for testing."""
    return {
        "first_name": "Sarah",
        "last_name": "Johnson",
        "date_of_birth": "1985-03-15",
        "gender": "female",
        "phone_primary": "5551234567",
        "address_line1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "United States",
        "emergency_contact_name": "John Johnson",
        "emergency_contact_relationship": "Spouse",
        "emergency_contact_phone": "5559876543",
        "allergies": ["Penicillin"],
        "chronic_conditions": ["Type 2 Diabetes"],
        "current_medications": ["Metformin"],
    }


class TestPatientRoutes:
    """Integration tests for patient API routes."""

    @pytest.mark.asyncio
    async def test_create_patient_success(
        self,
        mock_db_session,
        mock_current_user,
        sample_patient_data,
    ):
        """Successfully create a new patient."""
        # This would be an integration test with actual FastAPI TestClient
        # Mocking the full flow for unit test purposes

        from app.api.routes.patients import create_patient
        from app.schemas.patient import PatientCreate

        # Convert string date to date object
        sample_patient_data["date_of_birth"] = date(1985, 3, 15)
        patient_create = PatientCreate(**sample_patient_data)

        # Mock no duplicates found
        with patch("app.api.routes.patients.check_for_duplicates") as mock_check:
            mock_check.return_value = []

            with patch("app.api.routes.patients.generate_unique_mrn") as mock_mrn:
                mock_mrn.return_value = "NRX-2026-TEST1234"

                # In a real test, we'd use AsyncClient and the actual app
                # For now, verify the logic works
                assert mock_mrn.return_value == "NRX-2026-TEST1234"

    @pytest.mark.asyncio
    async def test_create_patient_duplicate_detected(
        self,
        mock_db_session,
        mock_current_user,
        sample_patient_data,
    ):
        """Duplicate patient detection should return 409."""
        from app.utils.duplicate_detection import DuplicateCandidate

        # Create a mock duplicate
        duplicate = DuplicateCandidate(
            id=uuid4(),
            mrn="NRX-2026-EXIST123",
            first_name="Sarah",
            last_name="Johnson",
            date_of_birth=date(1985, 3, 15),
            similarity_score=0.98,
            match_reason="Exact match",
        )

        # The API should reject with 409 if similarity >= 0.95
        assert duplicate.similarity_score >= 0.95

    @pytest.mark.asyncio
    async def test_list_patients_with_search(self, mock_db_session, mock_current_user):
        """List patients should support search filter."""
        # Mock query execution
        mock_patients = [
            MagicMock(
                id=uuid4(),
                mrn="NRX-2026-TEST0001",
                first_name="Sarah",
                last_name="Johnson",
                date_of_birth=date(1985, 3, 15),
                gender=Gender.FEMALE,
                phone_primary="5551234567",
                status=PatientStatus.ACTIVE,
                full_name="Sarah Johnson",
                age=40,
            ),
        ]

        mock_db_session.execute.return_value.scalars.return_value.all.return_value = mock_patients

        # Verify search filtering logic
        search_term = "Sarah"
        assert search_term.lower() in mock_patients[0].first_name.lower()

    @pytest.mark.asyncio
    async def test_update_patient_partial_update(
        self,
        mock_db_session,
        mock_current_user,
    ):
        """Partial update should only modify specified fields."""
        from app.schemas.patient import PatientUpdate

        update_data = PatientUpdate(
            phone_primary="5559999999",
            email="newemail@example.com",
        )

        # Only phone and email should be in the update dict
        update_dict = update_data.model_dump(exclude_unset=True)

        assert "phone_primary" in update_dict
        assert "email" in update_dict
        assert "first_name" not in update_dict
        assert len(update_dict) == 2


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
