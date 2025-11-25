-- Initialize database for AI Platform

-- Create pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ai_platform TO aiplatform;

-- Set timezone
SET timezone = 'UTC';

-- Create indexes will be handled by SQLAlchemy migrations
-- This script only handles initial setup
