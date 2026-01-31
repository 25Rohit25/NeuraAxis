# Alembic Database Migrations

This directory contains database migration files managed by Alembic.

## Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Structure

- `versions/` - Migration script files
- `env.py` - Alembic environment configuration
- `script.py.mako` - Template for new migrations
