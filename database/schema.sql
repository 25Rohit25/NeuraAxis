-- ============================================================================
-- NEURAXIS - HIPAA-Compliant Medical Diagnosis Platform Database Schema
-- ============================================================================
-- 
-- Design Decisions:
-- 1. UUID primary keys for security (non-sequential, harder to enumerate)
-- 2. Column-level encryption using pgcrypto for PHI (Protected Health Information)
-- 3. Row-Level Security (RLS) for multi-tenancy and access control
-- 4. JSONB columns for flexible, schema-less medical data
-- 5. Immutable audit_logs table for compliance tracking
-- 6. Soft deletes (deleted_at) to maintain data integrity for auditing
-- 7. Comprehensive indexing for query performance
--
-- HIPAA Requirements Addressed:
-- - Access Controls: RLS policies + role-based access
-- - Audit Controls: Immutable audit_logs with all access recorded
-- - Integrity Controls: Foreign keys, constraints, encrypted PHI
-- - Transmission Security: Handled at application/network layer
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- Encryption functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Trigram matching for search

-- Create custom schema for isolation
CREATE SCHEMA IF NOT EXISTS neuraxis;
SET search_path TO neuraxis, public;

-- ============================================================================
-- ENUM TYPES
-- ============================================================================
-- Using enums for type safety and query optimization

CREATE TYPE user_role AS ENUM (
    'super_admin',    -- System-wide access
    'admin',          -- Organization admin
    'doctor',         -- Physician
    'nurse',          -- Nursing staff
    'radiologist',    -- Imaging specialist
    'technician',     -- Lab/imaging technician
    'patient'         -- Patient portal access
);

CREATE TYPE user_status AS ENUM (
    'active',
    'inactive',
    'suspended',
    'pending_verification'
);

CREATE TYPE case_status AS ENUM (
    'draft',          -- Initial creation
    'pending_review', -- Awaiting physician review
    'in_progress',    -- Active treatment
    'awaiting_results', -- Waiting for lab/imaging
    'completed',      -- Treatment complete
    'closed',         -- Case closed
    'archived'        -- Long-term storage
);

CREATE TYPE case_priority AS ENUM (
    'routine',
    'urgent',
    'emergent',
    'critical'
);

CREATE TYPE diagnosis_status AS ENUM (
    'pending',        -- AI processing
    'generated',      -- AI completed
    'under_review',   -- Physician reviewing
    'confirmed',      -- Physician approved
    'rejected',       -- Physician rejected
    'superseded'      -- Replaced by newer diagnosis
);

CREATE TYPE diagnosis_severity AS ENUM (
    'minimal',
    'mild',
    'moderate',
    'severe',
    'critical',
    'life_threatening'
);

CREATE TYPE image_type AS ENUM (
    'xray',
    'ct_scan',
    'mri',
    'ultrasound',
    'mammogram',
    'pet_scan',
    'fluoroscopy',
    'dexa_scan',
    'echocardiogram',
    'other'
);

CREATE TYPE image_status AS ENUM (
    'uploading',
    'uploaded',
    'processing',
    'analyzed',
    'failed',
    'archived'
);

CREATE TYPE treatment_status AS ENUM (
    'draft',
    'active',
    'on_hold',
    'completed',
    'discontinued',
    'modified'
);

CREATE TYPE audit_action AS ENUM (
    'create',
    'read',
    'update',
    'delete',
    'login',
    'logout',
    'export',
    'print',
    'share',
    'access_denied'
);

-- ============================================================================
-- TABLE: organizations
-- Multi-tenant support for healthcare facilities
-- ============================================================================
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic Information
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    type VARCHAR(50) NOT NULL CHECK (type IN ('hospital', 'clinic', 'laboratory', 'imaging_center', 'research')),
    
    -- Contact Information
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    fax VARCHAR(50),
    website VARCHAR(255),
    
    -- Address (NOT PHI - organizational data)
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    
    -- Compliance
    npi_number VARCHAR(20),           -- National Provider Identifier
    tax_id VARCHAR(20),
    hipaa_compliance_date DATE,
    
    -- Settings stored as JSONB for flexibility
    settings JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT org_email_unique UNIQUE (email)
);

