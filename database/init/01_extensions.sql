-- ==============================================
-- LexIntellectus - Database Initialization
-- ==============================================
-- This script runs automatically when PostgreSQL
-- container starts for the first time.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'LexIntellectus database initialized with uuid-ossp, pgcrypto, and pgvector extensions.';
END $$;
