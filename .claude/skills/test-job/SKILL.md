---
name: test-job
description: 테스트 잡 생성 및 모니터링. test job, 잡 생성, 잡 실행, 테스트 실행 관련 작업 시 사용.
argument-hint: [옵션] — 예: "CTO/VP ko", "시니어 en", "기본" (기본=CTO/VP ko)
allowed-tools: Bash, Read
---

# Test Job Skill

테스트 잡을 생성하고 모니터링합니다.

## 사용법

```
/test-job                    # 기본 설정(CTO/VP, ko)으로 잡 생성
/test-job 시니어 en          # 시니어 레벨, 영어 출력
/test-job monitor JOB_ID     # 기존 잡 모니터링
```

## 실행 절차

### Step 1: JWT 토큰 생성

```bash
docker compose exec backend python -c "
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings
payload = {
    'sub': '53797d83-cb85-4bf3-8959-51650ec3cb44',
    'email': 'hoone0802@gmail.com',
    'plan': 'free',
    'exp': datetime.now(timezone.utc) + timedelta(days=1),
    'iat': datetime.now(timezone.utc),
}
print(jwt.encode(payload, settings.JWT_SECRET, algorithm='HS256'))
" 2>/dev/null | tail -1
```

### Step 2: 포트폴리오 업로드 (선택)

```bash
JWT_TOKEN="<Step1 결과>"
curl -s -X POST "http://localhost:8000/api/v1/upload/portfolio" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@/Users/sabyun/goinfre/IaaS/backend/potpolio.pdf" | python3 -m json.tool
```

### Step 3: 잡 생성

```bash
curl -s -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "jd_text": "<JD_TEXT>",
      "experience_level": "<LEVEL>",
      "output_language": "<LANG>",
      "linkedin_url": "https://www.linkedin.com/in/byun-sanghoon-303918338/",
      "git_url": "https://github.com/sabyunrepo",
      "portfolio_path": "<업로드 경로 또는 생략>"
    }
  }' | python3 -m json.tool
```

### Step 4: 모니터링

```bash
# 워커 로그 실시간
docker compose logs worker -f --tail=20

# DB 잡 상태 확인
docker compose exec backend python -c "
import asyncio
from app.core.database import get_session
from app.models.database import JobDB
from sqlalchemy import select
async def check(job_id):
    async for s in get_session():
        r = await s.execute(select(JobDB).where(JobDB.id == job_id))
        j = r.scalar_one_or_none()
        if j: print(f'Status: {j.status}, Updated: {j.updated_at}')
asyncio.run(check('JOB_ID'))
" 2>/dev/null | tail -1

# Temporal UI
open http://localhost:8233
```

## 기본 테스트 데이터

| 항목 | 값 |
|------|-----|
| 유저 ID | `53797d83-cb85-4bf3-8959-51650ec3cb44` |
| 이메일 | hoone0802@gmail.com |
| 레벨 | CTO/VP |
| 출력언어 | ko |
| LinkedIn | https://www.linkedin.com/in/byun-sanghoon-303918338/ |
| GitHub | https://github.com/sabyunrepo |
| 포트폴리오 | `backend/potpolio.pdf` |

## 기본 JD 텍스트

```
주요업무
• AI 활용 서비스 개발 : 기존 AI 서비스 고도화 및 LLM을 활용한 신규 AI 서비스를 직접 개발하고, 프롬프트 엔지니어링 및 성능 최적화를 책임집니다.
• AI 모델 백엔드 구축 및 애플리케이션 연동 : AI 모델을 상용 애플리케이션과 효율적으로 연동하고 AI 서비스의 백엔드 아키텍처를 설계하며 안정적인 운영과 지속적인 개선을 담당합니다.
• 제공 기술 및 서비스 문서화 : 개발된 AI 기술과 서비스에 대한 명확하고 상세한 문서를 작성하여, 전사 조직에 지식 공유를 활성화하고 효율적인 협업을 지원합니다.
자격요건
• 관련 경력 3년 이상 또는 그에 준하는 뛰어난 역량을 갖추신 분
• LLM API 활용 경험이 있거나, 생성형 AI 서비스를 개발해 본 경험이 있는 분
• AI 모델 백엔드 구축 경험이 있으며, AI 기술을 실제 상용 서비스에 적용한 경험이 있는 분
• Python 과 Typescript 를 활용한 API 개발 및 대규모 데이터 처리 로직 구현에 능숙하신 분
우대사항
• AI 모델 Fine-tuning 경험이 있거나, 사전 학습된 모델을 특정 도메인에 최적화한 경험이 있으신 분
• 대규모 AI 서비스 운영 경험이 있으며, AI 서비스의 안정성과 성능을 극대화한 경험이 있으신 분
• AI 성능 최적화 경험이 있거나, 추론 속도와 비용 효율성을 개선한 경험이 있으신 분
• 새로운 기술 트렌드에 대한 깊은 관심과 함께, 신기술 도입 및 적용에 적극적으로 참여하고자 하는 열정이 있으신 분
• 대규모 AI 서비스 및 트래픽을 안정적으로 처리할 수 있는 아키텍처를 설계하고 운영해 본 경험이 있으신 분
• 제공하는 서비스에 대한 적극적인 기술 가이드 제공 경험이 있거나, 이를 통해 동료들의 성장을 돕는 것을 좋아하시는 분
• 개발 과정에서의 문서화의 중요성을 이해하고, 명확하고 체계적인 문서 작성을 통해 지식 공유와 협업에 기여할 수 있는 분
```

## 경험 레벨 옵션

| 값 | 설명 |
|-----|------|
| `신입` | Entry level |
| `주니어` | Junior (1-3년) |
| `미들` | Mid-level (3-5년) |
| `시니어` | Senior (5-10년) |
| `CTO/VP` | Executive level |

## 자동화 원칙

1. JWT 토큰은 매번 새로 생성 (만료 24시간)
2. 포트폴리오 업로드 후 반환된 `file_path`를 잡 생성에 사용
3. 잡 생성 후 `job_id`를 기록
4. 워커 로그로 진행 상황 모니터링
5. 완료 후 DB에서 `final_output` 확인