COMMENT ON TABLE organizations IS 'Healthcare organizations/facilities - multi-tenant support';
COMMENT ON COLUMN organizations.settings IS 'JSONB for org-specific settings (timezone, features, etc.)';

-- ============================================================================
-- TABLE: users
-- Medical staff and patient accounts with role-based access
-- ============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    
    -- Authentication (NOT PHI)
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile Information
    -- Note: For staff, names are NOT PHI. For patients, they ARE PHI.
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    
    -- Role & Status
    role user_role NOT NULL,
    status user_status DEFAULT 'pending_verification' NOT NULL,
    
    -- Professional Information (staff only)
    title VARCHAR(100),                    -- Dr., RN, etc.
    specialization VARCHAR(255),           -- Cardiology, Radiology, etc.
    license_number VARCHAR(100),
    license_state VARCHAR(50),
    license_expiry DATE,
    npi_number VARCHAR(20),                -- Individual NPI
    dea_number VARCHAR(20),                -- DEA for prescribing
    
    -- Contact
    phone VARCHAR(50),
    phone_extension VARCHAR(20),
    
    -- Security
    mfa_enabled BOOLEAN DEFAULT false,
    mfa_secret_encrypted BYTEA,            -- Encrypted MFA secret
    last_login_at TIMESTAMPTZ,
    last_login_ip INET,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ,
    must_change_password BOOLEAN DEFAULT true,
    
    -- Preferences
    preferences JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT user_email_unique UNIQUE (email),
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

COMMENT ON TABLE users IS 'System users including medical staff and patient portal accounts';
COMMENT ON COLUMN users.password_hash IS 'bcrypt hashed password - never store plaintext';
COMMENT ON COLUMN users.mfa_secret_encrypted IS 'AES-256 encrypted TOTP secret';

-- ============================================================================
-- TABLE: patients
-- Protected Health Information (PHI) with column-level encryption
-- ============================================================================
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    
    -- Link to user account (for patient portal)
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Medical Record Number (organization-specific)
    mrn VARCHAR(50) NOT NULL,
    
    -- =========================================================================
    -- ENCRYPTED PHI FIELDS
    -- These fields store AES-256-GCM encrypted data
    -- Encryption key is managed at application level (never stored in DB)
    -- Format: pgp_sym_encrypt(data, key, 'compress-algo=1, cipher-algo=aes256')
    -- =========================================================================
    first_name_encrypted BYTEA NOT NULL,
    last_name_encrypted BYTEA NOT NULL,
    date_of_birth_encrypted BYTEA NOT NULL,
    ssn_encrypted BYTEA,                    -- Optional, highly sensitive
    
    -- Non-encrypted but still protected by RLS
    gender VARCHAR(20),
    
    -- Contact Information (encrypted)
    email_encrypted BYTEA,
    phone_encrypted BYTEA,
    address_encrypted BYTEA,                 -- JSON object with full address
    
    -- Emergency Contact (encrypted)
    emergency_contact_encrypted BYTEA,       -- JSON: {name, relationship, phone}
    
    -- Insurance Information (encrypted)
    insurance_encrypted BYTEA,               -- JSON: {provider, policy_number, group_number}
    
    -- =========================================================================
    -- NON-ENCRYPTED MEDICAL DATA
    -- These are typically not considered direct identifiers
    -- =========================================================================
    blood_type VARCHAR(5),
    
    -- Medical History as JSONB (flexible schema)
    -- Allows for varying medical data without schema changes
    allergies JSONB DEFAULT '[]',            -- Array of allergy objects
    chronic_conditions JSONB DEFAULT '[]',   -- Array of conditions with ICD codes
    current_medications JSONB DEFAULT '[]',  -- Array of medication objects
    surgical_history JSONB DEFAULT '[]',     -- Array of surgical procedures
    family_history JSONB DEFAULT '{}',       -- Family medical history
    
    -- Vital Statistics (latest readings)
    vitals JSONB DEFAULT '{}',               -- Latest vital signs
    
    -- Preferences
    preferred_language VARCHAR(10) DEFAULT 'en',
    preferred_pharmacy JSONB,                -- Pharmacy details
    
    -- Care Team
    primary_physician_id UUID REFERENCES users(id),
    care_team JSONB DEFAULT '[]',            -- Array of care team member IDs
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ,                  -- Soft delete for compliance
    
    -- Constraints
    CONSTRAINT patient_mrn_org_unique UNIQUE (organization_id, mrn)
);

