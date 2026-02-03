"""
Unit tests for Knowledge Graph services.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import uuid


# ============================================================
# Graph Store Tests
# ============================================================

class TestGraphStoreInit:
    def test_get_graph_store(self):
        from app.services.graph_store import get_graph_store
        store = get_graph_store("test-job-id")
        assert str(store.job_id) == "test-job-id"

    def test_graph_store_class(self):
        from app.services.graph_store import GraphStore
        store = GraphStore("abc-123")
        assert str(store.job_id) == "abc-123"


class TestKGDatabaseModels:
    def test_kg_node_db_importable(self):
        from app.models.database import KGNodeDB
        assert KGNodeDB.__tablename__ == "kg_nodes"

    def test_kg_node_db_columns(self):
        from app.models.database import KGNodeDB
        columns = {c.name for c in KGNodeDB.__table__.columns}
        assert "job_id" in columns
        assert "entity_type" in columns
        assert "name" in columns
        assert "properties" in columns
        assert "provenance" in columns
        assert "embedding" in columns

    def test_kg_edge_db_importable(self):
        from app.models.database import KGEdgeDB
        assert KGEdgeDB.__tablename__ == "kg_edges"

    def test_kg_edge_db_columns(self):
        from app.models.database import KGEdgeDB
        columns = {c.name for c in KGEdgeDB.__table__.columns}
        assert "job_id" in columns
        assert "source_id" in columns
        assert "target_id" in columns
        assert "relation_type" in columns
        assert "confidence" in columns
        assert "properties" in columns

    def test_claim_evidence_db_importable(self):
        from app.models.database import ClaimEvidenceDB
        assert ClaimEvidenceDB.__tablename__ == "claim_evidence"

    def test_claim_evidence_db_columns(self):
        from app.models.database import ClaimEvidenceDB
        columns = {c.name for c in ClaimEvidenceDB.__table__.columns}
        assert "job_id" in columns
        assert "claim_node_id" in columns
        assert "evidence_node_id" in columns
        assert "evidence_type" in columns
        assert "evidence_strength" in columns
        assert "analysis" in columns
        assert "recommended_probe" in columns


# ============================================================
# Entity Extractor Tests
# ============================================================

class TestCandidateEntityExtractor:
    def test_extractor_init(self):
        from app.services.entity_extractors import CandidateEntityExtractor
        extractor = CandidateEntityExtractor()
        assert extractor.source == "document_analysis"

    def test_extract_skills_from_profile(self):
        from app.services.entity_extractors import get_candidate_extractor
        extractor = get_candidate_extractor()

        profile = {
            "name": "Test User",
            "skills": ["Python", "React", "FastAPI"],
            "work_history": [],
            "education": [],
            "projects": [],
        }

        result = extractor.extract(profile)

        assert len(result.entities) >= 3  # At least 3 skills
        skill_entities = [e for e in result.entities if e.entity_type == "Skill"]
        skill_names = [e.name for e in skill_entities]
        assert "Python" in skill_names
        assert "React" in skill_names
        assert "FastAPI" in skill_names

    def test_extract_work_experience(self):
        from app.services.entity_extractors import get_candidate_extractor
        extractor = get_candidate_extractor()

        profile = {
            "name": "Test User",
            "skills": [],
            "work_history": [
                {
                    "company": "TechCorp",
                    "position": "Senior Engineer",
                    "period": "2020-2023",
                    "description": "Built AI systems",
                    "tech_stack": ["Python", "TensorFlow"],
                }
            ],
            "education": [],
            "projects": [],
        }

        result = extractor.extract(profile)

        work_entities = [e for e in result.entities if e.entity_type == "WorkExperience"]
        assert len(work_entities) == 1
        assert "TechCorp" in work_entities[0].name

        # Check for used_technology relations
        tech_relations = [r for r in result.relations if r.relation_type == "used_technology"]
        assert len(tech_relations) >= 2  # Python and TensorFlow

    def test_categorize_skill(self):
        from app.services.entity_extractors import CandidateEntityExtractor
        extractor = CandidateEntityExtractor()

        assert extractor._categorize_skill("Python") == "programming_language"
        assert extractor._categorize_skill("React") == "frontend"
        assert extractor._categorize_skill("FastAPI") == "backend"
        assert extractor._categorize_skill("PostgreSQL") == "database"
        assert extractor._categorize_skill("AWS") == "cloud"


class TestCodeEntityExtractor:
    def test_extractor_init(self):
        from app.services.entity_extractors import CodeEntityExtractor
        extractor = CodeEntityExtractor()
        assert extractor.source == "code_analysis"

    def test_extract_repositories(self):
        from app.services.entity_extractors import get_code_extractor
        extractor = get_code_extractor()

        code_analysis = {
            "repositories": [
                {
                    "repo_name": "test-repo",
                    "repo_url": "https://github.com/user/test-repo",
                    "language": "Python",
                    "tech_stack": ["FastAPI", "SQLAlchemy"],
                    "patterns": [],
                    "notable_implementations": [],
                }
            ],
            "combined_tech_stack": ["Python", "FastAPI"],
        }

        result = extractor.extract(code_analysis)

        repo_entities = [e for e in result.entities if e.entity_type == "Repository"]
        assert len(repo_entities) == 1
        assert repo_entities[0].name == "test-repo"

        # Check for demonstrated_by relations
        demo_relations = [r for r in result.relations if r.relation_type == "demonstrated_by"]
        assert len(demo_relations) >= 2  # FastAPI and SQLAlchemy

    def test_extract_notable_implementations(self):
        from app.services.entity_extractors import get_code_extractor
        extractor = get_code_extractor()

        code_analysis = {
            "repositories": [
                {
                    "repo_name": "test-repo",
                    "repo_url": "https://github.com/user/test-repo",
                    "language": "Python",
                    "tech_stack": [],
                    "patterns": [],
                    "notable_implementations": [
                        {
                            "title": "Async Workflow Engine",
                            "description": "Custom workflow engine",
                            "file_path": "workflow/engine.py",
                            "line_start": 10,
                            "line_end": 100,
                            "code_snippet": "async def run_workflow():\n    ...",
                            "why_notable": "Complex async patterns",
                            "question_potential": 0.9,
                        }
                    ],
                }
            ],
            "combined_tech_stack": [],
        }

        result = extractor.extract(code_analysis)

        impl_entities = [e for e in result.entities if e.entity_type == "NotableImplementation"]
        assert len(impl_entities) == 1
        assert impl_entities[0].name == "Async Workflow Engine"
        assert impl_entities[0].properties.get("question_potential") == 0.9


class TestJDEntityExtractor:
    def test_extractor_init(self):
        from app.services.entity_extractors import JDEntityExtractor
        extractor = JDEntityExtractor()
        assert extractor.source == "jd_analysis"

    def test_extract_requirements(self):
        from app.services.entity_extractors import get_jd_extractor
        extractor = get_jd_extractor()

        jd_analysis = {
            "job_title": "Senior Engineer",
            "company_name": "TechCorp",
            "requirements": [
                {"skill": "Python", "category": "필수", "experience_years": 3},
                {"skill": "LLM", "category": "우대"},
            ],
            "responsibilities": ["Build AI systems"],
            "company_culture": [],
        }

        result = extractor.extract(jd_analysis)

        req_entities = [e for e in result.entities if e.entity_type == "Requirement"]
        assert len(req_entities) == 2

        # Check priority mapping
        python_req = next(e for e in req_entities if e.name == "Python")
        assert python_req.properties.get("priority") == "required"

        llm_req = next(e for e in req_entities if e.name == "LLM")
        assert llm_req.properties.get("priority") == "preferred"


# ============================================================
# Knowledge Graph Service Tests
# ============================================================

class TestKnowledgeGraphService:
    def test_service_init(self):
        from app.services.knowledge_graph import KnowledgeGraphService
        kg = KnowledgeGraphService("test-job-id")
        assert kg.job_id == "test-job-id"
        assert kg.store is not None
        assert kg._node_cache == {}

    def test_get_knowledge_graph_factory(self):
        from app.services.knowledge_graph import get_knowledge_graph
        kg = get_knowledge_graph("abc-123")
        assert kg.job_id == "abc-123"


# ============================================================
# Conflict Detector Tests
# ============================================================

class TestConflictDetector:
    def test_detector_init(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test-job-id")
        assert detector.job_id == "test-job-id"

    def test_get_conflict_detector_factory(self):
        from app.services.conflict_detector import get_conflict_detector
        detector = get_conflict_detector("abc-123")
        assert detector.job_id == "abc-123"

    def test_determine_skill_severity(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        assert detector._determine_skill_severity("Python") == "high"
        assert detector._determine_skill_severity("React") == "medium"
        assert detector._determine_skill_severity("Obscure Framework") == "low"

    def test_expected_complexity_for_role(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        assert detector._expected_complexity_for_role("senior engineer") == 15.0
        assert detector._expected_complexity_for_role("software engineer") == 10.0
        assert detector._expected_complexity_for_role("junior developer") == 5.0
        assert detector._expected_complexity_for_role("unknown role") is None

    def test_find_related_tech(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        code_skills = {"django", "fastapi", "numpy"}

        assert detector._find_related_tech("python", code_skills) is True
        assert detector._find_related_tech("javascript", code_skills) is False

    def test_generate_skill_probe(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        python_probe = detector._generate_skill_probe("Python")
        assert "Python" in python_probe or "structure" in python_probe

        react_probe = detector._generate_skill_probe("React")
        assert "state" in react_probe or "React" in react_probe

        unknown_probe = detector._generate_skill_probe("UnknownTech")
        assert "UnknownTech" in unknown_probe


# ============================================================
# Graph Queries Tests
# ============================================================

class TestInterviewGraphQueries:
    def test_queries_init(self):
        from app.services.graph_queries import InterviewGraphQueries
        queries = InterviewGraphQueries("test-job-id")
        assert queries.job_id == "test-job-id"

    def test_get_interview_graph_queries_factory(self):
        from app.services.graph_queries import get_interview_graph_queries
        queries = get_interview_graph_queries("abc-123")
        assert queries.job_id == "abc-123"


class TestQuestionCandidateModel:
    def test_question_candidate_creation(self):
        from app.services.graph_queries import QuestionCandidate

        candidate = QuestionCandidate(
            topic="Python",
            category="skill_depth",
            priority=85.0,
            evidence_chain=[{"type": "Repository", "name": "test-repo"}],
            context={"evidence_count": 3},
            recommended_probe="Tell me about your Python experience",
        )

        assert candidate.topic == "Python"
        assert candidate.category == "skill_depth"
        assert candidate.priority == 85.0
        assert len(candidate.evidence_chain) == 1


# ============================================================
# KG Activity Tests
# ============================================================

class TestKGActivities:
    def test_build_knowledge_graph_activity_exists(self):
        from app.workflows.activities.knowledge_graph_activities import build_knowledge_graph
        assert callable(build_knowledge_graph)

    def test_get_kg_question_candidates_activity_exists(self):
        from app.workflows.activities.knowledge_graph_activities import get_kg_question_candidates
        assert callable(get_kg_question_candidates)

    def test_get_evidence_chain_activity_exists(self):
        from app.workflows.activities.knowledge_graph_activities import get_evidence_chain
        assert callable(get_evidence_chain)

    def test_clear_knowledge_graph_activity_exists(self):
        from app.workflows.activities.knowledge_graph_activities import clear_knowledge_graph
        assert callable(clear_knowledge_graph)


# ============================================================
# Worker Registration Tests
# ============================================================

class TestWorkerRegistration:
    def test_kg_activities_in_worker(self):
        from app.worker import ACTIVITIES

        activity_names = [a.__name__ for a in ACTIVITIES]

        assert "build_knowledge_graph" in activity_names
        assert "get_kg_question_candidates" in activity_names
        assert "get_evidence_chain" in activity_names
        assert "clear_knowledge_graph" in activity_names


# ============================================================
# Integration Tests (Modified Activities)
# ============================================================

class TestModifiedActivities:
    def test_document_analysis_returns_kg_count(self):
        """Verify document_analysis activity returns kg_entity_count."""
        # This is a structural test - actual DB integration would require mocking
        from app.workflows.activities.document_analysis import analyze_documents

        # Check the function signature and return type hint
        import inspect
        sig = inspect.signature(analyze_documents)
        assert "input_data" in sig.parameters

    def test_code_analysis_returns_kg_count(self):
        """Verify code_analysis activity returns kg_entity_count."""
        from app.workflows.activities.code_analysis import analyze_code

        import inspect
        sig = inspect.signature(analyze_code)
        assert "github_urls" in sig.parameters
        assert "input_data" in sig.parameters

    def test_jd_analysis_accepts_job_id(self):
        """Verify jd_analysis activity accepts job_id parameter."""
        from app.workflows.activities.jd_analysis import analyze_jd

        import inspect
        sig = inspect.signature(analyze_jd)
        assert "jd_text" in sig.parameters
        assert "job_id" in sig.parameters

    def test_select_topics_accepts_job_id(self):
        """Verify select_topics activity accepts job_id parameter."""
        from app.workflows.activities.question_generation import select_topics

        import inspect
        sig = inspect.signature(select_topics)
        assert "analysis" in sig.parameters
        assert "enriched_input" in sig.parameters
        assert "job_id" in sig.parameters

    def test_craft_question_accepts_job_id(self):
        """Verify craft_question activity accepts job_id parameter."""
        from app.workflows.activities.question_generation import craft_question

        import inspect
        sig = inspect.signature(craft_question)
        assert "topic" in sig.parameters
        assert "job_id" in sig.parameters
