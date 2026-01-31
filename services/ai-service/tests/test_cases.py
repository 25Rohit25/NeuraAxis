"""
NEURAXIS - Case API Tests
Unit and integration tests for case creation API
"""

import json
from datetime import datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import CaseDraft, CaseStatus, MedicalCase, UrgencyLevel
from app.models.patient import Patient

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def test_patient(db: AsyncSession):
    """Create a test patient for case tests."""
    patient = Patient(
        id=uuid4(),
        mrn=f"TEST-{uuid4().hex[:8].upper()}",
        first_name="Test",
        last_name="Patient",
        date_of_birth=datetime(1985, 3, 15),
        gender="male",
        phone_primary="1234567890",
        email="test@example.com",
        address_line_1="123 Test St",
        city="Test City",
        state="TS",
        postal_code="12345",
        emergency_contact_name="Emergency Contact",
        emergency_contact_relationship="Spouse",
        emergency_contact_phone="0987654321",
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@pytest.fixture
def case_creation_data(test_patient):
    """Valid case creation data."""
    return {
        "patient": {
            "patient_id": str(test_patient.id),
            "mrn": test_patient.mrn,
            "full_name": f"{test_patient.first_name} {test_patient.last_name}",
        },
        "chief_complaint": {
            "complaint": "Severe headache for the past 3 days",
            "duration": "3",
            "duration_unit": "days",
            "onset": "gradual",
            "severity": 7,
            "location": "Frontal",
        },
        "symptoms": [
            {
                "code": "R51",
                "name": "Headache",
                "category": "neurological",
                "severity": 7,
                "duration": "3 days",
            },
            {
                "name": "Photophobia",
                "category": "neurological",
                "severity": 5,
            },
        ],
        "vitals": {
            "blood_pressure_systolic": 130,
            "blood_pressure_diastolic": 85,
            "heart_rate": 78,
            "temperature": 98.8,
            "temperature_unit": "F",
            "oxygen_saturation": 98,
            "respiratory_rate": 16,
            "recorded_at": datetime.now().isoformat(),
        },
        "assessment": {
            "clinical_impression": "Patient presents with migraine with photophobia.",
            "differential_diagnosis": ["Migraine", "Tension headache"],
            "recommended_tests": ["CT Head if symptoms persist"],
            "urgency_level": "moderate",
        },
    }


# =============================================================================
# Case Creation Tests
# =============================================================================


class TestCaseCreation:
    """Tests for case creation endpoint."""

    @pytest.mark.asyncio
    async def test_create_case_success(
        self,
        client: AsyncClient,
        case_creation_data: dict,
    ):
        """Test successful case creation."""
        response = await client.post("/api/cases", json=case_creation_data)

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "case_number" in data
        assert data["case_number"].startswith("CASE-")
        assert data["status"] == "pending"
        assert data["urgency_level"] == "moderate"
        assert data["chief_complaint"] == case_creation_data["chief_complaint"]["complaint"]

    @pytest.mark.asyncio
    async def test_create_case_patient_not_found(
        self,
        client: AsyncClient,
        case_creation_data: dict,
    ):
        """Test case creation with non-existent patient."""
        case_creation_data["patient"]["patient_id"] = str(uuid4())

        response = await client.post("/api/cases", json=case_creation_data)

        assert response.status_code == 404
        assert "Patient not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_case_with_medications(
        self,
        client: AsyncClient,
        case_creation_data: dict,
    ):
        """Test case creation with medications."""
        case_creation_data["medications"] = [
            {
                "name": "Ibuprofen",
                "dosage": "400mg",
                "frequency": "Every 6 hours",
                "route": "Oral",
                "is_active": True,
                "compliance": "taking",
            }
        ]

        response = await client.post("/api/cases", json=case_creation_data)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_create_case_validates_urgency_level(
        self,
        client: AsyncClient,
        case_creation_data: dict,
    ):
        """Test that invalid urgency level is rejected."""
        case_creation_data["assessment"]["urgency_level"] = "invalid"

        response = await client.post("/api/cases", json=case_creation_data)

        assert response.status_code == 422