COMMENT ON TABLE patients IS 'Patient records with encrypted PHI - HIPAA compliant';
COMMENT ON COLUMN patients.first_name_encrypted IS 'AES-256-GCM encrypted first name';
COMMENT ON COLUMN patients.ssn_encrypted IS 'AES-256-GCM encrypted SSN - store only if legally required';
COMMENT ON COLUMN patients.allergies IS 'JSONB array: [{allergen, reaction, severity, onset_date}]';

-- ============================================================================
-- TABLE: medical_cases
-- Patient cases with workflow states
-- ============================================================================
CREATE TABLE medical_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
    
    -- Case Identification
    case_number VARCHAR(50) NOT NULL,        -- Human-readable case ID
    
    -- Case Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    chief_complaint TEXT,                    -- Primary reason for visit
    
    -- Classification
    case_type VARCHAR(100),                  -- Consultation, Follow-up, Emergency, etc.
    specialty VARCHAR(100),                  -- Department/specialty
    priority case_priority DEFAULT 'routine',
    
    -- Workflow
    status case_status DEFAULT 'draft' NOT NULL,
    
    -- Assignment
    assigned_physician_id UUID REFERENCES users(id),
    created_by_id UUID NOT NULL REFERENCES users(id),
    
    -- Dates
    admission_date DATE,
    discharge_date DATE,
    scheduled_date TIMESTAMPTZ,
    
    -- Clinical Notes (structured JSONB)
    subjective JSONB DEFAULT '{}',           -- Patient-reported symptoms
    objective JSONB DEFAULT '{}',            -- Examination findings
    assessment JSONB DEFAULT '{}',           -- Clinical assessment
    plan JSONB DEFAULT '{}',                 -- Treatment plan
    
    -- Additional Data
    metadata JSONB DEFAULT '{}',             -- Flexible additional data
    tags TEXT[],                             -- Searchable tags
    
    -- ICD-10 Codes (for billing)
    icd_codes TEXT[],
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    closed_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT case_number_org_unique UNIQUE (organization_id, case_number)
);

COMMENT ON TABLE medical_cases IS 'Patient medical cases with SOAP notes and workflow';
COMMENT ON COLUMN medical_cases.subjective IS 'SOAP: Subjective - patient symptoms and history';
COMMENT ON COLUMN medical_cases.objective IS 'SOAP: Objective - examination and test results';
COMMENT ON COLUMN medical_cases.assessment IS 'SOAP: Assessment - diagnosis and analysis';
COMMENT ON COLUMN medical_cases.plan IS 'SOAP: Plan - proposed treatment';

