"""
SonarQube Adapter — REST API 연동.

SonarQube 서버의 REST API를 호출하여 프로젝트의 기술부채, 코드스멜,
보안 취약점 등 품질 리포트를 가져온다.
"""
from dataclasses import dataclass, field

import httpx

from infrastructure.resilience.circuit_breaker import CircuitBreaker, CircuitOpenError


@dataclass(frozen=True)
class QualityIssue:
    """SonarQube 이슈 하나."""

    key: str
    rule: str
    severity: str  # BLOCKER | CRITICAL | MAJOR | MINOR | INFO
    component: str
    message: str
    type: str  # BUG | VULNERABILITY | CODE_SMELL


@dataclass(frozen=True)
class QualityReport:
    """SonarQube 프로젝트 품질 리포트."""

    project_key: str
    bugs: int = 0
    vulnerabilities: int = 0
    code_smells: int = 0
    coverage: float = 0.0
    duplicated_lines_density: float = 0.0
    technical_debt_minutes: int = 0
    security_hotspots: int = 0
    reliability_rating: str = "A"  # A~E
    security_rating: str = "A"
    issues: list[QualityIssue] = field(default_factory=list)


class SonarQubeAdapter:
    """SonarQube REST API 클라이언트."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        circuit_breaker: CircuitBreaker | None = None,
    ):
        """
        Args:
            base_url: SonarQube 서버 URL (예: http://localhost:9000).
            token: SonarQube API 토큰.
            timeout: HTTP 요청 타임아웃(초).
            circuit_breaker: Circuit breaker 인스턴스 (없으면 직접 호출).
        """
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._cb = circuit_breaker

    async def get_quality_report(self, project_key: str) -> QualityReport:
        """프로젝트의 품질 리포트를 가져온다.

        Args:
            project_key: SonarQube 프로젝트 키.

        Returns:
            QualityReport.

        Raises:
            ValueError: 프로젝트가 존재하지 않을 때.
            RuntimeError: API 호출 실패 시.
            CircuitOpenError: Circuit breaker가 Open 상태일 때.
        """
        if self._cb:
            return await self._cb.call(self._get_quality_report_impl, project_key)
        return await self._get_quality_report_impl(project_key)

    async def _get_quality_report_impl(self, project_key: str) -> QualityReport:
        measures = await self._fetch_measures(
            project_key,
            metric_keys=[
                "bugs",
                "vulnerabilities",
                "code_smells",
                "coverage",
                "duplicated_lines_density",
                "sqale_index",
                "security_hotspots",
                "reliability_rating",
                "security_rating",
            ],
        )

        issues = await self._fetch_issues(project_key, page_size=100)

        return QualityReport(
            project_key=project_key,
            bugs=int(measures.get("bugs", 0)),
            vulnerabilities=int(measures.get("vulnerabilities", 0)),
            code_smells=int(measures.get("code_smells", 0)),
            coverage=float(measures.get("coverage", 0.0)),
            duplicated_lines_density=float(
                measures.get("duplicated_lines_density", 0.0)
            ),
            technical_debt_minutes=int(measures.get("sqale_index", 0)),
            security_hotspots=int(measures.get("security_hotspots", 0)),
            reliability_rating=_rating_value(measures.get("reliability_rating", "1")),
            security_rating=_rating_value(measures.get("security_rating", "1")),
            issues=issues,
        )

    async def _fetch_measures(
        self, project_key: str, *, metric_keys: list[str]
    ) -> dict[str, str]:
        """프로젝트 메트릭을 가져온다."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/api/measures/component",
                params={
                    "component": project_key,
                    "metricKeys": ",".join(metric_keys),
                },
                auth=(self._token, ""),
            )

            if response.status_code == 404:
                raise ValueError(f"Project not found: {project_key}")
            response.raise_for_status()

            data = response.json()
            measures_list = data.get("component", {}).get("measures", [])
            return {m["metric"]: m["value"] for m in measures_list}

    async def _fetch_issues(
        self, project_key: str, *, page_size: int = 100
    ) -> list[QualityIssue]:
        """프로젝트의 오픈 이슈를 가져온다."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(
                f"{self._base_url}/api/issues/search",
                params={
                    "componentKeys": project_key,
                    "statuses": "OPEN,CONFIRMED,REOPENED",
                    "ps": str(page_size),
                },
                auth=(self._token, ""),
            )

            if response.status_code == 404:
                return []
            response.raise_for_status()

            data = response.json()
            return [
                QualityIssue(
                    key=issue["key"],
                    rule=issue["rule"],
                    severity=issue.get("severity", "INFO"),
                    component=issue.get("component", ""),
                    message=issue.get("message", ""),
                    type=issue.get("type", "CODE_SMELL"),
                )
                for issue in data.get("issues", [])
            ]


def _rating_value(raw: str) -> str:
    """SonarQube 숫자 등급 → 문자 등급."""
    mapping = {"1": "A", "1.0": "A", "2": "B", "2.0": "B", "3": "C", "3.0": "C",
               "4": "D", "4.0": "D", "5": "E", "5.0": "E"}
    return mapping.get(raw, "A")