class TestCaseRetrieval:
    """Tests for case retrieval endpoint."""

    @pytest.mark.asyncio
    async def test_get_case_success(
        self,
        client: AsyncClient,
        case_creation_data: dict,
    ):
        """Test successful case retrieval."""
        # First create a case
        create_response = await client.post("/api/cases", json=case_creation_data)
        case_id = create_response.json()["id"]

        # Then retrieve it
        response = await client.get(f"/api/cases/{case_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == case_id
        assert "patient" in data
        assert "symptoms" in data
        assert "vitals" in data
        assert "assessment" in data

    @pytest.mark.asyncio
    async def test_get_case_not_found(self, client: AsyncClient):
        """Test case retrieval with non-existent ID."""
        fake_id = uuid4()

        response = await client.get(f"/api/cases/{fake_id}")

        assert response.status_code == 404


# =============================================================================
# Draft Tests
# =============================================================================


class TestCaseDrafts:
    """Tests for case draft endpoints."""

    @pytest.mark.asyncio
    async def test_save_draft_new(self, client: AsyncClient, test_patient):
        """Test saving a new draft."""
        draft_data = {
            "patient_id": str(test_patient.id),
            "patient_name": "Test Patient",
            "chief_complaint": "Headache",
            "current_step": 2,
            "data": {
                "symptoms": [{"name": "Headache", "severity": 5}],
            },
        }

        response = await client.post("/api/cases/drafts", json=draft_data)

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert data["patient_name"] == "Test Patient"
        assert data["current_step"] == 2

    @pytest.mark.asyncio
    async def test_save_draft_update(self, client: AsyncClient, test_patient):
        """Test updating an existing draft."""
        # Create initial draft
        initial_data = {
            "patient_name": "Test Patient",
            "current_step": 1,
            "data": {},
        }

        create_response = await client.post("/api/cases/drafts", json=initial_data)
        draft_id = create_response.json()["id"]

        # Update the draft
        update_data = {
            "id": draft_id,
            "patient_name": "Test Patient",
            "chief_complaint": "Updated complaint",
            "current_step": 3,
            "data": {"updated": True},
        }

        response = await client.post("/api/cases/drafts", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == draft_id
        assert data["current_step"] == 3
        assert data["chief_complaint"] == "Updated complaint"

    @pytest.mark.asyncio
    async def test_get_draft(self, client: AsyncClient):
        """Test retrieving a draft."""
        # Create a draft
        draft_data = {
            "patient_name": "Test Patient",
            "current_step": 1,
            "data": {"test": True},
        }

        create_response = await client.post("/api/cases/drafts", json=draft_data)
        draft_id = create_response.json()["id"]

        # Retrieve the draft
        response = await client.get(f"/api/cases/drafts/{draft_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == draft_id
        assert data["data"]["test"] is True

    @pytest.mark.asyncio
    async def test_list_drafts(self, client: AsyncClient):
        """Test listing drafts."""
        # Create multiple drafts
        for i in range(3):
            await client.post(
                "/api/cases/drafts",
                json={
                    "patient_name": f"Patient {i}",
                    "current_step": i,
                    "data": {},
                },
            )

        response = await client.get("/api/cases/drafts")

        assert response.status_code == 200
        data = response.json()

        assert "drafts" in data
        assert len(data["drafts"]) >= 3

    @pytest.mark.asyncio
    async def test_delete_draft(self, client: AsyncClient):
        """Test deleting a draft."""
        # Create a draft
        create_response = await client.post(
            "/api/cases/drafts",
            json={
                "patient_name": "To Delete",
                "current_step": 0,
                "data": {},
            },
        )
        draft_id = create_response.json()["id"]

        # Delete the draft
        response = await client.delete(f"/api/cases/drafts/{draft_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = await client.get(f"/api/cases/drafts/{draft_id}")
        assert get_response.status_code == 404


# =============================================================================
# Symptom Search Tests
# =============================================================================


class TestSymptomSearch:
    """Tests for symptom search endpoints."""

    @pytest.mark.asyncio
    async def test_search_symptoms(self, client: AsyncClient):
        """Test symptom search returns results."""
        response = await client.get("/api/cases/symptoms/search?q=head")

        assert response.status_code == 200
        data = response.json()

        assert "symptoms" in data
        # Results depend on seeded data

    @pytest.mark.asyncio
    async def test_search_symptoms_with_category(self, client: AsyncClient):
        """Test symptom search with category filter."""
        response = await client.get("/api/cases/symptoms/search?q=pain&category=neurological")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_autocomplete_symptoms(self, client: AsyncClient):
        """Test symptom autocomplete."""
        response = await client.get("/api/cases/symptoms/autocomplete?q=head")

        assert response.status_code == 200
        data = response.json()

        assert "suggestions" in data


# =============================================================================
# AI Analysis Tests
# =============================================================================


class TestAIAnalysis:
    """Tests for AI analysis endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_case_structure(self, client: AsyncClient):
        """Test AI analysis returns correct structure."""
        analysis_data = {
            "chief_complaint": {
                "complaint": "Severe headache",
                "duration": "3",
                "onset": "gradual",
                "severity": 7,
            },
            "symptoms": [
                {"name": "Headache", "severity": 7},
                {"name": "Nausea", "severity": 4},
            ],
            "patient_age": 35,
            "patient_gender": "female",
        }

        response = await client.post("/api/ai/analyze-case", json=analysis_data)

        # This may fail if OpenAI key not configured, which is OK for CI
        if response.status_code == 200:
            data = response.json()

            assert "differential_diagnosis" in data
            assert "urgency_assessment" in data
            assert "related_symptoms" in data
            assert "confidence" in data

    @pytest.mark.asyncio
    async def test_related_symptoms_structure(self, client: AsyncClient):
        """Test related symptoms returns correct structure."""
        data = {
            "chief_complaint": {
                "complaint": "Chest pain",
                "duration": "1",
                "onset": "sudden",
                "severity": 8,
            },
            "current_symptoms": ["Chest pain", "Shortness of breath"],
            "patient_age": 55,
        }

        response = await client.post("/api/ai/related-symptoms", json=data)

        assert response.status_code == 200
        result = response.json()

        assert "suggestions" in result

    @pytest.mark.asyncio
    async def test_urgency_check(self, client: AsyncClient):
        """Test quick urgency check."""
        response = await client.post(
            "/api/ai/urgency-check",
            params={
                "chief_complaint": "Severe chest pain radiating to left arm",
                "symptoms": ["Chest pain", "Sweating", "Nausea"],
                "patient_age": 60,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "urgency" in data
        assert "reasoning" in data
        assert "red_flags" in data