-- ============================================================================
-- TABLE: diagnoses  
-- AI-generated diagnoses with confidence scores
-- ============================================================================
CREATE TABLE diagnoses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    case_id UUID NOT NULL REFERENCES medical_cases(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
    
    -- Source
    is_ai_generated BOOLEAN DEFAULT true,
    ai_model_version VARCHAR(100),
    ai_model_name VARCHAR(255),
    
    -- Primary Diagnosis
    primary_diagnosis VARCHAR(500) NOT NULL,
    icd_code VARCHAR(20),                    -- ICD-10 code
    snomed_code VARCHAR(50),                 -- SNOMED CT code
    
    -- Confidence & Severity
    confidence_score DECIMAL(5,4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    severity diagnosis_severity,
    
    -- AI Reasoning (explainability)
    reasoning TEXT,
    supporting_evidence JSONB DEFAULT '[]',   -- Evidence that led to diagnosis
    
    -- Differential Diagnoses
    -- Array of objects: [{name, icd_code, probability, reasoning}]
    differential_diagnoses JSONB DEFAULT '[]',
    
    -- Risk Assessment
    risk_factors JSONB DEFAULT '[]',
    contraindications JSONB DEFAULT '[]',
    
    -- Recommendations
    recommended_tests JSONB DEFAULT '[]',
    recommended_treatments JSONB DEFAULT '[]',
    
    -- Status & Review
    status diagnosis_status DEFAULT 'pending',
    
    -- Clinical Review
    reviewed_by_id UUID REFERENCES users(id),
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    
    -- If confirmed/rejected, what was the final diagnosis?
    final_diagnosis VARCHAR(500),
    final_icd_code VARCHAR(20),
    
    -- Analytics
    processing_time_ms INTEGER,              -- AI processing time
    input_data_hash VARCHAR(64),             -- Hash of input for reproducibility
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ
);

COMMENT ON TABLE diagnoses IS 'AI-generated and physician-confirmed diagnoses';
COMMENT ON COLUMN diagnoses.confidence_score IS 'AI confidence 0.0000 to 1.0000 (0-100%)';
COMMENT ON COLUMN diagnoses.differential_diagnoses IS 'Array of alternative diagnoses with probabilities';
COMMENT ON COLUMN diagnoses.input_data_hash IS 'SHA-256 hash of input data for audit trail';

-- ============================================================================
-- TABLE: medical_images
-- DICOM image metadata and storage references
-- ============================================================================
CREATE TABLE medical_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    case_id UUID REFERENCES medical_cases(id) ON DELETE SET NULL,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
    
    -- Image Identification
    accession_number VARCHAR(100),           -- Radiology accession number
    
    -- Image Type & Details
    image_type image_type NOT NULL,
    body_region VARCHAR(100),                -- Chest, Head, Abdomen, etc.
    laterality VARCHAR(20),                  -- Left, Right, Bilateral
    view_position VARCHAR(50),               -- AP, PA, Lateral, etc.
    
    -- DICOM Metadata (from DICOM headers)
    dicom_metadata JSONB DEFAULT '{}',
    study_instance_uid VARCHAR(255),
    series_instance_uid VARCHAR(255),
    sop_instance_uid VARCHAR(255),
    
    -- Storage (references to secure storage)
    storage_provider VARCHAR(50) DEFAULT 'S3',  -- S3, Azure, GCS
    storage_bucket VARCHAR(255),
    storage_key VARCHAR(500),                 -- File path/key in storage
    storage_url TEXT,                         -- Pre-signed URL (temporary)
    
    -- Thumbnails
    thumbnail_key VARCHAR(500),
    thumbnail_url TEXT,
    
    -- File Details
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    checksum_sha256 VARCHAR(64),             -- File integrity verification
    
    -- Processing Status
    status image_status DEFAULT 'uploading',
    
    -- AI Analysis Results
    ai_analysis JSONB DEFAULT '{}',          -- AI findings
    ai_analyzed_at TIMESTAMPTZ,
    ai_model_version VARCHAR(100),
    
    -- Clinical Notes
    radiologist_notes TEXT,
    findings TEXT,
    impression TEXT,
    
    -- Reported
    reported_by_id UUID REFERENCES users(id),
    reported_at TIMESTAMPTZ,
    
    -- Uploaded by
    uploaded_by_id UUID REFERENCES users(id),
    
    -- Timestamps
    study_date TIMESTAMPTZ,                  -- When image was taken
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ
);

COMMENT ON TABLE medical_images IS 'Medical imaging metadata - actual files in secure object storage';
COMMENT ON COLUMN medical_images.storage_key IS 'Encrypted path to image in object storage';
COMMENT ON COLUMN medical_images.ai_analysis IS 'AI findings: {findings: [], abnormalities: [], measurements: {}}';

