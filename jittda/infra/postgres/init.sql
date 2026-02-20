-- Jittda Sniper v5.0 — Fresh DB Schema
-- Clean Slate: Alembic 히스토리 없이 최적화된 단일 스키마

-- 확장 모듈
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- SonarQube 전용 DB
SELECT 'CREATE DATABASE sonarqube'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sonarqube')\gexec

-- ============================================================
-- LangGraph Checkpoint (3.0.x 호환)
-- ============================================================
CREATE TABLE IF NOT EXISTS checkpoints (
    thread_id TEXT NOT NULL,
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,
    parent_checkpoint_id TEXT,
    type TEXT,
    checkpoint BYTEA,
    metadata BYTEA,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

-- ============================================================
-- 비즈니스 테이블
-- ============================================================

-- 사용자
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    oauth_provider VARCHAR(20),
    oauth_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 분석 Job
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    langgraph_thread_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    input_data JSONB NOT NULL,
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_thread ON jobs(langgraph_thread_id);
CREATE INDEX idx_jobs_status ON jobs(status);

-- 분석 결과 (Worker별 — Reference Passing 저장소)
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    worker_name VARCHAR(50) NOT NULL,
    supervisor_name VARCHAR(30) NOT NULL,
    result_data JSONB NOT NULL,
    metrics JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_analysis_job ON analysis_results(job_id);
CREATE INDEX idx_analysis_worker ON analysis_results(worker_name);

-- 4대 지표 점수
CREATE TABLE candidate_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    logic_score FLOAT NOT NULL,
    mastery_score FLOAT NOT NULL,
    stability_score FLOAT NOT NULL,
    authenticity_score FLOAT NOT NULL,
    weighted_total FLOAT NOT NULL,
    confidence VARCHAR(10) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id)
);

-- Identity Resolution 결과
CREATE TABLE identity_resolutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    github_node_id VARCHAR(50),
    canonical_name VARCHAR(100),
    canonical_email VARCHAR(200),
    mailmap_entries JSONB,
    total_commits INT DEFAULT 0,
    verified_commits INT DEFAULT 0,
    pure_logic_lines INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_id)
);

-- SonarQube 프로젝트 매핑
CREATE TABLE sonarqube_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    project_key VARCHAR(200) NOT NULL,
    repo_url TEXT,
    scan_status VARCHAR(20) DEFAULT 'pending',
    result_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 벡터 임베딩 (pgvector)
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    kind VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_embeddings_job ON embeddings(job_id);
CREATE INDEX idx_embeddings_kind ON embeddings(kind);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);
