-- PostgreSQL initialization
-- Creates extensions and tables for Vantict Sniper

-- pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Langfuse DB
CREATE DATABASE langfuse;

-- ============================================
-- Auth Tables
-- ============================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    image VARCHAR(2048),
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_account_id VARCHAR(255) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at BIGINT,
    token_type VARCHAR(50),
    scope TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(provider, provider_account_id)
);

CREATE INDEX IF NOT EXISTS idx_oauth_provider ON oauth_accounts(provider, provider_account_id);
CREATE INDEX IF NOT EXISTS idx_oauth_user ON oauth_accounts(user_id);

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(10) NOT NULL,
    name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- ============================================
-- Job Tables
-- ============================================

CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    temporal_workflow_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    input_data JSONB NOT NULL,
    final_output JSONB,
    callback_url VARCHAR(2048),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_temporal ON jobs(temporal_workflow_id);

-- ============================================
-- Checkpoint Tables
-- ============================================

CREATE TABLE IF NOT EXISTS checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    phase VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(job_id, phase)
);

CREATE INDEX IF NOT EXISTS idx_checkpoints_job ON checkpoints(job_id);

-- ============================================
-- Embeddings Table
-- ============================================

CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL,
    content_key VARCHAR(255) NOT NULL,
    content_text TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_embeddings_job ON embeddings(job_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_kind ON embeddings(kind);

-- ============================================
-- Knowledge Graph Tables
-- ============================================

-- KG Nodes: Entity storage with optional embeddings for hybrid search
CREATE TABLE IF NOT EXISTS kg_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}',
    embedding VECTOR(1536),
    provenance JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kg_nodes_job ON kg_nodes(job_id);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_type ON kg_nodes(entity_type);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_job_type ON kg_nodes(job_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_kg_nodes_name ON kg_nodes(name);

-- KG Edges: Relationship storage with confidence scores
CREATE TABLE IF NOT EXISTS kg_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES kg_nodes(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,
    properties JSONB DEFAULT '{}',
    confidence INTEGER NOT NULL DEFAULT 100,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kg_edges_job ON kg_edges(job_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON kg_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_relation ON kg_edges(relation_type);
CREATE INDEX IF NOT EXISTS idx_kg_edges_job_relation ON kg_edges(job_id, relation_type);

-- Claim-Evidence: Verification records for interview probing
CREATE TABLE IF NOT EXISTS claim_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    claim_node_id UUID REFERENCES kg_nodes(id) ON DELETE SET NULL,
    evidence_node_id UUID REFERENCES kg_nodes(id) ON DELETE SET NULL,
    evidence_type VARCHAR(50) NOT NULL,
    evidence_strength INTEGER NOT NULL,
    analysis TEXT,
    recommended_probe TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_claim_evidence_job ON claim_evidence(job_id);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_type ON claim_evidence(evidence_type);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_strength ON claim_evidence(evidence_strength);

-- ============================================
-- Skill Taxonomy Tables (Hybrid Skill Graph)
-- Source: MIND Tech Ontology (3,333 skills)
-- ============================================

-- Canonical skill names with embeddings
CREATE TABLE IF NOT EXISTS skill_taxonomy (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(50),
    domain VARCHAR(50),
    embedding VECTOR(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_taxonomy_canonical ON skill_taxonomy(canonical_name);
CREATE INDEX IF NOT EXISTS idx_taxonomy_category ON skill_taxonomy(category);
CREATE INDEX IF NOT EXISTS idx_taxonomy_domain ON skill_taxonomy(domain);

-- Skill aliases (synonyms → canonical)
CREATE TABLE IF NOT EXISTS skill_aliases (
    id SERIAL PRIMARY KEY,
    taxonomy_id INT NOT NULL REFERENCES skill_taxonomy(id) ON DELETE CASCADE,
    alias VARCHAR(255) NOT NULL,
    source VARCHAR(20) NOT NULL DEFAULT 'ontology',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_skill_alias UNIQUE (alias)
);

CREATE INDEX IF NOT EXISTS idx_alias_lookup ON skill_aliases(alias);

-- Skill relationships (implies, requires, related_to, subset_of)
CREATE TABLE IF NOT EXISTS skill_relationships (
    id SERIAL PRIMARY KEY,
    source_id INT NOT NULL REFERENCES skill_taxonomy(id) ON DELETE CASCADE,
    target_id INT NOT NULL REFERENCES skill_taxonomy(id) ON DELETE CASCADE,
    relation_type VARCHAR(30) NOT NULL,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_skill_rel_source ON skill_relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_skill_rel_target ON skill_relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_skill_rel_type ON skill_relationships(relation_type);

-- ============================================
-- Candidate & JD Tables (Multi-Tenant)
-- ============================================

-- Candidates (1급 엔터티, JD-agnostic)
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    experience_years INT,
    experience_level VARCHAR(50),
    skills TEXT[] NOT NULL DEFAULT '{}',
    github_username VARCHAR(255),
    linkedin_url VARCHAR(2048),
    profile_data JSONB NOT NULL DEFAULT '{}',
    data_completeness FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_candidates_user ON candidates(user_id);
CREATE INDEX IF NOT EXISTS idx_candidates_skills ON candidates USING GIN (skills);

-- Job Descriptions (1급 엔터티)
CREATE TABLE IF NOT EXISTS job_descriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(500) NOT NULL,
    required_skills TEXT[] DEFAULT '{}',
    preferred_skills TEXT[] DEFAULT '{}',
    jd_text TEXT,
    jd_analysis JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jd_user ON job_descriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_jd_skills ON job_descriptions USING GIN (required_skills);

-- Candidate ↔ JD Match Results (사전계산)
CREATE TABLE IF NOT EXISTS candidate_jd_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    jd_id UUID NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    overall_match_score FLOAT DEFAULT 0.0,
    skill_match_score FLOAT DEFAULT 0.0,
    skill_matches JSONB DEFAULT '{}',
    gaps JSONB DEFAULT '[]',
    match_explanation TEXT,
    confidence_level VARCHAR(10) DEFAULT 'medium',
    job_id UUID REFERENCES jobs(id),
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(candidate_id, jd_id)
);

CREATE INDEX IF NOT EXISTS idx_match_by_jd ON candidate_jd_matches(jd_id, overall_match_score DESC);
CREATE INDEX IF NOT EXISTS idx_match_by_candidate ON candidate_jd_matches(candidate_id, overall_match_score DESC);
CREATE INDEX IF NOT EXISTS idx_match_user ON candidate_jd_matches(user_id);

-- Candidate Embeddings (프로필 시맨틱 검색)
CREATE TABLE IF NOT EXISTS candidate_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    embedding_type VARCHAR(50),
    embedding VECTOR(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(candidate_id, embedding_type)
);

CREATE INDEX IF NOT EXISTS idx_candidate_emb_user ON candidate_embeddings(user_id);

-- Add candidate_id and jd_id to existing jobs table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='jobs' AND column_name='candidate_id') THEN
        ALTER TABLE jobs ADD COLUMN candidate_id UUID REFERENCES candidates(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='jobs' AND column_name='jd_id') THEN
        ALTER TABLE jobs ADD COLUMN jd_id UUID REFERENCES job_descriptions(id);
    END IF;
END $$;

-- ============================================================
-- Row Level Security (RLS) — Multi-tenant isolation
-- Users can only access their own data.
-- The application sets current_setting('app.current_user_id')
-- before each query to enforce tenant isolation.
-- ============================================================

-- Enable RLS on tenant-scoped tables
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_descriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_jd_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_embeddings ENABLE ROW LEVEL SECURITY;

-- Candidates: user can only see/modify their own candidates
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='candidates' AND policyname='candidates_user_isolation') THEN
        CREATE POLICY candidates_user_isolation ON candidates
            USING (user_id = current_setting('app.current_user_id', true)::uuid)
            WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);
    END IF;
END $$;

-- Job Descriptions: user can only see/modify their own JDs
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='job_descriptions' AND policyname='jd_user_isolation') THEN
        CREATE POLICY jd_user_isolation ON job_descriptions
            USING (user_id = current_setting('app.current_user_id', true)::uuid)
            WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);
    END IF;
