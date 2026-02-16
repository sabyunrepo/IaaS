ttda Sniper v5.0 구현 계획"**에 대한 정밀 리뷰입니다.

설계의 방향성은 올바르나, '마이그레이션(이주)'이라는 단어가 주는 착시가 여전히 계획서 곳곳에 남아 있습니다. 우리는 기존 집을 리모델링하는 것이 아니라, 옆 부지에 새로운 집(Clean Slate)을 짓고 필요한 가구만 골라서 옮기는 것입니다.

이 관점에서 수정된 리뷰와 실행 가이드를 제시합니다.

Jittda Sniper v5.0 구현 계획 리뷰 보고서
1. 총평 (Executive Summary)
"마이그레이션(Migration)이 아닌 재건축(Reconstruction)입니다. 용어와 접근법을 수정하십시오."

제시된 계획은 LangGraph 도입과 DDD 적용, 포렌식 로직 강화 등 핵심 요구사항을 잘 반영하고 있습니다. 그러나 '기존 코드 제거', 'DB 마이그레이션' 같은 표현은 여전히 레거시 코드베이스 위에서 작업한다는 인상을 줍니다.

Jittda v5.0은 jittda/라는 완전히 새로운 디렉토리에서 시작해야 합니다. Temporal을 '제거'하는 것이 아니라, 처음부터 설치하지 않는 것입니다. 이 접근 방식의 차이가 프로젝트의 청결도(Cleanliness)를 결정합니다.

2. 주요 비판 및 개선 권고 (Critical Analysis)
2.1 접근 방식: 'Clean Slate' 원칙 위배
🔴 문제점:

계획서의 Phase 4에 "Temporal 제거" 단계가 포함됨.

Phase 0.3에 004_langgraph_migration.py 등 기존 DB 히스토리를 잇는 마이그레이션 스크립트 언급.

✅ 개선 권고:

Phase 4 삭제: 새 프로젝트 폴더(jittda/)에는 Temporal 코드가 애초에 존재하지 않아야 합니다.

Fresh Init SQL: 기존 DB 마이그레이션 히스토리(Alembic revisions)를 가져오지 마십시오. v5.0에 맞는 최적화된 스키마를 정의한 init.sql 하나로 DB를 초기화하십시오.

Legacy Reference: 기존 Vantict 코드는 참조용 라이브러리(Read-only)로만 취급하고, 필요한 로직만 발췌하여 v5 구조에 맞게 재작성(Rewrite) 하십시오.

2.2 인프라 및 환경 구성
🔴 문제점:

Makefile 및 환경 설정에 대한 구체성이 부족함.

로컬 개발 환경과 배포 환경의 일관성 보장 방안 미비.

✅ 개선 권고:

Cloudflare Tunnel 필수: ngrok이나 포트 포워딩 없이 보안 터널을 통해 외부(Webhook, Frontend)와 통신하도록 docker-compose에 cloudflared 서비스를 고정하십시오.

Makefile 표준화: make up, make infra-clean (볼륨까지 삭제 후 재시작) 등 개발 수명주기를 관리할 명령어를 명시하십시오.

2.3 DDD 아키텍처의 엄격함
🔴 문제점:

infrastructure 계층의 코드가 domain 로직을 침범할 우려가 있음 (예: Git 실행 결과 파싱 로직이 Infra에 있는지 Domain에 있는지 모호).

✅ 개선 권고:

의존성 규칙 준수: domain은 infrastructure를 절대 import 해선 안 됩니다. infrastructure가 domain 모델을 리턴하도록 구현하십시오.

Interface Layer 명시: api/routes는 application이 아니라 interface/api (Web/HTTP 어댑터) 계층으로 명확히 분리하십시오.

3. 레거시 자산 선별 가이드 (Selective Porting)
기존 프로젝트(Vantict)에서 Jittda로 가져올 것과 버릴 것을 명확히 정의합니다. **"파일 복사 붙여넣기 금지, 로직 이식 허용"**이 원칙입니다.

3.1 [Asset] 핵심 로직 (Port Logic, Rewrite Code)
비즈니스 로직은 가져오되, DDD/Pydantic 스타일에 맞춰 새로 짭니다.

점수 산출 공식 (scoring_formulas.py):

조치: 로직 100% 유지. 단, 함수형 스타일에서 domain/scoring/calculator.py 클래스 구조로 변경.

프롬프트 (prompts/*.yaml):

조치: infrastructure/llm/prompts/로 이동. LangChain/Instructor 포맷({variable}) 호환성 검증 후 저장.

JD 분석 및 매칭 로직:

조치: 기존의 키워드 매칭 로직을 domain/matching/funnel.py로 이식하되, 벡터 검색 로직과 결합.

3.2 [Reference] 참조 대상 (Read Only)
아이디어만 가져오고 코드는 완전히 새로 짭니다.

Git 분석 (services/git.py):

조치: 기존의 단순 clone 로직은 폐기. 'Identity Resolution' (Mailmap + Blame -w -M -C) 파이프라인으로 재구현.

LLM 클라이언트 (utils/llm_cache.py):

조치: Redis 캐싱 아이디어만 참조. 구현은 infrastructure/llm/client.py에 데코레이터 패턴으로 깔끔하게 재작성.

3.3 [Liability] 폐기 대상 (Do Not Copy)
새 프로젝트에 절대 포함시키지 않습니다.

Temporal 관련 모든 코드: workflows/, activities/, worker.py.

기존 DB 마이그레이션 스크립트: alembic/versions/*.py.

SVG 차트 컴포넌트: D3.js로 전면 교체.

구형 정규식 파서: Instructor(Structured Output)로 대체되므로 폐기.
