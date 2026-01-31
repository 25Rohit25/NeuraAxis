# NEURAXIS Database Schema

> HIPAA-Compliant PostgreSQL Database for Medical Diagnosis Platform

## Overview

This directory contains the complete database schema for NEURAXIS, designed with HIPAA compliance as a core requirement.

## Files

| File                   | Description                                           |
| ---------------------- | ----------------------------------------------------- |
| `schema.sql`           | Complete PostgreSQL DDL with all tables, indexes, RLS |
| `prisma/schema.prisma` | Prisma ORM schema for TypeScript integration          |
| `diagram.md`           | Entity-Relationship diagram in Mermaid format         |

## HIPAA Compliance Features

### 1. Access Controls

- **Row-Level Security (RLS)**: Multi-tenant data isolation
- **Role-Based Access**: Granular permissions per user role
- **Session-Based Context**: Organization/user context set per connection

### 2. Audit Controls

- **Immutable Audit Logs**: All access recorded, no updates/deletes allowed
- **PHI Access Tracking**: Flag and log all PHI field access
- **Request Tracing**: IP address, user agent, session tracking

### 3. Integrity Controls

- **UUID Primary Keys**: Non-sequential, harder to enumerate
- **Foreign Key Constraints**: Referential integrity enforced
- **Column-Level Encryption**: PHI encrypted with AES-256-GCM

### 4. Person/Entity Authentication

- **Password Hashing**: bcrypt for secure password storage
- **MFA Support**: TOTP secret storage (encrypted)
- **Session Management**: Login tracking and lockout support

## Schema Overview

```
┌─────────────────┐     ┌─────────────────┐
│  organizations  │────<│      users      │
└─────────────────┘     └─────────────────┘
         │                      │
         │              ┌───────┴───────┐
         │              │               │
         ▼              ▼               ▼
┌─────────────────┐   ┌─────────────────┐
│    patients     │──<│  medical_cases  │
└─────────────────┘   └─────────────────┘
         │                    │
         │            ┌───────┼───────┐
         │            │       │       │
         ▼            ▼       ▼       ▼
┌─────────────────┬─────────────────┬─────────────────┐
│   diagnoses     │ medical_images  │ treatment_plans │
└─────────────────┴─────────────────┴─────────────────┘

┌─────────────────┐     ┌─────────────────┐
│   medications   │     │   audit_logs    │
└─────────────────┘     └─────────────────┘
```

## Encrypted Fields (PHI)

The following patient fields are encrypted with AES-256-GCM:

| Field                         | Description              |
| ----------------------------- | ------------------------ |
| `first_name_encrypted`        | Patient first name       |
| `last_name_encrypted`         | Patient last name        |
| `date_of_birth_encrypted`     | Date of birth            |
| `ssn_encrypted`               | Social Security Number   |
| `email_encrypted`             | Email address            |
| `phone_encrypted`             | Phone number             |
| `address_encrypted`           | Full address (JSON)      |
| `emergency_contact_encrypted` | Emergency contact (JSON) |
| `insurance_encrypted`         | Insurance details (JSON) |

### Encryption Key Management

⚠️ **CRITICAL**: Encryption keys must NEVER be stored in the database.

- Keys should be managed via a secure key management service (AWS KMS, HashiCorp Vault, etc.)
- Keys are passed to the application at runtime
- Key rotation should be implemented

## Row-Level Security

RLS policies enforce multi-tenant data isolation:

```sql
-- Set context at connection start
SET app.current_organization_id = 'org-uuid-here';
SET app.current_user_id = 'user-uuid-here';
SET app.current_user_role = 'doctor';
```

## Usage

### Running Migrations (Alembic)

```bash
cd services/ai-service

# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Using Prisma

```bash
cd database

# Generate Prisma Client
npx prisma generate

# Push schema to database
npx prisma db push

# Create migration
npx prisma migrate dev --name init

# View database in browser
npx prisma studio
```

## Indexes

Optimized indexes are created for:

- Organization lookups (multi-tenant filtering)
- Patient MRN searches
- Case status filtering
- Diagnosis status and ICD code lookups
- Audit log compliance queries
- PHI access tracking

## Data Types

| Type          | Usage                                           |
| ------------- | ----------------------------------------------- |
| `UUID`        | All primary keys                                |
| `TIMESTAMPTZ` | All timestamps (timezone-aware)                 |
| `JSONB`       | Flexible medical data (allergies, vitals, etc.) |
| `BYTEA`       | Encrypted PHI fields                            |
| `ENUM`        | Status and type fields                          |
| `TEXT[]`      | Tags, ICD codes, arrays                         |

## Maintenance

### Vacuum and Analyze

```sql
-- Run periodically for performance
VACUUM ANALYZE neuraxis.patients;
VACUUM ANALYZE neuraxis.medical_cases;
VACUUM ANALYZE neuraxis.audit_logs;
```

### Partition Audit Logs (Recommended for Production)

For high-volume environments, partition `audit_logs` by date:

```sql
-- Example: Monthly partitioning
CREATE TABLE audit_logs_2026_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

## Security Reminders

1. ✅ Never store encryption keys in the database
2. ✅ Use TLS for all database connections
3. ✅ Implement regular key rotation
4. ✅ Enable audit logging at the PostgreSQL level
5. ✅ Regular security audits and penetration testing
6. ✅ Implement data retention policies per HIPAA requirements
