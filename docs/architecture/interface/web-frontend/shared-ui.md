---
title: "Shared UI (@jittda/ui)"
type: component
layer: interface
parent: "[[interface/web-frontend/MOC]]"
status: active
created: 2026-02-19
tags: [interface, frontend, design-system, ui]
---

# Shared UI (@jittda/ui)

> Public App과 Admin App이 공유하는 디자인 시스템.

## 컴포넌트 목록

### 기본 요소
| 컴포넌트 | 설명 |
|---------|------|
| Button | Primary/Secondary/Ghost 변형 |
| Input | 텍스트, 이메일, URL 입력 |
| Textarea | 멀티라인 입력 (JD 등) |
| Select | 드롭다운 선택 |
| Checkbox | 체크박스 (동의 등) |
| Badge | 상태 배지 (pending, analyzing, completed) |

### 복합 요소
| 컴포넌트 | 설명 |
|---------|------|
| Card | 범용 카드 컨테이너 |
| Modal | 모달 다이얼로그 |
| FileUpload | 파일 업로드 (drag & drop, PDF/DOC 제한) |
| Toast | 알림 토스트 |
| Table | 정렬/필터 가능한 테이블 |
| Pagination | 페이지네이션 |
| Tabs | 탭 네비게이션 |
| SkillTag | 기술 스택 태그 (추가/삭제) |

### 레이아웃
| 컴포넌트 | 설명 |
|---------|------|
| PublicLayout | 지원자 앱 레이아웃 (CompanyHeader + Footer) |
| AdminLayout | 관리자 앱 레이아웃 (Sidebar + Header + Content) |

## Hooks

| Hook | 설명 |
|------|------|
| useForm | 폼 상태 관리 + 유효성 검증 |
| useFileUpload | 파일 업로드 진행률 + 에러 처리 |
| useToast | 토스트 알림 관리 |

## 스타일 가이드

- **Tailwind 4 프리셋**: 공통 색상, 타이포그래피, 간격 토큰
- **테마 확장 구조**: CSS Variables로 회사별 테마 오버라이드 가능
- **반응형**: 모바일 퍼스트 (sm/md/lg 브레이크포인트)
- **접근성**: WCAG 2.1 AA 준수 (키보드, 스크린리더)
