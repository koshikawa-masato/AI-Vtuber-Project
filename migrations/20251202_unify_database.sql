-- =============================================================================
-- Migration: Unify LINE Bot and WhatsApp Bot Database
-- Date: 2025-12-02
-- Target DB: sisters_on_whatsapp
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Step 1: Enable pgvector extension (for LINE Bot RAG search)
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;

-- -----------------------------------------------------------------------------
-- Step 2: Add platform column to existing WhatsApp tables
-- -----------------------------------------------------------------------------

-- user_sessions
ALTER TABLE user_sessions
    ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'whatsapp';

-- conversation_history
ALTER TABLE conversation_history
    ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'whatsapp';

-- user_memories (WhatsApp version)
ALTER TABLE user_memories
    ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'whatsapp';

-- user_consents
ALTER TABLE user_consents
    ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'whatsapp';

-- daily_trends
ALTER TABLE daily_trends
    ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'whatsapp';

-- weekly_trends
ALTER TABLE weekly_trends
    ADD COLUMN IF NOT EXISTS platform VARCHAR(20) DEFAULT 'whatsapp';

-- -----------------------------------------------------------------------------
-- Step 3: Add LINE Bot specific columns to existing tables
-- -----------------------------------------------------------------------------

-- user_sessions: Add LINE Bot specific columns
ALTER TABLE user_sessions
    ADD COLUMN IF NOT EXISTS user_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS user_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS selected_mode VARCHAR(20) DEFAULT 'auto',
    ADD COLUMN IF NOT EXISTS feedback_state VARCHAR(20) DEFAULT 'none',
    ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_hash ON user_sessions(user_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);

-- conversation_history: Add LINE Bot specific columns
ALTER TABLE conversation_history
    ADD COLUMN IF NOT EXISTS user_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS user_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS message TEXT,
    ADD COLUMN IF NOT EXISTS embedding vector(1536);

CREATE INDEX IF NOT EXISTS idx_conversation_user_hash ON conversation_history(user_hash);
CREATE INDEX IF NOT EXISTS idx_conversation_user_id ON conversation_history(user_id);

-- user_memories: Add LINE Bot specific columns with pgvector
ALTER TABLE user_memories
    ADD COLUMN IF NOT EXISTS user_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS user_hash VARCHAR(64),
    ADD COLUMN IF NOT EXISTS memory_type VARCHAR(50),
    ADD COLUMN IF NOT EXISTS memory_text TEXT,
    ADD COLUMN IF NOT EXISTS context TEXT,
    ADD COLUMN IF NOT EXISTS embedding vector(1536),
    ADD COLUMN IF NOT EXISTS importance INTEGER DEFAULT 5,
    ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 0.5,
    ADD COLUMN IF NOT EXISTS fact_checked BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS fact_check_passed BOOLEAN,
    ADD COLUMN IF NOT EXISTS fact_check_source VARCHAR(50),
    ADD COLUMN IF NOT EXISTS learned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS reference_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_referenced TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_user_memories_user_hash ON user_memories(user_hash);
CREATE INDEX IF NOT EXISTS idx_user_memories_embedding ON user_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- daily_trends: Add character column if not exists
ALTER TABLE daily_trends
    ADD COLUMN IF NOT EXISTS character VARCHAR(50);

-- -----------------------------------------------------------------------------
-- Step 4: Create LINE Bot specific tables
-- -----------------------------------------------------------------------------

-- learning_logs (LINE Bot specific)
CREATE TABLE IF NOT EXISTS learning_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    character VARCHAR(50) NOT NULL,
    user_id VARCHAR(255),
    user_hash VARCHAR(64),
    user_message TEXT,
    bot_response TEXT,
    phase5_user_tier VARCHAR(50),
    phase5_response_tier VARCHAR(50),
    memories_used TEXT,
    response_time FLOAT,
    metadata TEXT,
    platform VARCHAR(20) DEFAULT 'line',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learning_logs_user_hash ON learning_logs(user_hash);
CREATE INDEX IF NOT EXISTS idx_learning_logs_timestamp ON learning_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_learning_logs_character ON learning_logs(character);

-- learned_knowledge (LINE Bot RAG knowledge base with pgvector)
CREATE TABLE IF NOT EXISTS learned_knowledge (
    id SERIAL PRIMARY KEY,
    character VARCHAR(50) NOT NULL,
    word VARCHAR(255) NOT NULL,
    meaning TEXT NOT NULL,
    context TEXT,
    embedding vector(1536),
    platform VARCHAR(20) DEFAULT 'line',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_learned_knowledge_character ON learned_knowledge(character);
CREATE INDEX IF NOT EXISTS idx_learned_knowledge_embedding ON learned_knowledge USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- user_personality (LINE Bot specific)
CREATE TABLE IF NOT EXISTS user_personality (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    user_hash VARCHAR(64) UNIQUE,
    playfulness_score FLOAT DEFAULT 0.5,
    trust_score FLOAT DEFAULT 0.5,
    relationship_level INTEGER DEFAULT 1,
    total_conversations INTEGER DEFAULT 0,
    platform VARCHAR(20) DEFAULT 'line',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_personality_user_hash ON user_personality(user_hash);

-- user_trust_history (LINE Bot specific)
CREATE TABLE IF NOT EXISTS user_trust_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    user_hash VARCHAR(64),
    character VARCHAR(50),
    trust_change FLOAT,
    reason TEXT,
    platform VARCHAR(20) DEFAULT 'line',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_trust_history_user_hash ON user_trust_history(user_hash);

-- feedback (LINE Bot specific)
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    user_hash VARCHAR(64),
    feedback_text TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    platform VARCHAR(20) DEFAULT 'line',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_hash ON feedback(user_hash);

-- enriched_trends (LINE Bot specific)
CREATE TABLE IF NOT EXISTS enriched_trends (
    id SERIAL PRIMARY KEY,
    character VARCHAR(50),
    topic VARCHAR(255),
    content TEXT,
    enriched_content TEXT,
    platform VARCHAR(20) DEFAULT 'line',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_enriched_trends_character ON enriched_trends(character);

-- -----------------------------------------------------------------------------
-- Step 5: Add user_consents support for LINE Bot
-- -----------------------------------------------------------------------------
ALTER TABLE user_consents
    ADD COLUMN IF NOT EXISTS user_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS user_hash VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_user_consents_user_hash ON user_consents(user_hash);

-- -----------------------------------------------------------------------------
-- Summary of changes:
-- 1. pgvector extension enabled for RAG search
-- 2. platform column added to all tables (whatsapp/line)
-- 3. user_hash column added for encrypted identifier lookup
-- 4. LINE Bot specific tables created (learning_logs, learned_knowledge, etc.)
-- 5. pgvector indexes created for embedding columns
-- -----------------------------------------------------------------------------
