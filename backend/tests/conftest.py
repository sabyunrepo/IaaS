"""
backend/tests/conftest.py
공통 Fixtures 및 테스트 설정
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ============================================================
# Phase 0: Input Enrichment Fixtures
# ============================================================

@pytest.fixture
def sample_jd_text():
    """샘플 JD 텍스트"""
    return """
주요업무
• AI 활용 서비스 개발 : 기존 AI 서비스 고도화 및 LLM을 활용한 신규 AI 서비스를 직접 개발
• AI 모델 백엔드 구축 : AI 모델을 상용 애플리케이션과 효율적으로 연동

자격요건
• 관련 경력 3년 이상
• LLM API 활용 경험
• Python과 TypeScript를 활용한 API 개발 및 대규모 데이터 처리 로직 구현에 능숙

우대사항
• AI 모델 Fine-tuning 경험
• 대규모 AI 서비스 운영 경험
"""


@pytest.fixture
def sample_input_data(sample_jd_text):
    """Phase 0 입력 데이터"""
    return {
        "resume_path": None,
        "portfolio_path": None,
        "linkedin_url": "https://www.linkedin.com/in/test-user",
        "git_url": None,
        "candidate_github_username": None,
        "jd_text": sample_jd_text,
        "experience_level": "시니어",
        "language_config": {
            "output_language": "ko",
            "terminology_languages": ["ko", "en"],
        },
        "max_questions": 25,
        "include_expected_answers": True,
    }


@pytest.fixture
def sample_linkedin_profile():
    """샘플 LinkedIn 프로필 (Bright Data 정규화 결과)"""
    return {
        "profile_url": "https://www.linkedin.com/in/test-user",
        "full_name": "Test User",
        "headline": "Software Engineer at TechCorp",
        "summary": "Experienced developer with 5 years of experience",
        "country": "KR",
        "city": "Seoul",
        "avatar_url": "https://example.com/avatar.jpg",
        "current_company": "TechCorp",
        "experiences": [
            {
                "title": "Senior Engineer",
                "company": "TechCorp",
                "description": "Building AI systems",
                "starts_at": "2022-01",
                "ends_at": None,
            }
        ],
        "education": [
            {
                "school": "Seoul National University",
                "degree": "Bachelor",
                "field": "Computer Science",
            }
        ],
        "skills": ["Python", "TypeScript", "FastAPI", "React"],
        "languages": ["Korean", "English"],
        "certifications": [],
        "projects": [
            {
                "title": "AI Interview Generator",
                "description": "GitHub: https://github.com/testuser/interview-gen",
            }
        ],
        "honors_and_awards": [],
        "activity": [],
        "followers": 500,
        "connections": 500,
        "github_url": None,
        "websites": [],
    }


@pytest.fixture
def mock_enriched_input(sample_input_data, sample_linkedin_profile):
    """Phase 0 완료 후 예상 결과 (Phase 1+ 테스트용)"""
    return {
        "raw_input": sample_input_data,
        "github_urls": ["https://github.com/testuser/interview-gen"],
        "all_extracted_github_urls": ["https://github.com/testuser/interview-gen"],
        "candidate_github_username": "testuser",
        "github_validation": {
            "username": "testuser",
            "confidence": "high",
            "source": "personal_repo:https://github.com/testuser/interview-gen",
            "personal_repos": ["https://github.com/testuser/interview-gen"],
            "skipped_org_repos": [],
        },
        "linkedin_profile": sample_linkedin_profile,
        "extraction_sources": {
            "github_urls": ["linkedin_project"],
        },
        "available_analyses": ["jd_analysis", "document_analysis", "code_analysis"],
        "document_errors": [],
    }


# ============================================================
# JIT-26: Code Analysis Pipeline Fixtures
# ============================================================

@pytest.fixture
def sample_jd_tech_stack():
    """JD 기술 스택 샘플"""
    return ["Python", "FastAPI", "PostgreSQL"]


@pytest.fixture
def valid_repo_result():
    """정상 레포 분석 결과 (validate_code_analysis 통과용)"""
    return {
        "repo_name": "test-repo",
        "candidate_commits": 50,
        "ast_analysis": {
            "functions": [{"name": "main"}, {"name": "helper"}],
            "classes": [{"name": "UserService"}],
            "parser_used": "ast",
        },
        "analysis": {
            "patterns": ["Repository", "Factory"],
            "quality_score": 0.7,
            "notable_implementations": [
                {"title": "Async workflow engine", "question_potential": 0.9},
            ],
        },
        "notable_implementations": [
            {"title": "Async workflow engine", "question_potential": 0.9},
        ],
        "hybrid_metadata": {
            "key_files_count": 3,
            "deep_analyses_count": 3,
        },
    }


# ============================================================
# Mock Services
# ============================================================

@pytest.fixture
def mock_linkedin_service():
    """LinkedIn 서비스 모킹"""
    mock = AsyncMock()
    mock.get_profile.return_value = {
        "profile_url": "https://www.linkedin.com/in/test-user",
        "full_name": "Test User",
        "projects": [
            {"title": "Project", "description": "GitHub: https://github.com/testuser/repo"}
        ],
    }
    return mock


@pytest.fixture
def mock_github_service():
    """GitHub 서비스 모킹"""
    mock = AsyncMock()
    mock.get_account_type.return_value = {
        "username": "testuser",
        "type": "User",
        "name": "Test User",
        "error": None,
    }
    mock.infer_candidate_username.return_value = {
        "username": "testuser",
        "confidence": "high",
        "source": "personal_repo",
        "personal_repos": ["https://github.com/testuser/repo"],
        "skipped_org_repos": [],
    }
    return mock


@pytest.fixture
def mock_document_parser():
    """Document Parser 모킹"""
    mock = AsyncMock()
    mock.return_value = "Extracted text from document"
    return mock


# ============================================================
# Temporal Activity 테스트용
# ============================================================

@pytest.fixture
def mock_heartbeat():
    """Temporal heartbeat 모킹"""
    with patch("temporalio.activity.heartbeat") as mock:
        mock.side_effect = lambda msg: print(f"  ♥ {msg}")
        yield mock


# ============================================================
# Phase 2: Analysis Fixtures
# ============================================================

@pytest.fixture
def mock_aggregated_analysis():
    """Phase 2 완료 후 집계 결과 (Phase 3 테스트용)"""
    return {
        "document_analysis": {
            "name": "Test User",
            "experience_years": 5,
            "skills": ["Python", "TypeScript", "FastAPI"],
            "education": [{"school": "Seoul National University"}],
            "work_history": [{"company": "TechCorp", "title": "Senior Engineer"}],
            "projects": [{"name": "AI Interview Generator"}],
            "summary": "Experienced software engineer",
        },
        "code_analysis": {
            "repositories": [
                {
                    "repo_url": "https://github.com/testuser/interview-gen",
                    "repo_name": "interview-gen",
                    "language": "Python",
                    "candidate_commits": 150,
                    "notable_implementations": [
                        {"title": "Async workflow engine", "complexity": "high"}
                    ],
                }
            ],
            "combined_tech_stack": ["Python", "FastAPI", "Temporal"],
            "total_patterns": 5,
            "total_notable_implementations": 3,
            "top_question_candidates": [
                {"title": "Async workflow design", "question_potential": 0.9}
            ],
        },
        "jd_analysis": {
            "job_title": "AI Engineer",
            "company_name": "TechCorp",
            "requirements": [
                {"skill": "LLM API", "category": "필수"},
                {"skill": "Python", "category": "필수"},
            ],
            "responsibilities": ["AI 서비스 개발", "백엔드 구축"],
            "company_culture": [],
        },
    }


# ============================================================
# JIT-41~44: Integration Test Fixtures
# ============================================================

@pytest.fixture
def candidate_profile_with_skills():
    """JIT-41/42/43: UnifiedCandidateProfile (multi-source skills)"""
    return {
        "name": "Test User",
        "skills": [
            {"canonical_name": "Python", "sources": ["resume", "github"], "category": "language", "confidence": 1.0, "proficiency_signals": {}, "implied_skills": [], "aliases": [], "domain": "backend"},
            {"canonical_name": "FastAPI", "sources": ["resume", "github", "linkedin"], "category": "framework", "confidence": 1.0, "proficiency_signals": {}, "implied_skills": [], "aliases": [], "domain": "backend"},
            {"canonical_name": "TypeScript", "sources": ["resume"], "category": "language", "confidence": 0.9, "proficiency_signals": {}, "implied_skills": [], "aliases": [], "domain": "frontend"},
            {"canonical_name": "PostgreSQL", "sources": ["github", "linkedin"], "category": "tool", "confidence": 0.8, "proficiency_signals": {}, "implied_skills": [], "aliases": [], "domain": "backend"},
        ],
        "experiences": [
            {"company": "TechCorp", "title": "Senior Engineer", "duration": "3 years"},
        ],
        "linkedin_experiences": [
            {"title": "Senior Engineer", "company": "TechCorp", "description": "Building AI systems", "starts_at": "2022-01"},
        ],
        "linkedin_honors": [{"title": "Top Contributor 2024", "issuer": "TechConf"}],
        "linkedin_projects": [{"title": "AI Interview Generator"}],
        "areas_to_probe": ["Distributed system experience gap", "No team leadership evidence"],
        "data_completeness": 0.85,
        "data_sources": ["resume", "github", "linkedin"],
        "confidence_level": "high",
        "experience_years": 5,
        "experience_level": "시니어",
    }


@pytest.fixture
def empty_candidate_profile():
    """시나리오 4: candidate_profile 없을 때"""
    return None


@pytest.fixture
def code_analysis_hybrid():
    """JIT-44: HYBRID 파이프라인 코드 분석 결과"""
    return {
        "repositories": [
            {
                "repo_name": "test-repo",
                "candidate_commits": 150,
                "ast_analysis": {
                    "functions": [{"name": "main"}, {"name": "process_data"}, {"name": "validate_input"}],
                    "classes": [{"name": "UserService"}],
                },
                "hybrid_metadata": {
                    "key_files_count": 5,
                    "deep_analyses_count": 4,
                    "ranked_chunks_count": 12,
                    "model_used": "moonshot-v1-128k",
                    "use_ast_pipeline": True,
                    "used_clone_fallback": False,
                },
            },
            {
                "repo_name": "test-lib",
                "candidate_commits": 80,
                "ast_analysis": {
                    "functions": [{"name": "helper_fn"}, {"name": "util_fn"}],
                    "classes": [],
                },
                "hybrid_metadata": {
                    "key_files_count": 3,
                    "deep_analyses_count": 2,
                    "ranked_chunks_count": 8,
                    "model_used": "moonshot-v1-128k",
                    "use_ast_pipeline": True,
                    "used_clone_fallback": False,
                },
            },
        ],
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        "combined_tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        "pipeline_type": "clone_based",
        "ast_chunk_count": 20,
        "analyzed_functions_count": 5,
        "hybrid_metadata": {
            "method": "hybrid",
            "total_repos": 2,
            "total_ast_chunks": 20,
            "total_deep_analyses": 6,
        },
        "monthly_contributions": [10, 15, 20, 25, 30, 20, 15, 10, 5, 0, 0, 0],
        "quality_metrics": {"test_coverage": 0.7},
        "risk_flags": [],
    }


@pytest.fixture
def code_analysis_legacy():
    """JIT-44: LEGACY 파이프라인 (HYBRID 필드 없음)"""
    return {
        "repositories": [
            {"repo_name": "old-repo", "candidate_commits": 50, "ast_analysis": {"functions": [], "classes": []}},
        ],
        "tech_stack": ["Python"],
        "pipeline_type": "legacy",
        "monthly_contributions": [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
        "quality_metrics": {},
        "risk_flags": [],
    }


@pytest.fixture
def document_analysis_with_skills():
    """document_analysis with profile.skills (fallback 용)"""
    return {
        "profile": {
            "name": "Test User",
            "skills": ["Python", "JavaScript", "Docker"],
            "experience_years": 5,
            "experiences": [{"company": "OldCorp", "title": "Developer", "duration": "2 years"}],
        },
        "jd_match_score": 0.7,
    }


@pytest.fixture
def document_analysis_empty_skills():
    """document_analysis with empty skills"""
    return {
        "profile": {"name": "Test User", "skills": [], "experience_years": 0},
        "jd_match_score": 0.3,
    }


@pytest.fixture
def jd_analysis_fixture():
    """JD 분석 결과"""
    return {
        "job_title": "Backend Engineer",
        "company_name": "TechCorp",
        "company_context": "AI 스타트업",
        "requirements": [
            {"skill": "Python", "category": "필수", "description": "Python 3년 이상"},
            {"skill": "FastAPI", "category": "필수", "description": "FastAPI 경험"},
            {"skill": "PostgreSQL", "category": "우대", "description": "DB 설계"},
            {"skill": "Kubernetes", "category": "우대", "description": "컨테이너 오케스트레이션"},
        ],
        "responsibilities": ["백엔드 개발", "API 설계"],
        "success_metrics": [],
    }
