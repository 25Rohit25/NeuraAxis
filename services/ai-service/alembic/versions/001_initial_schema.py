"""HIPAA-compliant medical diagnosis schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-01-29

This migration creates the complete HIPAA-compliant database schema for NEURAXIS.

Design Decisions:
- UUID primary keys for security (non-sequential)
- Column-level encryption for PHI using pgcrypto
- Row-Level Security (RLS) for multi-tenancy
- JSONB columns for flexible medical data
- Immutable audit_logs table for compliance
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables, indexes, and RLS policies."""

    # =========================================================================
    # Enable PostgreSQL Extensions
    # =========================================================================
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Create schema
    op.execute("CREATE SCHEMA IF NOT EXISTS neuraxis")

    # =========================================================================
    # Create ENUM Types
    # =========================================================================

    user_role = postgresql.ENUM(
        "super_admin",
        "admin",
        "doctor",
        "nurse",
        "radiologist",
        "technician",
        "patient",
        name="user_role",
        schema="neuraxis",
    )
    user_role.create(op.get_bind(), checkfirst=True)

    user_status = postgresql.ENUM(
        "active",
        "inactive",
        "suspended",
        "pending_verification",
        name="user_status",
        schema="neuraxis",
    )
    user_status.create(op.get_bind(), checkfirst=True)

    case_status = postgresql.ENUM(
        "draft",
        "pending_review",
        "in_progress",
        "awaiting_results",
        "completed",
        "closed",
        "archived",
        name="case_status",
        schema="neuraxis",
    )
    case_status.create(op.get_bind(), checkfirst=True)

    case_priority = postgresql.ENUM(
        "routine", "urgent", "emergent", "critical", name="case_priority", schema="neuraxis"
    )
    case_priority.create(op.get_bind(), checkfirst=True)

    diagnosis_status = postgresql.ENUM(
        "pending",
        "generated",
        "under_review",
        "confirmed",
        "rejected",
        "superseded",
        name="diagnosis_status",
        schema="neuraxis",
    )
    diagnosis_status.create(op.get_bind(), checkfirst=True)

    diagnosis_severity = postgresql.ENUM(
        "minimal",
        "mild",
        "moderate",
        "severe",
        "critical",
        "life_threatening",
        name="diagnosis_severity",
        schema="neuraxis",
    )
    diagnosis_severity.create(op.get_bind(), checkfirst=True)

    image_type = postgresql.ENUM(
        "xray",
        "ct_scan",
        "mri",
        "ultrasound",
        "mammogram",
        "pet_scan",
        "fluoroscopy",
        "dexa_scan",
        "echocardiogram",
        "other",
        name="image_type",
        schema="neuraxis",
    )
    image_type.create(op.get_bind(), checkfirst=True)

    image_status = postgresql.ENUM(
        "uploading",
        "uploaded",
        "processing",
        "analyzed",
        "failed",
        "archived",
        name="image_status",
        schema="neuraxis",
    )
    image_status.create(op.get_bind(), checkfirst=True)

    treatment_status = postgresql.ENUM(
        "draft",
        "active",
        "on_hold",
        "completed",
        "discontinued",
        "modified",
        name="treatment_status",
        schema="neuraxis",
    )
    treatment_status.create(op.get_bind(), checkfirst=True)

    audit_action = postgresql.ENUM(
        "create",
        "read",
        "update",
        "delete",
        "login",
        "logout",
        "export",
        "print",
        "share",
        "access_denied",
        name="audit_action",
        schema="neuraxis",
    )
    audit_action.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # Create Tables
    # =========================================================================

    # Organizations Table
    op.create_table(
        "organizations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255)),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(50)),
        sa.Column("fax", sa.String(50)),
        sa.Column("website", sa.String(255)),
        sa.Column("address_line1", sa.String(255)),
        sa.Column("address_line2", sa.String(255)),
        sa.Column("city", sa.String(100)),
        sa.Column("state", sa.String(100)),
        sa.Column("postal_code", sa.String(20)),
        sa.Column("country", sa.String(100), server_default="USA"),
        sa.Column("npi_number", sa.String(20)),
        sa.Column("tax_id", sa.String(20)),
        sa.Column("hipaa_compliance_date", sa.Date),
        sa.Column("settings", postgresql.JSONB, server_default="{}"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint(
            "type IN ('hospital', 'clinic', 'laboratory', 'imaging_center', 'research')",
            name="org_type_check",
        ),
        schema="neuraxis",
    )

    # Users Table
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(name="user_role", schema="neuraxis", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="user_status", schema="neuraxis", create_type=False),
            server_default="pending_verification",
            nullable=False,
        ),
        sa.Column("title", sa.String(100)),
        sa.Column("specialization", sa.String(255)),
        sa.Column("license_number", sa.String(100)),
        sa.Column("license_state", sa.String(50)),
        sa.Column("license_expiry", sa.Date),
        sa.Column("npi_number", sa.String(20)),
        sa.Column("dea_number", sa.String(20)),
        sa.Column("phone", sa.String(50)),
        sa.Column("phone_extension", sa.String(20)),
        sa.Column("mfa_enabled", sa.Boolean, server_default="false"),
        sa.Column("mfa_secret_encrypted", sa.LargeBinary),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("last_login_ip", postgresql.INET),
        sa.Column("failed_login_attempts", sa.Integer, server_default="0"),
        sa.Column("locked_until", sa.TIMESTAMP(timezone=True)),
        sa.Column("password_changed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("must_change_password", sa.Boolean, server_default="true"),
        sa.Column("preferences", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        schema="neuraxis",
    )

    # Patients Table (with encrypted PHI)
    op.create_table(
        "patients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.users.id", ondelete="SET NULL"),
        ),
        sa.Column("mrn", sa.String(50), nullable=False),
        # Encrypted PHI fields
        sa.Column("first_name_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("last_name_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("date_of_birth_encrypted", sa.LargeBinary, nullable=False),
        sa.Column("ssn_encrypted", sa.LargeBinary),
        sa.Column("gender", sa.String(20)),
        sa.Column("email_encrypted", sa.LargeBinary),
        sa.Column("phone_encrypted", sa.LargeBinary),
        sa.Column("address_encrypted", sa.LargeBinary),
        sa.Column("emergency_contact_encrypted", sa.LargeBinary),
        sa.Column("insurance_encrypted", sa.LargeBinary),
        # Non-encrypted medical data
        sa.Column("blood_type", sa.String(5)),
        sa.Column("allergies", postgresql.JSONB, server_default="[]"),
        sa.Column("chronic_conditions", postgresql.JSONB, server_default="[]"),
        sa.Column("current_medications", postgresql.JSONB, server_default="[]"),
        sa.Column("surgical_history", postgresql.JSONB, server_default="[]"),
        sa.Column("family_history", postgresql.JSONB, server_default="{}"),
        sa.Column("vitals", postgresql.JSONB, server_default="{}"),
        sa.Column("preferred_language", sa.String(10), server_default="'en'"),
        sa.Column("preferred_pharmacy", postgresql.JSONB),
        sa.Column(
            "primary_physician_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.users.id"),
        ),
        sa.Column("care_team", postgresql.JSONB, server_default="[]"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("organization_id", "mrn", name="patient_mrn_org_unique"),
        schema="neuraxis",
    )

    # Medical Cases Table
    op.create_table(
        "medical_cases",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.patients.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("case_number", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("chief_complaint", sa.Text),
        sa.Column("case_type", sa.String(100)),
        sa.Column("specialty", sa.String(100)),
        sa.Column(
            "priority",
            postgresql.ENUM(name="case_priority", schema="neuraxis", create_type=False),
            server_default="routine",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(name="case_status", schema="neuraxis", create_type=False),
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "assigned_physician_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.users.id"),
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.users.id"),
            nullable=False,
        ),
        sa.Column("admission_date", sa.Date),
        sa.Column("discharge_date", sa.Date),
        sa.Column("scheduled_date", sa.TIMESTAMP(timezone=True)),
        sa.Column("subjective", postgresql.JSONB, server_default="{}"),
        sa.Column("objective", postgresql.JSONB, server_default="{}"),
        sa.Column("assessment", postgresql.JSONB, server_default="{}"),
        sa.Column("plan", postgresql.JSONB, server_default="{}"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("tags", postgresql.ARRAY(sa.Text)),
        sa.Column("icd_codes", postgresql.ARRAY(sa.Text)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("closed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("organization_id", "case_number", name="case_number_org_unique"),
        schema="neuraxis",
    )

    # Diagnoses Table
    op.create_table(
        "diagnoses",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.medical_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.patients.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("is_ai_generated", sa.Boolean, server_default="true"),
        sa.Column("ai_model_version", sa.String(100)),
        sa.Column("ai_model_name", sa.String(255)),
        sa.Column("primary_diagnosis", sa.String(500), nullable=False),
        sa.Column("icd_code", sa.String(20)),
        sa.Column("snomed_code", sa.String(50)),
        sa.Column("confidence_score", sa.Numeric(5, 4)),
        sa.Column(
            "severity",
            postgresql.ENUM(name="diagnosis_severity", schema="neuraxis", create_type=False),
        ),
        sa.Column("reasoning", sa.Text),
        sa.Column("supporting_evidence", postgresql.JSONB, server_default="[]"),
        sa.Column("differential_diagnoses", postgresql.JSONB, server_default="[]"),
        sa.Column("risk_factors", postgresql.JSONB, server_default="[]"),
        sa.Column("contraindications", postgresql.JSONB, server_default="[]"),
        sa.Column("recommended_tests", postgresql.JSONB, server_default="[]"),
        sa.Column("recommended_treatments", postgresql.JSONB, server_default="[]"),
        sa.Column(
            "status",
            postgresql.ENUM(name="diagnosis_status", schema="neuraxis", create_type=False),
            server_default="pending",
        ),
        sa.Column(
            "reviewed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("neuraxis.users.id")
        ),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("review_notes", sa.Text),
        sa.Column("final_diagnosis", sa.String(500)),
        sa.Column("final_icd_code", sa.String(20)),
        sa.Column("processing_time_ms", sa.Integer),
        sa.Column("input_data_hash", sa.String(64)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1", name="confidence_check"
        ),
        schema="neuraxis",
    )

    # Medical Images Table
    op.create_table(
        "medical_images",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.medical_cases.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.patients.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("accession_number", sa.String(100)),
        sa.Column(
            "image_type",
            postgresql.ENUM(name="image_type", schema="neuraxis", create_type=False),
            nullable=False,
        ),
        sa.Column("body_region", sa.String(100)),
        sa.Column("laterality", sa.String(20)),
        sa.Column("view_position", sa.String(50)),
        sa.Column("dicom_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("study_instance_uid", sa.String(255)),
        sa.Column("series_instance_uid", sa.String(255)),
        sa.Column("sop_instance_uid", sa.String(255)),
        sa.Column("storage_provider", sa.String(50), server_default="'S3'"),
        sa.Column("storage_bucket", sa.String(255)),
        sa.Column("storage_key", sa.String(500)),
        sa.Column("storage_url", sa.Text),
        sa.Column("thumbnail_key", sa.String(500)),
        sa.Column("thumbnail_url", sa.Text),
        sa.Column("file_name", sa.String(255)),
        sa.Column("file_size_bytes", sa.BigInteger),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("checksum_sha256", sa.String(64)),
        sa.Column(
            "status",
            postgresql.ENUM(name="image_status", schema="neuraxis", create_type=False),
            server_default="uploading",
        ),
        sa.Column("ai_analysis", postgresql.JSONB, server_default="{}"),
        sa.Column("ai_analyzed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("ai_model_version", sa.String(100)),
        sa.Column("radiologist_notes", sa.Text),
        sa.Column("findings", sa.Text),
        sa.Column("impression", sa.Text),
        sa.Column(
            "reported_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("neuraxis.users.id")
        ),
        sa.Column("reported_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("neuraxis.users.id")
        ),
        sa.Column("study_date", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        schema="neuraxis",
    )

    # Medications Table
    op.create_table(
        "medications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column("ndc_code", sa.String(20), unique=True),
        sa.Column("rxcui", sa.String(20)),
        sa.Column("generic_name", sa.String(255), nullable=False),
        sa.Column("brand_names", postgresql.ARRAY(sa.Text)),
        sa.Column("drug_class", sa.String(255)),
        sa.Column("therapeutic_class", sa.String(255)),
        sa.Column("pharmacological_class", sa.String(255)),
        sa.Column("dosage_form", sa.String(100)),
        sa.Column("strength", sa.String(100)),
        sa.Column("route", sa.String(100)),
        sa.Column("description", sa.Text),
        sa.Column("indications", postgresql.JSONB, server_default="[]"),
        sa.Column("contraindications", postgresql.JSONB, server_default="[]"),
        sa.Column("warnings", postgresql.JSONB, server_default="[]"),
        sa.Column("interactions", postgresql.JSONB, server_default="[]"),
        sa.Column("side_effects", postgresql.JSONB, server_default="[]"),
        sa.Column("dosing_guidelines", postgresql.JSONB, server_default="{}"),
        sa.Column("schedule", sa.String(10)),
        sa.Column("requires_prescription", sa.Boolean, server_default="true"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("fda_approval_date", sa.Date),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema="neuraxis",
    )

    # Treatment Plans Table
    op.create_table(
        "treatment_plans",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.organizations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.medical_cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.patients.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "diagnosis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.diagnoses.id", ondelete="SET NULL"),
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "status",
            postgresql.ENUM(name="treatment_status", schema="neuraxis", create_type=False),
            server_default="draft",
        ),
        sa.Column("medications", postgresql.JSONB, server_default="[]"),
        sa.Column("procedures", postgresql.JSONB, server_default="[]"),
        sa.Column("lab_orders", postgresql.JSONB, server_default="[]"),
        sa.Column("imaging_orders", postgresql.JSONB, server_default="[]"),
        sa.Column("referrals", postgresql.JSONB, server_default="[]"),
        sa.Column("follow_ups", postgresql.JSONB, server_default="[]"),
        sa.Column("patient_instructions", sa.Text),
        sa.Column("dietary_restrictions", sa.Text),
        sa.Column("activity_restrictions", sa.Text),
        sa.Column("treatment_goals", postgresql.JSONB, server_default="[]"),
        sa.Column("expected_outcomes", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.users.id"),
            nullable=False,
        ),
        sa.Column(
            "approved_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("neuraxis.users.id")
        ),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("start_date", sa.Date),
        sa.Column("expected_end_date", sa.Date),
        sa.Column("actual_end_date", sa.Date),
        sa.Column("clinical_notes", sa.Text),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        schema="neuraxis",
    )

    # Audit Logs Table (Immutable)
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.users.id", ondelete="SET NULL"),
        ),
        sa.Column("user_email", sa.String(255)),
        sa.Column(
            "user_role", postgresql.ENUM(name="user_role", schema="neuraxis", create_type=False)
        ),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("neuraxis.organizations.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "action",
            postgresql.ENUM(name="audit_action", schema="neuraxis", create_type=False),
            nullable=False,
        ),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True)),
        sa.Column("resource_description", sa.String(500)),
        sa.Column("changes", postgresql.JSONB, server_default="{}"),
        sa.Column("ip_address", postgresql.INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("request_id", postgresql.UUID(as_uuid=True)),
        sa.Column("session_id", postgresql.UUID(as_uuid=True)),
        sa.Column("endpoint", sa.String(500)),
        sa.Column("http_method", sa.String(10)),
        sa.Column("request_body_hash", sa.String(64)),
        sa.Column("success", sa.Boolean, server_default="true"),
        sa.Column("error_message", sa.Text),
        sa.Column("accessed_phi", sa.Boolean, server_default="false"),
        sa.Column("phi_fields_accessed", postgresql.ARRAY(sa.Text)),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema="neuraxis",
    )

    # =========================================================================
    # Create Indexes
    # =========================================================================

    # Organizations indexes
    op.create_index(
        "idx_organizations_is_active",
        "organizations",
        ["is_active"],
        schema="neuraxis",
        postgresql_where=sa.text("is_active = true"),
    )

    # Users indexes
    op.create_index("idx_users_organization_id", "users", ["organization_id"], schema="neuraxis")
    op.create_index("idx_users_email", "users", ["email"], schema="neuraxis")
    op.create_index("idx_users_role", "users", ["role"], schema="neuraxis")
    op.create_index("idx_users_status", "users", ["status"], schema="neuraxis")
    op.create_index("idx_users_org_role", "users", ["organization_id", "role"], schema="neuraxis")

    # Patients indexes
    op.create_index(
        "idx_patients_organization_id", "patients", ["organization_id"], schema="neuraxis"
    )
    op.create_index("idx_patients_mrn", "patients", ["organization_id", "mrn"], schema="neuraxis")
    op.create_index(
        "idx_patients_is_active",
        "patients",
        ["is_active"],
        schema="neuraxis",
        postgresql_where=sa.text("is_active = true"),
    )

    # Medical Cases indexes
    op.create_index(
        "idx_cases_organization_id", "medical_cases", ["organization_id"], schema="neuraxis"
    )
    op.create_index("idx_cases_patient_id", "medical_cases", ["patient_id"], schema="neuraxis")
    op.create_index("idx_cases_status", "medical_cases", ["status"], schema="neuraxis")
    op.create_index("idx_cases_priority", "medical_cases", ["priority"], schema="neuraxis")
    op.create_index(
        "idx_cases_org_status", "medical_cases", ["organization_id", "status"], schema="neuraxis"
    )
    op.create_index(
        "idx_cases_created_at", "medical_cases", [sa.text("created_at DESC")], schema="neuraxis"
    )

    # Diagnoses indexes
    op.create_index(
        "idx_diagnoses_organization_id", "diagnoses", ["organization_id"], schema="neuraxis"
    )
    op.create_index("idx_diagnoses_case_id", "diagnoses", ["case_id"], schema="neuraxis")
    op.create_index("idx_diagnoses_patient_id", "diagnoses", ["patient_id"], schema="neuraxis")
    op.create_index("idx_diagnoses_status", "diagnoses", ["status"], schema="neuraxis")
    op.create_index("idx_diagnoses_icd_code", "diagnoses", ["icd_code"], schema="neuraxis")

    # Medical Images indexes
    op.create_index(
        "idx_images_organization_id", "medical_images", ["organization_id"], schema="neuraxis"
    )
    op.create_index("idx_images_case_id", "medical_images", ["case_id"], schema="neuraxis")
    op.create_index("idx_images_patient_id", "medical_images", ["patient_id"], schema="neuraxis")
    op.create_index("idx_images_type", "medical_images", ["image_type"], schema="neuraxis")
    op.create_index("idx_images_status", "medical_images", ["status"], schema="neuraxis")

    # Medications indexes
    op.create_index(
        "idx_medications_generic_name", "medications", ["generic_name"], schema="neuraxis"
    )
    op.create_index("idx_medications_ndc", "medications", ["ndc_code"], schema="neuraxis")
    op.create_index("idx_medications_drug_class", "medications", ["drug_class"], schema="neuraxis")

    # Treatment Plans indexes
    op.create_index(
        "idx_treatment_plans_organization_id",
        "treatment_plans",
        ["organization_id"],
        schema="neuraxis",
    )
    op.create_index(
        "idx_treatment_plans_case_id", "treatment_plans", ["case_id"], schema="neuraxis"
    )
    op.create_index(
        "idx_treatment_plans_patient_id", "treatment_plans", ["patient_id"], schema="neuraxis"
    )
    op.create_index("idx_treatment_plans_status", "treatment_plans", ["status"], schema="neuraxis")

    # Audit Logs indexes
    op.create_index("idx_audit_user_id", "audit_logs", ["user_id"], schema="neuraxis")
    op.create_index(
        "idx_audit_organization_id", "audit_logs", ["organization_id"], schema="neuraxis"
    )
    op.create_index("idx_audit_action", "audit_logs", ["action"], schema="neuraxis")
    op.create_index(
        "idx_audit_resource", "audit_logs", ["resource_type", "resource_id"], schema="neuraxis"
    )
    op.create_index(
        "idx_audit_created_at", "audit_logs", [sa.text("created_at DESC")], schema="neuraxis"
    )
    op.create_index(
        "idx_audit_accessed_phi",
        "audit_logs",
        ["accessed_phi"],
        schema="neuraxis",
        postgresql_where=sa.text("accessed_phi = true"),
    )

    # =========================================================================
    # Create helper functions
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION neuraxis.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # =========================================================================
    # Create triggers for updated_at
    # =========================================================================

    tables_with_updated_at = [
        "organizations",
        "users",
        "patients",
        "medical_cases",
        "diagnoses",
        "medical_images",
        "medications",
        "treatment_plans",
    ]

    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON neuraxis.{table}
            FOR EACH ROW EXECUTE FUNCTION neuraxis.update_updated_at_column();
        """)

    # =========================================================================
    # Enable Row Level Security
    # =========================================================================

    rls_tables = [
        "organizations",
        "users",
        "patients",
        "medical_cases",
        "diagnoses",
        "medical_images",
        "treatment_plans",
        "audit_logs",
    ]

    for table in rls_tables:
        op.execute(f"ALTER TABLE neuraxis.{table} ENABLE ROW LEVEL SECURITY;")

    # Make audit_logs append-only
    op.execute("REVOKE UPDATE, DELETE ON neuraxis.audit_logs FROM PUBLIC;")


def downgrade() -> None:
    """Drop all tables and types."""

    # Drop tables in reverse order of dependencies
    tables = [
        "audit_logs",
        "treatment_plans",
        "medications",
        "medical_images",
        "diagnoses",
        "medical_cases",
        "patients",
        "users",
        "organizations",
    ]

    for table in tables:
        op.drop_table(table, schema="neuraxis")

    # Drop ENUMs
    enums = [
        "audit_action",
        "treatment_status",
        "image_status",
        "image_type",
        "diagnosis_severity",
        "diagnosis_status",
        "case_priority",
        "case_status",
        "user_status",
        "user_role",
    ]

    for enum in enums:
        op.execute(f"DROP TYPE IF EXISTS neuraxis.{enum}")

    # Drop helper function
    op.execute("DROP FUNCTION IF EXISTS neuraxis.update_updated_at_column()")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS neuraxis CASCADE")
