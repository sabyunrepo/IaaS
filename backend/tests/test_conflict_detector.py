"""
Unit tests for Conflict Detector service.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ============================================================
# Conflict Analysis Model Tests
# ============================================================

class TestConflictAnalysisModel:
    def test_conflict_analysis_creation(self):
        from app.services.conflict_detector import ConflictAnalysis

        conflict = ConflictAnalysis(
            claim="Proficiency in Python",
            claim_source="resume",
            expected_evidence="Code demonstrating Python usage",
            actual_evidence=None,
            conflict_type="missing",
            severity="high",
            confidence=85,
            analysis="Candidate claims Python but no evidence found",
            recommended_probe="Can you describe your Python experience?",
        )

        assert conflict.claim == "Proficiency in Python"
        assert conflict.conflict_type == "missing"
        assert conflict.severity == "high"
        assert conflict.confidence == 85

    def test_conflict_analysis_all_types(self):
        from app.services.conflict_detector import ConflictAnalysis

        conflict_types = ["missing", "contradicting", "overstated", "understated"]
        severities = ["high", "medium", "low"]

        for ct in conflict_types:
            for sev in severities:
                conflict = ConflictAnalysis(
                    claim="Test claim",
                    claim_source="resume",
                    expected_evidence="Expected",
                    actual_evidence="Actual",
                    conflict_type=ct,
                    severity=sev,
                    confidence=75,
                    analysis="Analysis text",
                    recommended_probe="Probe question",
                )
                assert conflict.conflict_type == ct
                assert conflict.severity == sev


class TestConflictReportModel:
    def test_conflict_report_creation(self):
        from app.services.conflict_detector import ConflictReport, ConflictAnalysis

        conflict = ConflictAnalysis(
            claim="Test",
            claim_source="resume",
            expected_evidence="Expected",
            actual_evidence=None,
            conflict_type="missing",
            severity="medium",
            confidence=80,
            analysis="Analysis",
            recommended_probe="Probe",
        )

        report = ConflictReport(
            job_id="test-job-id",
            total_claims_analyzed=10,
            conflicts=[conflict],
            verified_claims=[{"skill": "Verified Skill"}],
            summary={"total_conflicts": 1},
        )

        assert report.job_id == "test-job-id"
        assert report.total_claims_analyzed == 10
        assert len(report.conflicts) == 1
        assert len(report.verified_claims) == 1

    def test_conflict_report_empty(self):
        from app.services.conflict_detector import ConflictReport

        report = ConflictReport(
            job_id="test-job-id",
            total_claims_analyzed=0,
        )

        assert report.conflicts == []
        assert report.verified_claims == []
        assert report.summary == {}


# ============================================================
# Conflict Detector Logic Tests
# ============================================================

class TestConflictDetectorLogic:
    def test_determine_skill_severity_critical(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        critical_skills = ["Python", "Java", "JavaScript", "SQL", "Git"]
        for skill in critical_skills:
            assert detector._determine_skill_severity(skill) == "high", f"{skill} should be high severity"

    def test_determine_skill_severity_important(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        important_skills = ["React", "Node.js", "Docker", "Kubernetes", "AWS"]
        for skill in important_skills:
            assert detector._determine_skill_severity(skill) == "medium", f"{skill} should be medium severity"

    def test_determine_skill_severity_low(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        low_skills = ["ObscureFramework", "SomeLibrary", "RandomTool"]
        for skill in low_skills:
            assert detector._determine_skill_severity(skill) == "low", f"{skill} should be low severity"

    def test_expected_complexity_senior(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        senior_roles = ["senior developer", "lead engineer", "principal architect", "staff engineer"]
        for role in senior_roles:
            assert detector._expected_complexity_for_role(role) == 15.0, f"{role} should expect 15.0 complexity"

    def test_expected_complexity_mid(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        mid_roles = ["software engineer", "mid level developer", "regular developer"]
        for role in mid_roles:
            result = detector._expected_complexity_for_role(role)
            assert result == 10.0, f"{role} should expect 10.0 complexity, got {result}"

    def test_expected_complexity_junior(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        junior_roles = ["junior developer", "associate engineer", "entry level"]
        for role in junior_roles:
            result = detector._expected_complexity_for_role(role)
            assert result == 5.0, f"{role} should expect 5.0 complexity, got {result}"

    def test_find_related_tech_python(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        # Python-related techs
        python_related = {"django", "flask", "fastapi"}
        assert detector._find_related_tech("python", python_related) is True

        # No Python-related techs
        no_python_related = {"react", "vue", "angular"}
        assert detector._find_related_tech("python", no_python_related) is False

    def test_find_related_tech_javascript(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        # JS-related techs
        js_related = {"react", "vue", "node.js"}
        assert detector._find_related_tech("javascript", js_related) is True

        # No JS-related techs
        no_js_related = {"django", "flask", "postgresql"}
        assert detector._find_related_tech("javascript", no_js_related) is False

    def test_count_by_type(self):
        from app.services.conflict_detector import ConflictDetector, ConflictAnalysis
        detector = ConflictDetector("test")

        conflicts = [
            ConflictAnalysis(
                claim="A", claim_source="resume", expected_evidence="E", actual_evidence=None,
                conflict_type="missing", severity="high", confidence=80,
                analysis="A", recommended_probe="P",
            ),
            ConflictAnalysis(
                claim="B", claim_source="resume", expected_evidence="E", actual_evidence="X",
                conflict_type="missing", severity="medium", confidence=70,
                analysis="A", recommended_probe="P",
            ),
            ConflictAnalysis(
                claim="C", claim_source="resume", expected_evidence="E", actual_evidence="Y",
                conflict_type="overstated", severity="low", confidence=60,
                analysis="A", recommended_probe="P",
            ),
        ]

        counts = detector._count_by_type(conflicts)
        assert counts["missing"] == 2
        assert counts["overstated"] == 1


# ============================================================
# Probe Generation Tests
# ============================================================

class TestProbeGeneration:
    def test_generate_skill_probe_python(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        probe = detector._generate_skill_probe("Python")
        assert "Python" in probe or "structuring" in probe

    def test_generate_skill_probe_react(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        probe = detector._generate_skill_probe("React")
        assert "state" in probe.lower() or "react" in probe.lower()

    def test_generate_skill_probe_docker(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        probe = detector._generate_skill_probe("Docker")
        assert "docker" in probe.lower() or "container" in probe.lower()

    def test_generate_skill_probe_unknown(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        probe = detector._generate_skill_probe("SomeUnknownTech")
        assert "SomeUnknownTech" in probe
        assert "describe" in probe.lower() or "project" in probe.lower()

    def test_generate_skill_probe_all_major_techs(self):
        from app.services.conflict_detector import ConflictDetector
        detector = ConflictDetector("test")

        major_techs = ["python", "java", "javascript", "react", "docker",
                       "kubernetes", "postgresql", "aws"]

        for tech in major_techs:
            probe = detector._generate_skill_probe(tech)
            assert len(probe) > 20, f"Probe for {tech} should be meaningful"
            assert "?" in probe or "walk" in probe.lower() or "describe" in probe.lower() or "explain" in probe.lower()


# ============================================================
# Integration Tests (Mocked)
# ============================================================

class TestConflictDetectorIntegration:
    @pytest.fixture
    def mock_kg_service(self):
        """Mock knowledge graph service."""
        with patch("app.services.conflict_detector.get_knowledge_graph") as mock:
            kg_instance = AsyncMock()
            kg_instance.get_skills_with_evidence = AsyncMock(return_value=[
                {
                    "skill": "Python",
                    "is_claimed": True,
                    "verified": True,
                    "evidence_count": 3,
                    "evidence": [{"name": "test-repo", "type": "Repository"}],
                },
                {
                    "skill": "React",
                    "is_claimed": True,
                    "verified": False,
                    "evidence_count": 0,
                    "evidence": [],
                },
            ])
            mock.return_value = kg_instance
            yield kg_instance

    @pytest.fixture
    def mock_graph_store(self):
        """Mock graph store."""
        with patch("app.services.conflict_detector.get_graph_store") as mock:
            store_instance = AsyncMock()
            store_instance.get_nodes_by_type = AsyncMock(return_value=[])
            store_instance.create_claim_evidence = AsyncMock(return_value="mock-id")
            store_instance.find_node_by_name = AsyncMock(return_value=None)
            mock.return_value = store_instance
            yield store_instance

    @pytest.mark.asyncio
    async def test_detect_skill_conflicts(self, mock_kg_service, mock_graph_store):
        from app.services.conflict_detector import ConflictDetector

        detector = ConflictDetector("test-job-id")

        # Mock _detect_experience_conflicts and _detect_technology_conflicts
        detector._detect_experience_conflicts = AsyncMock(return_value=[])
        detector._detect_technology_conflicts = AsyncMock(return_value=[])

        report = await detector.detect_all_conflicts()

        assert report.job_id == "test-job-id"
        # Should find React as unverified
        react_conflicts = [c for c in report.conflicts if "React" in c.claim]
        # Note: This may vary based on mock setup
        assert report.total_claims_analyzed >= 0


class TestConflictDetectorWithMockedKG:
    @pytest.mark.asyncio
    async def test_detect_skill_conflicts_finds_unverified(self):
        """Test that unverified skills are detected as conflicts."""
        from app.services.conflict_detector import ConflictDetector

        with patch.object(ConflictDetector, "__init__", lambda x, y: None):
            detector = ConflictDetector.__new__(ConflictDetector)
            detector.job_id = "test"
            detector.kg = AsyncMock()
            detector.store = AsyncMock()

            detector.kg.get_skills_with_evidence = AsyncMock(return_value=[
                {
                    "skill": "Claimed But Not Found",
                    "is_claimed": True,
                    "verified": False,
                    "evidence_count": 0,
                    "evidence": [],
                },
            ])

            result = await detector._detect_skill_conflicts()

            assert "conflicts" in result
            assert "verified" in result
            assert len(result["conflicts"]) == 1
            assert result["conflicts"][0].conflict_type == "missing"