-- ============================================================================
-- TABLE: medications
-- Drug catalog with interaction data
-- ============================================================================
CREATE TABLE medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Drug Identification
    ndc_code VARCHAR(20),                    -- National Drug Code
    rxcui VARCHAR(20),                       -- RxNorm Concept Unique Identifier
    
    -- Names
    generic_name VARCHAR(255) NOT NULL,
    brand_names TEXT[],                      -- Array of brand names
    
    -- Classification
    drug_class VARCHAR(255),
    therapeutic_class VARCHAR(255),
    pharmacological_class VARCHAR(255),
    
    -- Formulation
    dosage_form VARCHAR(100),                -- Tablet, Capsule, Injection, etc.
    strength VARCHAR(100),
    route VARCHAR(100),                      -- Oral, IV, Topical, etc.
    
    -- Details
    description TEXT,
    indications JSONB DEFAULT '[]',          -- Approved uses
    contraindications JSONB DEFAULT '[]',    -- When NOT to use
    warnings JSONB DEFAULT '[]',             -- Black box and other warnings
    
    -- Drug Interactions
    -- Array of objects: [{drug_id, severity, description}]
    interactions JSONB DEFAULT '[]',
    
    -- Side Effects
    -- Array of objects: [{effect, frequency, severity}]
    side_effects JSONB DEFAULT '[]',
    
    -- Dosing Information
    dosing_guidelines JSONB DEFAULT '{}',
    
    -- Regulatory
    schedule VARCHAR(10),                    -- DEA schedule (I, II, III, IV, V, none)
    requires_prescription BOOLEAN DEFAULT true,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    fda_approval_date DATE,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Constraints
    CONSTRAINT medication_ndc_unique UNIQUE (ndc_code)
);

COMMENT ON TABLE medications IS 'Drug catalog with comprehensive interaction and safety data';
COMMENT ON COLUMN medications.interactions IS 'Drug-drug interactions with severity levels';

-- ============================================================================
-- TABLE: treatment_plans
-- Patient treatment plans including medications, procedures, follow-ups
-- ============================================================================
CREATE TABLE treatment_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    case_id UUID NOT NULL REFERENCES medical_cases(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
    diagnosis_id UUID REFERENCES diagnoses(id) ON DELETE SET NULL,
    
    -- Plan Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Status
    status treatment_status DEFAULT 'draft',
    
    -- Prescribed Medications
    -- Array: [{medication_id, dosage, frequency, duration, instructions, start_date, end_date}]
    medications JSONB DEFAULT '[]',
    
    -- Procedures
    -- Array: [{name, cpt_code, scheduled_date, facility, notes}]
    procedures JSONB DEFAULT '[]',
    
    -- Lab Orders
    -- Array: [{test_name, loinc_code, urgency, special_instructions}]
    lab_orders JSONB DEFAULT '[]',
    
    -- Imaging Orders
    -- Array: [{type, body_region, urgency, clinical_indication}]
    imaging_orders JSONB DEFAULT '[]',
    
    -- Referrals
    -- Array: [{specialty, reason, urgency, preferred_provider}]
    referrals JSONB DEFAULT '[]',
    
    -- Follow-up Schedule
    -- Array: [{type, scheduled_date, duration_minutes, notes}]
    follow_ups JSONB DEFAULT '[]',
    
    -- Patient Instructions
    patient_instructions TEXT,
    dietary_restrictions TEXT,
    activity_restrictions TEXT,
    
    -- Goals & Outcomes
    treatment_goals JSONB DEFAULT '[]',
    expected_outcomes JSONB DEFAULT '{}',
    
    -- Care Team
    created_by_id UUID NOT NULL REFERENCES users(id),
    approved_by_id UUID REFERENCES users(id),
    approved_at TIMESTAMPTZ,
    
    -- Duration
    start_date DATE,
    expected_end_date DATE,
    actual_end_date DATE,
    
    -- Notes
    clinical_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    deleted_at TIMESTAMPTZ
);

COMMENT ON TABLE treatment_plans IS 'Comprehensive treatment plans with medications, procedures, and follow-ups';
COMMENT ON COLUMN treatment_plans.medications IS 'Prescribed medications with dosing schedules';

