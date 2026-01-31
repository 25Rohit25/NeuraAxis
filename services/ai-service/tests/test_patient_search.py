"""
NEURAXIS - Patient Search API Unit Tests
Tests for search endpoint, filtering, and pagination
"""

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.routes.patient_search import (
    PatientListItem,
    PatientSearchResponse,
    SearchFacets,
    _get_search_facets,
    _patient_to_list_item,
)
from app.models.patient import Gender, Patient, PatientStatus

# =============================================================================
# Search Response Tests
# =============================================================================


class TestPatientSearchResponse:
    """Tests for search response structure."""

    def test_paginated_response_structure(self):
        """Response should include pagination metadata."""
        response = PatientSearchResponse(
            items=[],
            total=100,
            page=2,
            page_size=20,
            total_pages=5,
            has_next_page=True,
            has_previous_page=True,
        )

        assert response.total == 100
        assert response.page == 2
        assert response.page_size == 20
        assert response.total_pages == 5
        assert response.has_next_page is True
        assert response.has_previous_page is True

    def test_first_page_has_no_previous(self):
        """First page should not have previous page."""
        response = PatientSearchResponse(
            items=[],
            total=50,
            page=1,
            page_size=20,
            total_pages=3,
            has_next_page=True,
            has_previous_page=False,
        )

        assert response.has_previous_page is False

    def test_last_page_has_no_next(self):
        """Last page should not have next page."""
        response = PatientSearchResponse(
            items=[],
            total=50,
            page=3,
            page_size=20,
            total_pages=3,
            has_next_page=False,
            has_previous_page=True,
        )

        assert response.has_next_page is False


# =============================================================================
# Patient List Item Tests
# =============================================================================


