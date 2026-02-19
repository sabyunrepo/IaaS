---
title: "SonarQube — Docker Profile On-Demand 분석"
type: component
status: draft
created: 2026-02-19
updated: 2026-02-19
tags: [sonarqube, quality, tech-debt, code-smell, security, docker, infrastructure]
parent: "[[complexity-analysis/MOC]]"
children: []
depends-on: []
affects:
  - "[[application/nodes/quality-scanner-worker]]"
linear: [JIT-96]
phase: 2
---

# SonarQube — Docker Profile On-Demand 분析

## 개요

SonarQube는 기술부채(Technical Debt), 코드스멜(Code Smell), 보안 취약점(Security Hotspot)을
탐지하는 정적 분석 도구다.
QualityScannerWorker(W8)가 분석 요청 시에만 Docker Profile로 컨테이너를 기동하여
소나 스캔을 실행하고, REST API로 결과를 수집한 뒤 컨테이너를 종료한다.

## 상세 설계

### 핵심 개념

| 항목 | 설명 |
|------|------|
| On-Demand Profile | 분석 시에만 `sonarqube` Docker Compose profile 활성화 |
| Project Key | 분석 대상 레포를 식별하는 고유 키 (`{job_id}_{repo_name}`) |
| Quality Gate | 분석 통과 기준 (메트릭 임계값 집합) |
| Issue | 코드스멜/버그/취약점 한 건 |
| Technical Debt | 모든 Issue 수정에 필요한 예상 시간 합계 |

### Docker Compose Profile 설정

```yaml
# docker-compose.yml (sonarqube profile 발췌)
services:
  sonarqube:
    image: sonarqube:10-community
    profiles:
      - sonarqube          # 기본 up 시 비활성화. On-Demand만 활성화
    ports:
      - "9000:9000"
    environment:
      SONAR_JDBC_URL: "jdbc:postgresql://db:5432/sonarqube"
      SONAR_JDBC_USERNAME: sonar
      SONAR_JDBC_PASSWORD: sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_logs:/opt/sonarqube/logs
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/api/system/status"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  sonarqube_data:
  sonarqube_logs:
```

### SonarQube 어댑터

```python
# infrastructure/analysis/sonarqube_adapter.py
import asyncio
import httpx
from pathlib import Path


class SonarQubeAdapter:
    """SonarQube REST API 어댑터.

    On-Demand 패턴:
        1. Docker Compose profile 'sonarqube' 기동
        2. sonar-scanner CLI 실행 (프로젝트 분석)
        3. REST API로 분석 결과 조회
        4. 컨테이너 종료
    """

    def __init__(
        self,
        sonar_url: str = "http://localhost:9000",
        sonar_token: str = "",
    ):
        self.sonar_url = sonar_url
        self.token = sonar_token
        self._auth = (sonar_token, "")  # Basic Auth: token as username

    async def wait_for_ready(self, timeout_seconds: int = 120) -> None:
        """SonarQube 서버 준비 완료 대기 (healthcheck 폴링)."""
        deadline = asyncio.get_event_loop().time() + timeout_seconds
        async with httpx.AsyncClient() as client:
            while asyncio.get_event_loop().time() < deadline:
                try:
                    response = await client.get(
                        f"{self.sonar_url}/api/system/status",
                        auth=self._auth,
                        timeout=5,
                    )
                    data = response.json()
                    if data.get("status") == "UP":
                        return
                except (httpx.ConnectError, httpx.TimeoutException):
                    pass
                await asyncio.sleep(5)
        raise TimeoutError("SonarQube did not become ready in time")

    async def run_scan(self, repo_path: str, project_key: str) -> None:
        """sonar-scanner CLI로 레포 분석 실행.

        Args:
            repo_path: 클론된 레포 로컬 경로
            project_key: SonarQube 프로젝트 식별자 (e.g. "job123_myrepo")
        """
        sonar_properties = Path(repo_path) / "sonar-project.properties"
        sonar_properties.write_text(
            f"sonar.projectKey={project_key}\n"
            f"sonar.sources=.\n"
            f"sonar.host.url={self.sonar_url}\n"
            f"sonar.token={self.token}\n"
            f"sonar.scm.disabled=true\n"
        )

        proc = await asyncio.create_subprocess_exec(
            "sonar-scanner",
            "-Dproject.settings=" + str(sonar_properties),
            cwd=repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"sonar-scanner failed (code {proc.returncode}): "
                f"{stderr.decode()}"
            )

    async def get_issues(
        self,
        project_key: str,
        severities: list[str] | None = None,
        types: list[str] | None = None,
    ) -> list[dict]:
        """프로젝트의 Issue 목록 조회.

        Args:
            severities: ["BLOCKER", "CRITICAL", "MAJOR", "MINOR", "INFO"]
            types: ["BUG", "VULNERABILITY", "CODE_SMELL", "SECURITY_HOTSPOT"]
        """
        params: dict = {
            "projectKeys": project_key,
            "ps": 500,  # 페이지 크기 최대
        }
        if severities:
            params["severities"] = ",".join(severities)
        if types:
            params["types"] = ",".join(types)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.sonar_url}/api/issues/search",
                params=params,
                auth=self._auth,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        return [
            {
                "key": issue["key"],
                "type": issue["type"],
                "severity": issue["severity"],
                "message": issue["message"],
                "component": issue.get("component", ""),
                "line": issue.get("line"),
                "effort": issue.get("effort", "0min"),  # 수정 예상 시간
                "debt": issue.get("debt", "0min"),
            }
            for issue in data.get("issues", [])
        ]

    async def get_metrics(self, project_key: str) -> dict:
        """프로젝트 수준 집계 메트릭 조회.

        Returns:
            {
                "bugs": int,
                "vulnerabilities": int,
                "code_smells": int,
                "security_hotspots": int,
                "coverage": float,
                "duplicated_lines_density": float,
                "sqale_index": int,  # 기술부채 총합 (분 단위)
                "sqale_debt_ratio": float,  # 부채 비율 (%)
            }
        """
        metric_keys = [
            "bugs",
            "vulnerabilities",
            "code_smells",
            "security_hotspots",
            "coverage",
            "duplicated_lines_density",
            "sqale_index",
            "sqale_debt_ratio",
        ]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.sonar_url}/api/measures/component",
                params={
                    "component": project_key,
                    "metricKeys": ",".join(metric_keys),
                },
                auth=self._auth,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

        measures = {
            m["metric"]: m.get("value", "0")
            for m in data.get("component", {}).get("measures", [])
        }

        return {
            "bugs": int(measures.get("bugs", 0)),
            "vulnerabilities": int(measures.get("vulnerabilities", 0)),
            "code_smells": int(measures.get("code_smells", 0)),
            "security_hotspots": int(measures.get("security_hotspots", 0)),
            "coverage": float(measures.get("coverage", 0)),
            "duplicated_lines_density": float(
                measures.get("duplicated_lines_density", 0)
            ),
            "sqale_index": int(measures.get("sqale_index", 0)),  # 분
            "sqale_debt_ratio": float(measures.get("sqale_debt_ratio", 0)),
        }
```

