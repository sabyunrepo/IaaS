---
title: "Three-Layer Questions"
type: component
layer: application
status: draft
created: 2026-02-19
updated: 2026-02-19
parent: "[[application/live-session/MOC]]"
depends-on:
  - "[[application/live-session/pre-interview-graph]]"
  - "[[application/live-session/live-engine]]"
affects: []
linear: JTL-61, JTL-62, JTL-77
tags: [question-deck, realtime-probing, layer-1, layer-2, interview-guide]
---

# Three-Layer Questions

> 면접관 보조 질문 시스템은 2계층으로 구성된다. Layer 1(Question Deck)은 면접 전 사전 생성된 깊이 있는 질문이고, Layer 2(Real-time Probing)는 대화 맥락에 따라 동적 생성되는 실시간 질문이다.

## 계층 구조

```
+---------------------------------------------------------+
|           Layer 1: Question Deck (사전 생성)               |
|                                                         |
|  면접 시작 전, v5.0 KG 분석 결과 기반으로                  |
|  주제별 질문 카드 미리 생성 (서버, Kimi K2.5)              |
|  -> 클라이언트에 동기화 -> 즉시 사용 가능                  |
|                                                         |
|  특징: 깊이 있는 분석, 모순점 사전 발굴, 0ms 지연          |
+---------------------------------------------------------+
|           Layer 2: Real-time Probing (실시간 보조)        |
|                                                         |
|  면접 대화 흐름에 따라 동적 생성 (클라이언트, Groq)         |
|  -> Deck에 없는 꼬리질문, 새로운 모순점, 맥락 기반 심화     |
|                                                         |
|  특징: 대화 맥락 반영, 예측 불가 상황 대응                  |
+---------------------------------------------------------+
```

## Layer 1 vs Layer 2 비교

| 항목 | Layer 1: Question Deck | Layer 2: Real-time Probing |
|------|----------------------|---------------------------|
| **생성 시점** | 면접 전 (v5.0 분석 완료 후) | 면접 중 (발화 분석 시) |
| **생성 위치** | 서버 (Kimi K2.5) | 클라이언트 (Groq) |
| **데이터 기반** | KG 그래프 도구 + 사전 분석 전체 | 실시간 발화 + 로컬 RAG |
| **질문 깊이** | 깊음 (시간 여유, 전체 맥락) | 상황 적응적 (실시간 압박) |
| **지연 시간** | 0ms (미리 준비됨) | ~700ms (Groq TTFT) |
| **LLM 토큰** | 사전 1회 소비 | 트리거 시에만 소비 |
| **면접 시작 즉시** | 주제별 질문 이미 준비됨 | 질문 없음 (발화 대기) |
| **네트워크 장애 시** | Deck으로 면접 진행 가능 | 질문 생성 불가 |

## Layer 1: Question Deck 상세

### Deck 구성

| 그룹 | 설명 | 수량 |
|------|------|------|
| Ice Breakers | 경력 기반 자연스러운 오프닝 질문 | 1-2개 |
| Topic Groups | JD 요구사항별 질문 묶음 | 5-8개 그룹, 그룹당 2-3개 질문 |
| Red Flags | 모순/위험 신호 기반 검증 질문 | 별도 분리 |

### Deck 생성 프로세스

```
v5.0 분석 완료 -> KG 완성
        |
        v
DeckGenerator (서버, Kimi K2.5 + Graph Tools)
  1. get_jd_coverage() -> 미검증 역량 목록
  2. find_contradictions() -> 모순점 목록
  3. get_unverified_topics() -> 미확인 주장 목록

  주제별로 그래프 도구 호출하며 질문 생성:
    for topic in jd_requirements:
      evidence = get_skill_evidence(topic.skill)
      cards = llm.generate_questions(topic, evidence, depth="deep")

  모순점 -> red_flags 카드 별도 생성
  오프닝 -> ice_breakers 생성
        |
        v
Question Deck DB 저장 -> 클라이언트 동기화
```

## Layer 2: Real-time Probing 상세

### 트리거 발동 조건

| 트리거 | 상황 | 예시 |
|--------|------|------|
| **모순 감지** | 지원자 발화가 Deck/KG와 충돌 | "혼자 다 했다" vs 이력서 "팀 프로젝트" |
| **예상 외 주제** | Deck에 없는 기술/경험 언급 | Deck에 없는 "Kafka" 언급 -> 심화 질문 |
| **꼬리 질문** | Deck 질문 사용 후 답변이 불충분 | 답변이 모호 -> 구체적 수치 요구 |

### 실시간 분석 흐름

```
지원자 발화 완료 (stt:final)
        |
        v
RealTimeAnalyzer:
  1. 발화 내용 vs Deck 주제 매칭
     -> 매칭되면 Deck 카드 자동 활성화
  2. 트리거 조건 체크
     -> 모순 감지? 예상 외 주제?
     -> 트리거 없으면 -> 생성 안 함 (LLM 미호출)
  3. 트리거 있을 때만
     -> Groq LLM 호출 (실시간)
     -> 새 카드 생성 -> UI 푸시
```

## UI에서의 2계층 표현

```
+--------------------------------------+
| Zone B: 질문 카드 영역                 |
|                                      |
|  [실시간 -- 모순 발견]           NOW  |
| +----------------------------------+ |
| | "혼자 구축" 발언 vs 팀 프로젝트    | |
| | Q. "캐시 무효화 전략은?"          | |
| | [사용함]  [다른 질문]             | |
| +----------------------------------+ |
|                      ^ Layer 2       |
|  - - - - - - - - - - - - - - - - -  |
|                      v Layer 1       |
|  MSA 분산 환경                [미검증] |
| +----------------------------------+ |
| | Q1. "서비스 분리 기준은?"         | |
| | 의도: MSA 설계 원칙              | |
| | [사용함]  [다음 질문]             | |
| +----------------------------------+ |
|                                      |
|  캐싱 / Redis               [약함]  |
|  ...                                 |
+--------------------------------------+
```

### UI 동작 규칙

| 규칙 | 설명 |
|------|------|
| Layer 2(실시간)는 항상 **최상단** | 긴급도가 높으므로 시선 우선 |
| Layer 1(Deck)은 **주제별 접이식** | 현재 대화 주제와 매칭되는 그룹 자동 펼침 |
| `사용함` 누르면 | 해당 카드 반투명 + 커버리지 반영 |
| `다음 질문` | 같은 주제의 다음 Deck 질문으로 이동 |
| `다른 질문` | Layer 2 실시간 재생성 (같은 의도, 다른 각도) |
| 대화 주제 변경 감지 시 | 해당 주제 그룹 자동 펼침 + 스크롤 |

## 성능 목표

| 지표 | 목표 | 설명 |
|------|------|------|
| Layer 1 표시 지연 | 0ms | 사전 동기화 완료 |
| Layer 2 생성 지연 | < 700ms | Groq TTFT 0.14초 + 로컬 RAG < 100ms |
| Hybrid RAG 검색 | < 100ms | LanceDB + graphology 로컬 |
| KG 그래프 쿼리 | < 5ms | graphology In-memory |

## 관련 문서

- [[live-session/pre-interview-graph]] -- Layer 1 Deck 생성 (Phase 1)
- [[live-session/live-engine]] -- Layer 2 실시간 생성 (Phase 2)
- [[live-session/post-interview-graph]] -- 사용된 카드 기반 평가 (Phase 3)