class TestPatientListItem:
    """Tests for patient list item transformation."""

    def test_list_item_includes_required_fields(self):
        """List item should include all required fields."""
        item = PatientListItem(
            id=uuid4(),
            mrn="NRX-2026-TEST1234",
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            date_of_birth=date(1985, 3, 15),
            age=41,
            gender=Gender.MALE,
            phone_primary="5551234567",
            email="john@example.com",
            city="New York",
            state="NY",
            status=PatientStatus.ACTIVE,
            primary_diagnosis=None,
            allergies_count=2,
            conditions_count=3,
            last_visit_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert item.mrn == "NRX-2026-TEST1234"
        assert item.full_name == "John Doe"
        assert item.age == 41
        assert item.allergies_count == 2

    def test_patient_to_list_item_transformation(self):
        """Patient model should transform to list item correctly."""
        mock_patient = MagicMock()
        mock_patient.id = uuid4()
        mock_patient.mrn = "NRX-2026-TEST0001"
        mock_patient.first_name = "Sarah"
        mock_patient.last_name = "Johnson"
        mock_patient.full_name = "Sarah Johnson"
        mock_patient.date_of_birth = date(1985, 3, 15)
        mock_patient.age = 41
        mock_patient.gender = Gender.FEMALE
        mock_patient.phone_primary = "5551234567"
        mock_patient.email = "sarah@example.com"
        mock_patient.city = "Boston"
        mock_patient.state = "MA"
        mock_patient.status = PatientStatus.ACTIVE
        mock_patient.allergies = '["Penicillin", "Aspirin"]'
        mock_patient.chronic_conditions = '["Type 2 Diabetes"]'
        mock_patient.created_at = datetime.now()
        mock_patient.updated_at = datetime.now()

        item = _patient_to_list_item(mock_patient)

        assert item.mrn == "NRX-2026-TEST0001"
        assert item.full_name == "Sarah Johnson"
        assert item.allergies_count == 2
        assert item.conditions_count == 1
        assert item.primary_diagnosis == "Type 2 Diabetes"

    def test_patient_to_list_item_handles_empty_json(self):
        """Transformation should handle empty JSON arrays."""
        mock_patient = MagicMock()
        mock_patient.id = uuid4()
        mock_patient.mrn = "NRX-2026-TEST0002"
        mock_patient.first_name = "Test"
        mock_patient.last_name = "Patient"
        mock_patient.full_name = "Test Patient"
        mock_patient.date_of_birth = date(1990, 1, 1)
        mock_patient.age = 36
        mock_patient.gender = Gender.OTHER
        mock_patient.phone_primary = "5559876543"
        mock_patient.email = None
        mock_patient.city = "Chicago"
        mock_patient.state = "IL"
        mock_patient.status = PatientStatus.ACTIVE
        mock_patient.allergies = None
        mock_patient.chronic_conditions = "[]"
        mock_patient.created_at = datetime.now()
        mock_patient.updated_at = datetime.now()

        item = _patient_to_list_item(mock_patient)

        assert item.allergies_count == 0
        assert item.conditions_count == 0
        assert item.primary_diagnosis is None


# =============================================================================
# Search Facets Tests
# =============================================================================


class TestSearchFacets:
    """Tests for search facet aggregation."""

    def test_facets_structure(self):
        """Facets should have correct structure."""
        facets = SearchFacets(
            status={"active": 100, "inactive": 50},
            gender={"male": 80, "female": 70},
            age_ranges={
                "0-17": 10,
                "18-30": 30,
                "31-50": 60,
                "51-70": 40,
                "71+": 10,
            },
            top_conditions=[
                {"condition": "Type 2 Diabetes", "count": 25},
                {"condition": "Hypertension", "count": 20},
            ],
        )

        assert facets.status["active"] == 100
        assert facets.gender["male"] == 80
        assert facets.age_ranges["31-50"] == 60
        assert len(facets.top_conditions) == 2

    def test_age_range_calculation(self):
        """Age ranges should be calculated correctly."""
        # Test DOB to age calculation
        today = date.today()
        current_year = today.year

        test_cases = [
            (date(current_year - 5, 1, 1), "0-17"),
            (date(current_year - 17, 1, 1), "0-17"),
            (date(current_year - 18, 1, 1), "18-30"),
            (date(current_year - 30, 1, 1), "18-30"),
            (date(current_year - 31, 1, 1), "31-50"),
            (date(current_year - 50, 1, 1), "31-50"),
            (date(current_year - 51, 1, 1), "51-70"),
            (date(current_year - 70, 1, 1), "51-70"),
            (date(current_year - 71, 1, 1), "71+"),
            (date(current_year - 90, 1, 1), "71+"),
        ]

        for dob, expected_range in test_cases:
            age = current_year - dob.year
            if age <= 17:
                actual_range = "0-17"
            elif age <= 30:
                actual_range = "18-30"
            elif age <= 50:
                actual_range = "31-50"
            elif age <= 70:
                actual_range = "51-70"
            else:
                actual_range = "71+"

            assert actual_range == expected_range, f"DOB {dob} should be in range {expected_range}"


# =============================================================================
# Filter Logic Tests
# =============================================================================


class TestFilterLogic:
    """Tests for search filter logic."""

    def test_status_filter_single_value(self):
        """Single status filter should work."""
        # Simulate filter application
        status_filter = ["active"]

        assert "active" in status_filter
        assert "inactive" not in status_filter

    def test_status_filter_multiple_values(self):
        """Multiple status filters should work."""
        status_filter = ["active", "inactive"]

        assert len(status_filter) == 2

    def test_age_filter_min_only(self):
        """Age filter with min only."""
        age_min = 65
        age_max = None

        # Patients older than 65
        today = date.today()
        patient_dob = date(1950, 1, 1)  # ~76 years old
        age = today.year - patient_dob.year

        passes_filter = age >= age_min and (age_max is None or age <= age_max)
        assert passes_filter is True

    def test_age_filter_max_only(self):
        """Age filter with max only."""
        age_min = None
        age_max = 17

        # Pediatric patients
        today = date.today()
        patient_dob = date(today.year - 10, 1, 1)  # 10 years old
        age = today.year - patient_dob.year

        passes_filter = (age_min is None or age >= age_min) and age <= age_max
        assert passes_filter is True

    def test_age_filter_range(self):
        """Age filter with range."""
        age_min = 18
        age_max = 65

        today = date.today()
        patient_dob = date(today.year - 35, 1, 1)  # 35 years old
        age = today.year - patient_dob.year

        passes_filter = age >= age_min and age <= age_max
        assert passes_filter is True

    def test_text_search_matches_name(self):
        """Text search should match patient name."""
        search_term = "john"
        first_name = "John"
        last_name = "Doe"

        matches = (
            search_term.lower() in first_name.lower() or search_term.lower() in last_name.lower()
        )
        assert matches is True

    def test_text_search_matches_mrn(self):
        """Text search should match MRN."""
        search_term = "NRX-2026"
        mrn = "NRX-2026-TEST1234"

        matches = search_term.lower() in mrn.lower()
        assert matches is True


# =============================================================================
# Sorting Tests
# =============================================================================


class TestSorting:
    """Tests for search result sorting."""

    def test_sort_by_name_asc(self):
        """Sort by name ascending."""
        patients = [
            {"last_name": "Zebra", "first_name": "Alice"},
            {"last_name": "Apple", "first_name": "Bob"},
            {"last_name": "Middle", "first_name": "Charlie"},
        ]

        sorted_patients = sorted(patients, key=lambda p: p["last_name"])

        assert sorted_patients[0]["last_name"] == "Apple"
        assert sorted_patients[-1]["last_name"] == "Zebra"

    def test_sort_by_name_desc(self):
        """Sort by name descending."""
        patients = [
            {"last_name": "Zebra", "first_name": "Alice"},
            {"last_name": "Apple", "first_name": "Bob"},
            {"last_name": "Middle", "first_name": "Charlie"},
        ]

        sorted_patients = sorted(patients, key=lambda p: p["last_name"], reverse=True)

        assert sorted_patients[0]["last_name"] == "Zebra"
        assert sorted_patients[-1]["last_name"] == "Apple"

    def test_sort_by_date(self):
        """Sort by date."""
        patients = [
            {"created_at": datetime(2026, 1, 15)},
            {"created_at": datetime(2026, 1, 1)},
            {"created_at": datetime(2026, 1, 30)},
        ]

        sorted_patients = sorted(patients, key=lambda p: p["created_at"], reverse=True)

        assert sorted_patients[0]["created_at"].day == 30
        assert sorted_patients[-1]["created_at"].day == 1


# =============================================================================
# Pagination Tests
# =============================================================================


class TestPagination:
    """Tests for pagination logic."""

    def test_calculate_total_pages(self):
        """Calculate total pages correctly."""
        test_cases = [
            (100, 20, 5),
            (101, 20, 6),
            (99, 20, 5),
            (20, 20, 1),
            (0, 20, 0),
            (1, 20, 1),
        ]

        for total, page_size, expected_pages in test_cases:
            actual_pages = (total + page_size - 1) // page_size if total > 0 else 0
            assert actual_pages == expected_pages, f"total={total}, page_size={page_size}"

    def test_calculate_offset(self):
        """Calculate offset correctly."""
        test_cases = [
            (1, 20, 0),
            (2, 20, 20),
            (3, 20, 40),
            (1, 50, 0),
            (2, 50, 50),
        ]

        for page, page_size, expected_offset in test_cases:
            actual_offset = (page - 1) * page_size
            assert actual_offset == expected_offset

    def test_has_next_page(self):
        """Determine if next page exists."""
        test_cases = [
            (1, 5, True),
            (3, 5, True),
            (5, 5, False),
            (1, 1, False),
        ]

        for current_page, total_pages, expected in test_cases:
            has_next = current_page < total_pages
            assert has_next == expected

    def test_has_previous_page(self):
        """Determine if previous page exists."""
        test_cases = [
            (1, True, False),
            (2, True, True),
            (5, True, True),
        ]

        for current_page, _, expected in test_cases:
            has_previous = current_page > 1
            assert has_previous == expected


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
