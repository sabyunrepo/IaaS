-- Jittda Sniper v5.0 — Fresh DB Schema
-- Clean Slate: Alembic 히스토리 없이 최적화된 단일 스키마

-- 확장 모듈
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- SonarQube 전용 DB
SELECT 'CREATE DATABASE sonarqube'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sonarqube')\gexec

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
    company_name VARCHAR(100),
    company_slug VARCHAR(50) UNIQUE,
    company_logo VARCHAR(500),
    company_description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 분석 Job
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    temporal_workflow_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    input_data JSONB NOT NULL,
    result_data JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_workflow ON jobs(temporal_workflow_id);
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

-- ============================================================
-- 채용 공고 / 지원 관리 (Phase 5)
-- ============================================================

-- 채용 공고
CREATE TABLE postings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    jd_description TEXT,
    jd_languages TEXT[] DEFAULT '{}',
    jd_tech_stack TEXT[] DEFAULT '{}',
    jd_experience_years INT,
    auto_analyze BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft','active','closed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_postings_user ON postings(user_id);
CREATE INDEX idx_postings_status ON postings(status);

-- 지원 (applications)
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    posting_id UUID NOT NULL REFERENCES postings(id) ON DELETE CASCADE,
    candidate_name VARCHAR(200),
    candidate_email VARCHAR(200),
    github_username VARCHAR(100),
    github_urls TEXT[] DEFAULT '{}',
    linkedin_url VARCHAR(500),
    resume_path VARCHAR(500),
    cover_letter_path VARCHAR(500),
    portfolio_path VARCHAR(500),
    memo TEXT,
    source VARCHAR(20) DEFAULT 'admin_manual' CHECK (source IN ('self_apply','admin_manual')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending','analyzing','completed','failed')),
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(posting_id, candidate_email)
);
CREATE INDEX idx_apps_posting ON applications(posting_id);
CREATE INDEX idx_apps_job ON applications(job_id);
CREATE INDEX idx_apps_status ON applications(status);

-- 파일 업로드 메타
CREATE TABLE file_uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploader_type VARCHAR(20) NOT NULL CHECK (uploader_type IN ('admin','candidate')),
    uploader_ref VARCHAR(200),
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('resume','cover_letter','portfolio')),
    file_name VARCHAR(300) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    content_type VARCHAR(100),
    size_bytes BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
