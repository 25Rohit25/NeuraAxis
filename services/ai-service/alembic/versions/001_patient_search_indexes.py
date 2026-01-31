"""
NEURAXIS - Database Indexes Migration
Optimized indexes for patient search with 10,000+ patients
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic
revision = "001_patient_search_indexes"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create optimized indexes for patient search."""

    # ==========================================================================
    # Primary search indexes
    # ==========================================================================

    # Index on organization_id (always used for multi-tenant filtering)
    op.create_index(
        "idx_patients_organization_id",
        "patients",
        ["organization_id"],
        if_not_exists=True,
    )

    # Composite index for active patients per organization
    op.create_index(
        "idx_patients_org_active",
        "patients",
        ["organization_id", "is_deleted", "status"],
        if_not_exists=True,
    )

    # Index on MRN (unique, frequently searched)
    op.create_index(
        "idx_patients_mrn",
        "patients",
        ["mrn"],
        unique=True,
        if_not_exists=True,
    )

    # ==========================================================================
    # Text search indexes
    # ==========================================================================

    # Index on last_name (most common sort/search)
    op.create_index(
        "idx_patients_last_name",
        "patients",
        ["last_name"],
        if_not_exists=True,
    )

    # Index on first_name
    op.create_index(
        "idx_patients_first_name",
        "patients",
        ["first_name"],
        if_not_exists=True,
    )

    # Composite index for name search and sorting
    op.create_index(
        "idx_patients_name_sort",
        "patients",
        ["organization_id", "last_name", "first_name"],
        if_not_exists=True,
    )

    # GIN index for full-text search (PostgreSQL specific)
    # Using raw SQL for PostgreSQL-specific features
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_patients_search_tsvector
        ON patients
        USING GIN (
            to_tsvector('english', 
                coalesce(first_name, '') || ' ' || 
                coalesce(last_name, '') || ' ' || 
                coalesce(mrn, '') || ' ' ||
                coalesce(phone_primary, '') || ' ' ||
                coalesce(email, '')
            )
        );
    """)

    # ==========================================================================
    # Filter indexes
    # ==========================================================================

    # Index on status for filtering
    op.create_index(
        "idx_patients_status",
        "patients",
        ["status"],
        if_not_exists=True,
    )

    # Index on gender for filtering
    op.create_index(
        "idx_patients_gender",
        "patients",
        ["gender"],
        if_not_exists=True,
    )

    # Index on date_of_birth for age filtering
    op.create_index(
        "idx_patients_dob",
        "patients",
        ["date_of_birth"],
        if_not_exists=True,
    )

    # Composite index for common filter combinations
    op.create_index(
        "idx_patients_filters",
        "patients",
        ["organization_id", "status", "gender", "date_of_birth"],
        if_not_exists=True,
    )

    # ==========================================================================
    # Sorting indexes
    # ==========================================================================

    # Index on created_at (common sort, recent patients)
    op.create_index(
        "idx_patients_created_at",
        "patients",
        ["created_at"],
        if_not_exists=True,
    )

    # Composite index for org + created_at (common query pattern)
    op.create_index(
        "idx_patients_org_created",
        "patients",
        ["organization_id", "created_at"],
        if_not_exists=True,
    )

    # Index on updated_at (for last modified sorting)
    op.create_index(
        "idx_patients_updated_at",
        "patients",
        ["updated_at"],
        if_not_exists=True,
    )

    # ==========================================================================
    # Soft delete optimization
    # ==========================================================================

    # Partial index for non-deleted patients (most queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_patients_active_only
        ON patients (organization_id)
        WHERE is_deleted = false;
    """)

    # ==========================================================================
    # Phone/Email lookup indexes
    # ==========================================================================

    # Index on phone_primary for duplicate detection
    op.create_index(
        "idx_patients_phone",
        "patients",
        ["phone_primary"],
        if_not_exists=True,
    )

    # Index on email for duplicate detection
    op.create_index(
        "idx_patients_email",
        "patients",
        ["email"],
        if_not_exists=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    # ==========================================================================
    # GIN index for JSON array fields
    # ==========================================================================

    # Index for allergies (frequently filtered)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_patients_allergies_gin
        ON patients USING GIN ((allergies::jsonb))
        WHERE allergies IS NOT NULL AND allergies != '[]';
    """)

    # Index for chronic conditions (frequently filtered)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_patients_conditions_gin
        ON patients USING GIN ((chronic_conditions::jsonb))
        WHERE chronic_conditions IS NOT NULL AND chronic_conditions != '[]';
    """)


def downgrade() -> None:
    """Remove patient search indexes."""

    # PostgreSQL-specific indexes
    op.execute("DROP INDEX IF EXISTS idx_patients_search_tsvector;")
    op.execute("DROP INDEX IF EXISTS idx_patients_active_only;")
    op.execute("DROP INDEX IF EXISTS idx_patients_allergies_gin;")
    op.execute("DROP INDEX IF EXISTS idx_patients_conditions_gin;")

    # Standard indexes
    index_names = [
        "idx_patients_organization_id",
        "idx_patients_org_active",
        "idx_patients_mrn",
        "idx_patients_last_name",
        "idx_patients_first_name",
        "idx_patients_name_sort",
        "idx_patients_status",
        "idx_patients_gender",
        "idx_patients_dob",
        "idx_patients_filters",
        "idx_patients_created_at",
        "idx_patients_org_created",
        "idx_patients_updated_at",
        "idx_patients_phone",
        "idx_patients_email",
    ]

    for index_name in index_names:
        op.drop_index(index_name, table_name="patients", if_exists=True)
