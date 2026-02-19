"""
SonarQube Adapter 테스트 — REST API 연동 (mock 사용).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.analysis.sonarqube_adapter import (
    QualityIssue,
    QualityReport,
    SonarQubeAdapter,
    _rating_value,
)


class TestRatingValue:
    def test_numeric_to_letter(self):
        assert _rating_value("1") == "A"
        assert _rating_value("1.0") == "A"
        assert _rating_value("2") == "B"
        assert _rating_value("3") == "C"
        assert _rating_value("4") == "D"
        assert _rating_value("5") == "E"

    def test_unknown_defaults_to_a(self):
        assert _rating_value("unknown") == "A"
        assert _rating_value("") == "A"


class TestQualityReport:
    def test_default_values(self):
        report = QualityReport(project_key="test")
        assert report.bugs == 0
        assert report.vulnerabilities == 0
        assert report.code_smells == 0
        assert report.coverage == 0.0
        assert report.reliability_rating == "A"
        assert report.issues == []


class TestQualityIssue:
    def test_creation(self):
        issue = QualityIssue(
            key="AX123",
            rule="python:S1234",
            severity="MAJOR",
            component="src/main.py",
            message="Remove this unused import",
            type="CODE_SMELL",
        )
        assert issue.severity == "MAJOR"
        assert issue.type == "CODE_SMELL"


class TestSonarQubeAdapter:
    @pytest.mark.asyncio
    async def test_get_quality_report_success(self):
        adapter = SonarQubeAdapter(base_url="http://localhost:9000", token="test-token")

        measures_response = MagicMock()
        measures_response.status_code = 200
        measures_response.raise_for_status = MagicMock()
        measures_response.json.return_value = {
            "component": {
                "measures": [
                    {"metric": "bugs", "value": "3"},
                    {"metric": "vulnerabilities", "value": "1"},
                    {"metric": "code_smells", "value": "42"},
                    {"metric": "coverage", "value": "78.5"},
                    {"metric": "reliability_rating", "value": "2"},
                    {"metric": "security_rating", "value": "1"},
                ]
            }
        }

        issues_response = MagicMock()
        issues_response.status_code = 200
        issues_response.raise_for_status = MagicMock()
        issues_response.json.return_value = {
            "issues": [
                {
                    "key": "AX1",
                    "rule": "python:S1234",
                    "severity": "MAJOR",
                    "component": "src/main.py",
                    "message": "Fix this",
                    "type": "BUG",
                }
            ]
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[measures_response, issues_response])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("infrastructure.analysis.sonarqube_adapter.httpx.AsyncClient", return_value=mock_client):
            report = await adapter.get_quality_report("my-project")

        assert report.project_key == "my-project"
        assert report.bugs == 3
        assert report.vulnerabilities == 1
        assert report.code_smells == 42
        assert report.coverage == 78.5
        assert report.reliability_rating == "B"
        assert report.security_rating == "A"
        assert len(report.issues) == 1
        assert report.issues[0].type == "BUG"

    @pytest.mark.asyncio
    async def test_project_not_found(self):
        adapter = SonarQubeAdapter(base_url="http://localhost:9000", token="test-token")

        not_found_response = MagicMock()
        not_found_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=not_found_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("infrastructure.analysis.sonarqube_adapter.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(ValueError, match="Project not found"):
                await adapter.get_quality_report("nonexistent")
