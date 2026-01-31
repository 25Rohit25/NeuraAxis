-- ============================================
-- NEURAXIS PostgreSQL Initialization Script
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS neuraxis;

-- Grant permissions
GRANT ALL ON SCHEMA neuraxis TO neuraxis_user;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'NEURAXIS database initialized successfully';
END $$;
