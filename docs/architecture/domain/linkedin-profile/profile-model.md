---
title: "LinkedIn Profile Model"
type: component
layer: domain
parent: "[[domain/linkedin-profile/MOC]]"
status: draft
created: 2026-02-19
updated: 2026-02-19
linear: ["JIT-124"]
depends-on: ["[[infrastructure/linkedin-adapter/MOC]]"]
---

# LinkedIn Profile Model

## 목적

LinkedIn에서 수집한 프로필 데이터를 **순수 도메인 Pydantic 모델로 구조화**한다. BrightData API 호출과 HTML/JSON 파싱은 Infrastructure 레이어(JIT-125)가 담당하며, 이 모델은 파싱된 데이터의 구조와 유효성만 책임진다.

## 모델 계층 구조

```
LinkedInProfile
  ├── experiences: list[LinkedInExperience]
  ├── educations:  list[LinkedInEducation]
  ├── skills:      list[LinkedInSkill]
  └── certifications: list[LinkedInCertification]
```

## Pydantic 모델 전체 정의

```python
# domain/identity/linkedin_models.py
from pydantic import BaseModel, Field, ConfigDict


class LinkedInExperience(BaseModel):
    model_config = ConfigDict(strict=True)

    company: str
    title: str
    duration_months: int = Field(ge=0)
    start_date: str | None = None       # "YYYY-MM" 형식
    end_date: str | None = None         # None = 현재 재직
    description: str = ""
    location: str | None = None
    is_current: bool = False


class LinkedInEducation(BaseModel):
    model_config = ConfigDict(strict=True)

    school: str
    degree: str | None = None           # "학사", "석사" 등
    field_of_study: str | None = None
    start_year: int | None = None
    end_year: int | None = None


class LinkedInSkill(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    endorsement_count: int = Field(ge=0, default=0)


class LinkedInCertification(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    issuer: str
    issue_date: str | None = None       # "YYYY-MM"
    credential_url: str | None = None


class LinkedInProfile(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    headline: str | None = None          # "Senior Backend Engineer at ..."
    location: str | None = None
    summary: str = ""
    profile_url: str

    experiences: list[LinkedInExperience] = []
    educations: list[LinkedInEducation] = []
    skills: list[LinkedInSkill] = []
    certifications: list[LinkedInCertification] = []

    @property
    def total_experience_months(self) -> int:
        """전체 경력 월수 합산"""
        return sum(e.duration_months for e in self.experiences)

    @property
    def current_company(self) -> str | None:
        """현재 재직 회사 (is_current=True인 경험 중 첫 번째)"""
        current = [e for e in self.experiences if e.is_current]
        return current[0].company if current else None
```

## 필드 정의

### LinkedInProfile (루트 모델)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | `str` | 필수 | 프로필 표시 이름 |
| `headline` | `str \| None` | 선택 | 직책/소속 한 줄 요약 (예: "Senior Backend Engineer at ...") |
| `location` | `str \| None` | 선택 | 거주/근무 위치 |
| `summary` | `str` | 기본값 `""` | About 섹션 자기소개 |
| `profile_url` | `str` | 필수 | LinkedIn 프로필 URL |
| `experiences` | `list[LinkedInExperience]` | 기본값 `[]` | 경력 목록 |
| `educations` | `list[LinkedInEducation]` | 기본값 `[]` | 학력 목록 |
| `skills` | `list[LinkedInSkill]` | 기본값 `[]` | 스킬 목록 |
| `certifications` | `list[LinkedInCertification]` | 기본값 `[]` | 자격증 목록 |

### LinkedInExperience (경력)

| 필드 | 타입 | 설명 |
|------|------|------|
| `company` | `str` | 회사명 |
| `title` | `str` | 직책 |
| `duration_months` | `int (ge=0)` | 재직 기간 (월 단위, 0 이상) |
| `start_date` | `str \| None` | 시작일 "YYYY-MM" 형식 |
| `end_date` | `str \| None` | 종료일 "YYYY-MM", None = 현재 재직 |
| `description` | `str` | 담당 업무 설명 |
| `location` | `str \| None` | 근무 위치 |
| `is_current` | `bool` | 현재 재직 여부 |