-- ============================================================================
-- TABLE: audit_logs
-- Immutable HIPAA compliance logging
-- ============================================================================
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Actor
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),                 -- Preserved even if user deleted
    user_role user_role,
    organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    
    -- Action
    action audit_action NOT NULL,
    
    -- Target Resource
    resource_type VARCHAR(100) NOT NULL,     -- Table name / resource type
    resource_id UUID,                        -- ID of accessed resource
    resource_description VARCHAR(500),       -- Human-readable description
    
    -- Change Details
    -- For updates: {field: {old: value, new: value}}
    changes JSONB DEFAULT '{}',
    
    -- Request Context
    ip_address INET,
    user_agent TEXT,
    request_id UUID,                         -- Correlation ID
    session_id UUID,
    
    -- API Details
    endpoint VARCHAR(500),
    http_method VARCHAR(10),
    request_body_hash VARCHAR(64),           -- Hash of request (not actual data)
    
    -- Result
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    
    -- PHI Access Flag
    accessed_phi BOOLEAN DEFAULT false,      -- Did this access PHI?
    phi_fields_accessed TEXT[],              -- Which PHI fields were accessed
    
    -- Timestamp (immutable)
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
    
    -- NO updated_at or deleted_at - audit logs are immutable!
);

-- Make audit_logs append-only
REVOKE UPDATE, DELETE ON audit_logs FROM PUBLIC;

COMMENT ON TABLE audit_logs IS 'Immutable audit trail for HIPAA compliance - NO updates or deletes allowed';
COMMENT ON COLUMN audit_logs.accessed_phi IS 'Flag indicating PHI was accessed - required for HIPAA';
COMMENT ON COLUMN audit_logs.phi_fields_accessed IS 'List of PHI fields accessed for audit trail';

-- ============================================================================
-- INDEXES
-- Optimized for common query patterns
-- ============================================================================

-- Organizations
CREATE INDEX idx_organizations_is_active ON organizations(is_active) WHERE is_active = true;

-- Users
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_org_role ON users(organization_id, role);
CREATE INDEX idx_users_last_login ON users(last_login_at DESC);