### QualityScannerWorker(W8) 통합 — On-Demand 패턴

```python
# application/nodes/quality_scanner_worker.py (발췌)
import asyncio
import subprocess
from infrastructure.analysis.sonarqube_adapter import SonarQubeAdapter


SONAR_TOKEN = "sqa_..."  # 환경변수로 주입
sonar_adapter = SonarQubeAdapter(sonar_token=SONAR_TOKEN)


async def quality_scanner_worker(state: dict) -> dict:
    """W8: SonarQube On-Demand 분석.

    패턴:
        1. sonarqube Docker profile 기동
        2. ready 대기
        3. 스캔 실행
        4. 결과 조회
        5. 컨테이너 종료
    """
    job_id = state["job_id"]
    repo_name = state["repo_name"]
    clone_dir = state["clone_dir"]
    project_key = f"{job_id}_{repo_name}"

    try:
        # Step 1: sonarqube profile 기동
        subprocess.run(
            ["docker", "compose", "--profile", "sonarqube", "up", "-d", "sonarqube"],
            check=True,
        )

        # Step 2: 서버 준비 대기
        await sonar_adapter.wait_for_ready(timeout_seconds=120)

        # Step 3: 스캔 실행
        await sonar_adapter.run_scan(clone_dir, project_key)

        # Step 4: 결과 조회
        metrics = await sonar_adapter.get_metrics(project_key)
        critical_issues = await sonar_adapter.get_issues(
            project_key,
            severities=["BLOCKER", "CRITICAL"],
            types=["BUG", "VULNERABILITY"],
        )
        code_smells = await sonar_adapter.get_issues(
            project_key,
            types=["CODE_SMELL"],
        )

        quality_report = {
            "metrics": metrics,
            "critical_issues": critical_issues[:20],  # 상위 20건
            "code_smells_count": len(code_smells),
            "tech_debt_minutes": metrics["sqale_index"],
        }

    finally:
        # Step 5: 컨테이너 종료 (항상 실행)
        subprocess.run(
            ["docker", "compose", "--profile", "sonarqube", "stop", "sonarqube"],
            check=False,  # 실패해도 계속 진행
        )

    return {"quality_report": quality_report}
```

### pyproject.toml 의존성

```toml
httpx = ">=0.27.0"
# sonar-scanner CLI는 Docker 이미지 내 포함 또는 호스트에 설치
```

## 관련 문서

- 상위: [[complexity-analysis/MOC]]
- 함께 사용: [[complexity-analysis/radon]], [[complexity-analysis/lizard]]
- 설계 원본: `plan/v5-design/phase2-infrastructure.md` §9.1 W8
