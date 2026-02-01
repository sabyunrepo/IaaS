# Planner Agent Skill

> 실행 계획 수립 에이전트

---

## 역할

입력 데이터를 분석하고, 전체 워크플로우의 실행 계획을 수립합니다.

## 책임

1. **입력 검증**: 필수 데이터 존재 여부, 형식 유효성 확인
2. **워크로드 추정**: GitHub API로 분석 대상 규모 파악
3. **실행 계획 생성**: 어떤 분석을 어떤 순서로 실행할지 결정
4. **리소스 할당**: 예상 소요 시간 및 우선순위 설정

---

## Activity 정의

### create_execution_plan

```python
@activity.defn
async def create_execution_plan(job_id: str, input_data: dict) -> dict:
    """
    실행 계획 수립

    Input:
        job_id: 작업 ID
        input_data: {
            resume_path: str | None,
            portfolio_path: str | None,
            github_urls: list[str],
            jd_text: str,
            experience_level: str,
            language_config: dict,
        }

    Output:
        {
            job_id: str,
            phases: [
                {name: "document_analysis", enabled: bool, priority: int},
                {name: "code_analysis", enabled: bool, priority: int},
                {name: "jd_analysis", enabled: bool, priority: int},
            ],
            workload: {
                "https://github.com/...": {
                    total_files: int,
                    python_files: int,
                    estimated_time_seconds: int,
                }
            },
            estimated_total_time_seconds: int,
        }
    """
```

---

## 입력 검증 규칙

```python
VALIDATION_RULES = {
    "jd_text": {
        "required": True,
        "min_length": 50,
        "error": "채용공고는 최소 50자 이상이어야 합니다",
    },
    "github_urls": {
        "required": False,
        "format": "github_url",
        "max_count": 5,
        "error": "유효한 GitHub URL이어야 합니다 (최대 5개)",
    },
    "experience_level": {
        "required": True,
        "allowed": ["신입", "주니어", "미들", "시니어"],
        "error": "경험 레벨은 신입/주니어/미들/시니어 중 하나여야 합니다",
    },
    "resume_path": {
        "required": False,
        "format": "s3_path",
        "extensions": [".pdf"],
    },
    "portfolio_path": {
        "required": False,
        "format": "s3_path",
        "extensions": [".pdf", ".docx"],
    },
}
```

---

## GitHub 워크로드 추정 로직

```python
async def estimate_github_workload(url: str) -> dict:
    """
    GitHub API를 사용하여 레포지토리 워크로드 추정

    사용 API:
    - GET /repos/{owner}/{repo} - 기본 정보
    - GET /repos/{owner}/{repo}/languages - 언어 비율
    - GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1 - 파일 목록
    """
    github = GitHubService()

    # 기본 정보
    repo_info = await github.get_repo_info(url)

    # Python 비율
    languages = await github.get_languages(url)
    python_ratio = languages.get("Python", 0) / sum(languages.values()) if languages else 0

    # 파일 수 추정 (tree API)
    tree = await github.get_tree(url)
    python_files = [f for f in tree["tree"] if f["path"].endswith(".py")]

    # 시간 추정 (파일당 약 2초)
    estimated_time = len(python_files) * 2

    return {
        "repo_name": repo_info["name"],
        "total_files": len(tree["tree"]),
        "python_files": len(python_files),
        "python_ratio": python_ratio,
        "estimated_time_seconds": min(estimated_time, 300),  # 최대 5분
        "last_commit": repo_info.get("pushed_at"),
    }
```

---

## 실행 계획 전략

### Phase 우선순위 결정

```python
def determine_phase_priority(input_data: dict) -> list[dict]:
    """
    입력 데이터에 따른 Phase 우선순위 결정

    규칙:
    1. JD 분석은 항상 실행 (기본)
    2. GitHub URL이 있으면 코드 분석이 가장 중요
    3. 문서가 있으면 문서 분석 추가
    4. 모든 분석은 병렬 실행 가능
    """
    phases = []

    # JD 분석 (필수, 가장 빠름)
    phases.append({
        "name": "jd_analysis",
        "enabled": True,
        "priority": 1,
        "estimated_time": 30,
    })

    # 문서 분석
    has_documents = input_data.get("resume_path") or input_data.get("portfolio_path")
    if has_documents:
        phases.append({
            "name": "document_analysis",
            "enabled": True,
            "priority": 2,
            "estimated_time": 60,
        })

    # 코드 분석 (가장 오래 걸림, 가장 중요)
    if input_data.get("github_urls"):
        phases.append({
            "name": "code_analysis",
            "enabled": True,
            "priority": 3,
            "estimated_time": 180,  # 기본값, 실제는 workload에서 계산
        })

    return phases
```

---

## 에러 처리

```python
class PlanningError(Exception):
    """계획 수립 중 에러"""
    pass

class ValidationError(PlanningError):
    """입력 검증 에러 (재시도 불필요)"""
    pass

class GitHubAPIError(PlanningError):
    """GitHub API 에러 (재시도 가능)"""
    pass

# 에러 처리 예시
async def create_execution_plan(job_id: str, input_data: dict) -> dict:
    try:
        # 입력 검증
        validate_input(input_data)
    except ValidationError as e:
        # 재시도해도 안 됨 - 사용자 입력 오류
        raise

    try:
        # GitHub API 호출
        workload = await estimate_workload(input_data)
    except GitHubAPIError as e:
        # 재시도 가능 - Rate Limit 등
        raise

    return build_plan(input_data, workload)
```

---

## 출력 예시

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "phases": [
    {
      "name": "jd_analysis",
      "enabled": true,
      "priority": 1,
      "estimated_time": 30
    },
    {
      "name": "document_analysis",
      "enabled": true,
      "priority": 2,
      "estimated_time": 45
    },
    {
      "name": "code_analysis",
      "enabled": true,
      "priority": 3,
      "estimated_time": 120
    }
  ],
  "workload": {
    "https://github.com/user/repo1": {
      "repo_name": "repo1",
      "total_files": 150,
      "python_files": 45,
      "python_ratio": 0.78,
      "estimated_time_seconds": 90,
      "last_commit": "2024-01-15T10:30:00Z"
    }
  },
  "estimated_total_time_seconds": 195,
  "parallel_execution": true
}
```

---

## 관련 파일

- `backend/app/workflows/activities/planning.py`
- `backend/app/services/github_service.py`
- `backend/app/models/job.py`

---

## 의존성

- **외부 서비스**: GitHub API
- **내부 서비스**: 없음 (첫 번째 Phase)
- **다음 Phase**: Document Analysis, Code Analysis, JD Analysis (병렬)