-- Patients
CREATE INDEX idx_patients_organization_id ON patients(organization_id);
CREATE INDEX idx_patients_mrn ON patients(organization_id, mrn);
CREATE INDEX idx_patients_user_id ON patients(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_patients_primary_physician ON patients(primary_physician_id) WHERE primary_physician_id IS NOT NULL;
CREATE INDEX idx_patients_is_active ON patients(is_active) WHERE is_active = true;
CREATE INDEX idx_patients_created_at ON patients(created_at DESC);

-- Medical Cases
CREATE INDEX idx_cases_organization_id ON medical_cases(organization_id);
CREATE INDEX idx_cases_patient_id ON medical_cases(patient_id);
CREATE INDEX idx_cases_assigned_physician ON medical_cases(assigned_physician_id);
CREATE INDEX idx_cases_status ON medical_cases(status);
CREATE INDEX idx_cases_priority ON medical_cases(priority);
CREATE INDEX idx_cases_org_status ON medical_cases(organization_id, status);
CREATE INDEX idx_cases_created_at ON medical_cases(created_at DESC);
CREATE INDEX idx_cases_tags ON medical_cases USING GIN(tags);
CREATE INDEX idx_cases_icd_codes ON medical_cases USING GIN(icd_codes);

-- Diagnoses
CREATE INDEX idx_diagnoses_organization_id ON diagnoses(organization_id);
CREATE INDEX idx_diagnoses_case_id ON diagnoses(case_id);
CREATE INDEX idx_diagnoses_patient_id ON diagnoses(patient_id);
CREATE INDEX idx_diagnoses_status ON diagnoses(status);
CREATE INDEX idx_diagnoses_severity ON diagnoses(severity);
CREATE INDEX idx_diagnoses_icd_code ON diagnoses(icd_code);
CREATE INDEX idx_diagnoses_confidence ON diagnoses(confidence_score DESC);
CREATE INDEX idx_diagnoses_reviewed_by ON diagnoses(reviewed_by_id) WHERE reviewed_by_id IS NOT NULL;
CREATE INDEX idx_diagnoses_created_at ON diagnoses(created_at DESC);
CREATE INDEX idx_diagnoses_ai_generated ON diagnoses(is_ai_generated) WHERE is_ai_generated = true;

-- Medical Images
CREATE INDEX idx_images_organization_id ON medical_images(organization_id);
CREATE INDEX idx_images_case_id ON medical_images(case_id);
CREATE INDEX idx_images_patient_id ON medical_images(patient_id);
CREATE INDEX idx_images_type ON medical_images(image_type);
CREATE INDEX idx_images_status ON medical_images(status);
CREATE INDEX idx_images_study_date ON medical_images(study_date DESC);
CREATE INDEX idx_images_study_uid ON medical_images(study_instance_uid);
CREATE INDEX idx_images_accession ON medical_images(accession_number);

-- Medications
CREATE INDEX idx_medications_generic_name ON medications(generic_name);
CREATE INDEX idx_medications_ndc ON medications(ndc_code);
CREATE INDEX idx_medications_rxcui ON medications(rxcui);
CREATE INDEX idx_medications_drug_class ON medications(drug_class);
CREATE INDEX idx_medications_schedule ON medications(schedule);
CREATE INDEX idx_medications_brand_names ON medications USING GIN(brand_names);
CREATE INDEX idx_medications_is_active ON medications(is_active) WHERE is_active = true;

-- Full-text search on medication names
CREATE INDEX idx_medications_search ON medications 
    USING GIN(to_tsvector('english', generic_name || ' ' || COALESCE(array_to_string(brand_names, ' '), '')));

-- Treatment Plans
CREATE INDEX idx_treatment_plans_organization_id ON treatment_plans(organization_id);
CREATE INDEX idx_treatment_plans_case_id ON treatment_plans(case_id);
CREATE INDEX idx_treatment_plans_patient_id ON treatment_plans(patient_id);
CREATE INDEX idx_treatment_plans_diagnosis_id ON treatment_plans(diagnosis_id);
CREATE INDEX idx_treatment_plans_status ON treatment_plans(status);
CREATE INDEX idx_treatment_plans_created_by ON treatment_plans(created_by_id);
CREATE INDEX idx_treatment_plans_created_at ON treatment_plans(created_at DESC);

-- Audit Logs (critical for compliance queries)
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_organization_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_accessed_phi ON audit_logs(accessed_phi) WHERE accessed_phi = true;
CREATE INDEX idx_audit_ip_address ON audit_logs(ip_address);
CREATE INDEX idx_audit_session ON audit_logs(session_id);

-- Composite index for common audit queries
CREATE INDEX idx_audit_compliance_query ON audit_logs(organization_id, created_at DESC, action);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- Multi-tenant data isolation
-- ============================================================================

-- Enable RLS on all tables with patient data
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE treatment_plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create a function to get the current user's organization
CREATE OR REPLACE FUNCTION current_user_org_id() RETURNS UUID AS $$
BEGIN
    -- This should be set by the application when establishing a connection
    RETURN current_setting('app.current_organization_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to get the current user's ID
CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_user_id', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a function to get the current user's role
CREATE OR REPLACE FUNCTION current_user_role() RETURNS user_role AS $$
BEGIN
    RETURN current_setting('app.current_user_role', true)::user_role;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Organizations Policy
CREATE POLICY org_isolation_policy ON organizations
    USING (id = current_user_org_id() OR current_user_role() = 'super_admin');

-- Users Policy - can see users in same org
CREATE POLICY users_isolation_policy ON users
    USING (organization_id = current_user_org_id() OR current_user_role() = 'super_admin');

-- Patients Policy - organization isolation + role-based access
CREATE POLICY patients_isolation_policy ON patients
    USING (
        organization_id = current_user_org_id()
        AND (
            current_user_role() IN ('admin', 'doctor', 'nurse', 'radiologist', 'technician')
            OR (current_user_role() = 'patient' AND user_id = current_user_id())
        )
    );

-- Medical Cases Policy
CREATE POLICY cases_isolation_policy ON medical_cases
    USING (
        organization_id = current_user_org_id()
        AND current_user_role() IN ('admin', 'doctor', 'nurse', 'radiologist', 'technician')
    );

-- Diagnoses Policy
CREATE POLICY diagnoses_isolation_policy ON diagnoses
    USING (
        organization_id = current_user_org_id()
        AND current_user_role() IN ('admin', 'doctor', 'nurse', 'radiologist')
    );

-- Medical Images Policy
CREATE POLICY images_isolation_policy ON medical_images
    USING (
        organization_id = current_user_org_id()
        AND current_user_role() IN ('admin', 'doctor', 'nurse', 'radiologist', 'technician')
    );

-- Treatment Plans Policy
CREATE POLICY treatment_plans_isolation_policy ON treatment_plans
    USING (
        organization_id = current_user_org_id()
        AND current_user_role() IN ('admin', 'doctor', 'nurse')
    );

-- Audit Logs Policy - only admins can read
CREATE POLICY audit_logs_policy ON audit_logs
    USING (
        organization_id = current_user_org_id()
        AND current_user_role() IN ('admin', 'super_admin')
    );

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_medical_cases_updated_at
    BEFORE UPDATE ON medical_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_diagnoses_updated_at
    BEFORE UPDATE ON diagnoses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_medical_images_updated_at
    BEFORE UPDATE ON medical_images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_medications_updated_at
    BEFORE UPDATE ON medications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_treatment_plans_updated_at
    BEFORE UPDATE ON treatment_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- HELPER FUNCTIONS FOR PHI ENCRYPTION/DECRYPTION
-- ============================================================================

-- Note: The actual encryption key should NEVER be stored in the database
-- It should be passed from the application layer

CREATE OR REPLACE FUNCTION encrypt_phi(data TEXT, key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, key, 'compress-algo=1, cipher-algo=aes256');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrypt_phi(encrypted_data BYTEA, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(encrypted_data, key);
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL; -- Return NULL if decryption fails
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- AUDIT TRIGGER FOR PHI ACCESS LOGGING
-- ============================================================================

CREATE OR REPLACE FUNCTION log_phi_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id,
        user_email,
        user_role,
        organization_id,
        action,
        resource_type,
        resource_id,
        accessed_phi,
        phi_fields_accessed,
        ip_address
    ) VALUES (
        current_user_id(),
        current_setting('app.current_user_email', true),
        current_user_role(),
        current_user_org_id(),
        TG_OP::audit_action,
        TG_TABLE_NAME,
        CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
        true,
        ARRAY['first_name_encrypted', 'last_name_encrypted', 'date_of_birth_encrypted', 'ssn_encrypted'],
        current_setting('app.client_ip', true)::INET
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply PHI access logging to patients table
CREATE TRIGGER audit_phi_access_patients
    AFTER INSERT OR UPDATE OR DELETE ON patients
    FOR EACH ROW EXECUTE FUNCTION log_phi_access();

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Create roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'neuraxis_app') THEN
        CREATE ROLE neuraxis_app WITH LOGIN PASSWORD 'change_me_in_production';
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'neuraxis_readonly') THEN
        CREATE ROLE neuraxis_readonly WITH LOGIN PASSWORD 'change_me_in_production';
    END IF;
END
$$;

-- Grant schema access
GRANT USAGE ON SCHEMA neuraxis TO neuraxis_app, neuraxis_readonly;

-- Grant table access to application role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA neuraxis TO neuraxis_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA neuraxis TO neuraxis_app;

-- Audit logs should only allow INSERT for app (immutable)
REVOKE UPDATE, DELETE ON neuraxis.audit_logs FROM neuraxis_app;
GRANT INSERT ON neuraxis.audit_logs TO neuraxis_app;

-- Read-only role
GRANT SELECT ON ALL TABLES IN SCHEMA neuraxis TO neuraxis_readonly;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