END $$;

-- Candidate-JD Matches: user can only see/modify their own matches
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='candidate_jd_matches' AND policyname='match_user_isolation') THEN
        CREATE POLICY match_user_isolation ON candidate_jd_matches
            USING (user_id = current_setting('app.current_user_id', true)::uuid)
            WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);
    END IF;
END $$;

-- Candidate Embeddings: user can only see/modify their own embeddings
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='candidate_embeddings' AND policyname='emb_user_isolation') THEN
        CREATE POLICY emb_user_isolation ON candidate_embeddings
            USING (user_id = current_setting('app.current_user_id', true)::uuid)
            WITH CHECK (user_id = current_setting('app.current_user_id', true)::uuid);
    END IF;
END $$;

-- ============================================
-- Schema Migrations (idempotent)
-- ============================================

-- v2: users 테이블에 role, github_username 추가
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role') THEN
        ALTER TABLE users ADD COLUMN role VARCHAR(50);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='github_username') THEN
        ALTER TABLE users ADD COLUMN github_username VARCHAR(255);
    END IF;
END $$;

-- v2: candidates 테이블에 is_self_registered, selected_repos 추가
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='candidates' AND column_name='is_self_registered') THEN
        ALTER TABLE candidates ADD COLUMN is_self_registered BOOLEAN DEFAULT false;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='candidates' AND column_name='selected_repos') THEN
        ALTER TABLE candidates ADD COLUMN selected_repos TEXT[] DEFAULT '{}';
    END IF;
END $$;

-- BYPASS policy for the application role (superuser/owner already bypasses)
-- The backend connects as the DB owner, so RLS is bypassed by default.
-- When we want to enforce RLS, we use SET ROLE or row_security = force.
-- For now, the policies are in place for future enforcement.