### LinkedInEducation (학력)

| 필드 | 타입 | 설명 |
|------|------|------|
| `school` | `str` | 학교명 |
| `degree` | `str \| None` | 학위 ("학사", "석사", "박사" 등) |
| `field_of_study` | `str \| None` | 전공 |
| `start_year` | `int \| None` | 입학 연도 |
| `end_year` | `int \| None` | 졸업 연도 |

### LinkedInSkill (스킬)

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | `str` | 스킬명 |
| `endorsement_count` | `int (ge=0)` | 추천 수 (기본값 0) |

### LinkedInCertification (자격증)

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | `str` | 자격증명 |
| `issuer` | `str` | 발급 기관 |
| `issue_date` | `str \| None` | 발급일 "YYYY-MM" |
| `credential_url` | `str \| None` | 자격증 URL |

## 프로필 정규화 함수

BrightData에서 수집한 raw JSON/HTML을 `LinkedInProfile` 모델로 변환하는 정규화 함수다.

```python
# domain/identity/linkedin_normalizer.py

def normalize_linkedin_profile(raw_data: dict) -> LinkedInProfile:
    """BrightData에서 수집한 raw JSON/HTML → 구조화 모델 변환"""
    experiences = [
        LinkedInExperience(
            company=exp.get("company", ""),
            title=exp.get("title", ""),
            duration_months=_calc_duration(exp.get("start"), exp.get("end")),
            start_date=exp.get("start"),
            end_date=exp.get("end"),
            description=exp.get("description", ""),
            location=exp.get("location"),
            is_current=exp.get("end") is None,
        )
        for exp in raw_data.get("experiences", [])
    ]
    educations = [
        LinkedInEducation(
            school=edu.get("school", ""),
            degree=edu.get("degree"),
            field_of_study=edu.get("field_of_study"),
            start_year=edu.get("start_year"),
            end_year=edu.get("end_year"),
        )
        for edu in raw_data.get("educations", [])
    ]
    skills = [
        LinkedInSkill(
            name=skill.get("name", ""),
            endorsement_count=skill.get("endorsement_count", 0),
        )
        for skill in raw_data.get("skills", [])
    ]
    certifications = [
        LinkedInCertification(
            name=cert.get("name", ""),
            issuer=cert.get("issuer", ""),
            issue_date=cert.get("issue_date"),
            credential_url=cert.get("credential_url"),
        )
        for cert in raw_data.get("certifications", [])
    ]
    return LinkedInProfile(
        name=raw_data["name"],
        headline=raw_data.get("headline"),
        location=raw_data.get("location"),
        summary=raw_data.get("summary", ""),
        profile_url=raw_data["url"],
        experiences=experiences,
        educations=educations,
        skills=skills,
        certifications=certifications,
    )


def _calc_duration(start: str | None, end: str | None) -> int:
    """재직 기간 월수 계산. end=None이면 현재 날짜 기준."""
    from datetime import date
    if not start:
        return 0
    start_date = date.fromisoformat(start + "-01")
    end_date = date.today() if end is None else date.fromisoformat(end + "-01")
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
```

## 테스트 케이스

| 테스트 | 검증 내용 |
|--------|-----------|
| `test_linkedin_profile_creation` | 전체 필드 모델 생성 (경력, 학력, 스킬, 자격증 포함) |
| `test_total_experience_months` | `total_experience_months` 프로퍼티 합산 정확성 |
| `test_current_company` | `current_company` 프로퍼티 — `is_current=True`인 경험 추출 |
| `test_empty_profile` | 경력/스킬 없는 최소 프로필 생성 (필수 필드만) |
| `test_normalize_raw_data` | raw dict → `LinkedInProfile` 변환 정확성 |

## 의존성

- BrightData 스크레이핑 및 파싱: [[infrastructure/linkedin-adapter/MOC]] (JIT-125)
- `SkillAssessment` 모델과의 연동: `experiences.title` + `skills.name`이 기술스택 평가에 사용됨
