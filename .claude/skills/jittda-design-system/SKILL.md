---
name: jittda-design-system
description: Jittda Design System Context Injection. UI 컴포넌트 생성/수정 시 디자인 토큰 규칙을 강제 적용. Seed Design(당근마켓) 2-tier 토큰 구조 기반.
triggers:
  - UI, component, 컴포넌트
  - Tailwind, 스타일, color, 색상
  - design system, 디자인 시스템
  - Button, Card, Input, Modal
---

# Jittda Design System — Context Injection Skill

> Seed Design(당근마켓) 2-tier 토큰 아키텍처를 Jittda 브랜드에 맞게 적용.
> 이 스킬이 로딩되면, 모든 UI 코드는 아래 규칙을 **절대 규칙(Design Bible)**으로 따른다.

## Brand Identity

```
Logo: Emerald + Teal 그라데이션 (Building Tomorrow)
Primary: Emerald #2db882 — 신뢰, 성장, 안정
Accent:  Teal #2dd4bf — 그라데이션 파트너, 보조 액센트
Neutral: Ink (cool blue-gray) — 텍스트, 보더, 배경
Warning: Amber — 경고, 우려사항 (brand-* 대신 amber-* 사용)
```

---

## 1. 토큰 아키텍처 (2-Tier)

### Tier 1: Scale Token (raw value)

> Tailwind v4 `@theme`에서 정의. 직접 사용 **비권장** — Semantic Token 우선.

```css
/* Emerald palette (primary accent) */
--color-em-50 ~ --color-em-950

/* Ink palette (cool neutral / blue-gray) */
--color-ink-50 ~ --color-ink-950

/* Teal (gradient partner) */
--color-teal-400, --color-teal-500
```

**Tailwind 사용**: `bg-em-500`, `text-ink-600` (Scale 직접 참조)

### Tier 2: Semantic Token (intent-based)

> **항상 이것을 먼저 사용**. 다크모드, 테마 전환 시 자동 대응.

| Semantic Token | Light 값 | 용도 |
|---------------|----------|------|
| `--color-bg-page` | ink-50 (#f5f7fa) | 페이지 배경 |
| `--color-bg-surface` | white | 카드/섹션 배경 |
| `--color-bg-surface-hover` | em-50 (#f0fdf8) | 카드 호버 |
| `--color-bg-accent` | em-500 (#2db882) | CTA 버튼 배경 |
| `--color-bg-accent-hover` | em-600 (#1f9a6a) | CTA 호버 |
| `--color-bg-accent-subtle` | em-50 (#f0fdf8) | 강조 배경 (연한) |
| `--color-bg-neutral` | ink-100 (#e8ecf2) | 비활성 배경 |
| `--color-text-primary` | ink-900 (#0f1e2e) | 제목/라벨 |
| `--color-text-secondary` | ink-600 (#344f6b) | 본문 텍스트 |
| `--color-text-tertiary` | ink-400 (#7089a8) | 힌트/캡션 |
| `--color-text-on-accent` | white | CTA 버튼 위 텍스트 |
| `--color-text-accent` | em-600 (#1f9a6a) | 링크/강조 텍스트 |
| `--color-text-accent-strong` | em-700 (#167a52) | 강한 강조 |
| `--color-border-default` | ink-200 (#ccd4e0) | 기본 테두리 |
| `--color-border-subtle` | ink-100 (#e8ecf2) | 연한 테두리 |
| `--color-border-accent` | em-500 (#2db882) | 포커스/활성 테두리 |

**상태 색상 (변경 안 함)**:
- Red: error/danger (`bg-red-50`, `text-red-600`)
- Green: success (`bg-green-50`, `text-green-600`)
- Blue: LinkedIn 브랜드 (`bg-blue-50`, `text-blue-700`)
- Amber: warning/concern (`bg-amber-50`, `text-amber-800`)

---

## 2. 절대 규칙 (Mandatory Rules)

### MUST
1. **모든 색상은 Semantic Token 변수명으로 작성**. Hex/RGB 하드코딩 금지.
   - `bg-[--color-bg-surface]` (O)
   - `bg-white` (X) → `bg-[--color-bg-surface]` 사용
   - `text-[#2db882]` (X) → `text-[--color-text-accent]` 사용
2. **Semantic Token이 없는 경우에만 Scale Token 허용** (em-*, ink-*).
3. **CTA(Call To Action) 버튼은 반드시 `--color-bg-accent`** 사용 + glow 효과.
4. **헤더 그라데이션: `from-em-500 to-teal-500`** 또는 `from-em-600 to-teal-500`.
5. **포커스 링: `ring-[--color-border-accent]`** (Emerald).

### MUST NOT
1. ~~navy-*~~, ~~brand-*~~ 사용 금지 — `em-*`, `ink-*`, `amber-*` 사용.
2. 임의 색상 변수 생성 금지 — 토큰 테이블에 없으면 추가 요청.
3. `!important` 금지 (접근성 오버라이드 제외).

---

## 3. 타이포그래피

| Role | Size | Weight | 용도 |
|------|------|--------|------|
| `text-display` | 2.25rem (36px) | Bold 700 | 히어로 제목 |
| `text-h1` | 1.875rem (30px) | Semibold 600 | 페이지 제목 |
| `text-h2` | 1.5rem (24px) | Semibold 600 | 섹션 제목 |
| `text-h3` | 1.25rem (20px) | Medium 500 | 카드 제목 |
| `text-body-lg` | 1.125rem (18px) | Regular 400 | 큰 본문 |
| `text-body` | 1rem (16px) | Regular 400 | 기본 본문 |
| `text-body-sm` | 0.875rem (14px) | Regular 400 | 보조 텍스트 |
| `text-caption` | 0.75rem (12px) | Regular 400 | 캡션, 라벨 |

**Font Stack**: `'Pretendard Variable', Pretendard, -apple-system, system-ui, sans-serif`

---

## 4. 간격(Spacing) 시스템

| Token | Value | 용도 |
|-------|-------|------|
| `--space-1` | 0.25rem (4px) | 아이콘-텍스트 간격 |
| `--space-2` | 0.5rem (8px) | 인라인 요소 간격 |
| `--space-3` | 0.75rem (12px) | 컴팩트 패딩 |
| `--space-4` | 1rem (16px) | 기본 패딩/마진 |
| `--space-5` | 1.25rem (20px) | 카드 패딩 |
| `--space-6` | 1.5rem (24px) | 섹션 간격 |
| `--space-8` | 2rem (32px) | 큰 섹션 간격 |
| `--space-10` | 2.5rem (40px) | 페이지 패딩 |
| `--space-12` | 3rem (48px) | 히어로 간격 |
| `--space-16` | 4rem (64px) | 섹션 구분 |

---

## 5. 컴포넌트 패턴

### Button

```tsx
// Primary CTA (with glow on hover)
<button className="bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover] text-[--color-text-on-accent] px-6 py-3 rounded-lg font-medium transition-all hover:shadow-[0_0_20px_-5px_hsl(160_60%_45%/0.2)]">
  지원하기
</button>

// Secondary
<button className="bg-[--color-bg-surface] hover:bg-[--color-bg-surface-hover] text-[--color-text-secondary] border border-[--color-border-default] px-6 py-3 rounded-lg font-medium transition-colors">
  취소
</button>

// Disabled
<button className="bg-ink-300 text-white px-6 py-3 rounded-lg font-medium cursor-not-allowed" disabled>
  제출 중...
</button>
```

### Card

```tsx
<div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card hover:shadow-card-hover p-5 transition-all">
  <h3 className="text-[--color-text-primary] text-h3">카드 제목</h3>
  <p className="text-[--color-text-secondary] text-body mt-2">설명</p>
</div>
```

### Input

```tsx
<input
  className="w-full px-4 py-3 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:border-[--color-border-accent] focus:ring-2 focus:ring-em-500/20 transition-colors"
  placeholder="이메일을 입력하세요"
/>
```

### Header Gradient

```tsx
<div className="bg-gradient-to-r from-em-500 to-teal-500 rounded-xl p-6 text-white">
  <h2 className="text-xl font-bold">후보자 분석</h2>
</div>
```

### Glass Effect (Navbar/Modal)

```tsx
// Navbar
<nav className="bg-white/80 backdrop-blur-lg border-b border-[--color-border-default]/50">

// Modal overlay
<div className="bg-ink-950/60 backdrop-blur-sm">
```

---

## 6. 검증 (Audit) 체크리스트

코드 작성 후 반드시 다음을 검증:

- [ ] Hex/RGB 하드코딩 없음 (index.css @theme 제외)
- [ ] ~~navy-*~~, ~~brand-*~~ 사용 없음 — `em-*`, `ink-*` 사용
- [ ] CTA 버튼에 `--color-bg-accent` + glow 효과 사용 확인
- [ ] 헤더에 `from-em-500 to-teal-500` 그라데이션 확인
- [ ] 포커스 스타일에 `--color-border-accent` 사용 확인
- [ ] 텍스트에 `--color-text-primary/secondary/tertiary` 사용 확인
- [ ] 경고에 `amber-*` 사용 확인 (brand-* 금지)
- [ ] 반응형 간격 (모바일: p-4, 데스크톱: p-6~8)
- [ ] `prefers-reduced-motion` 대응

---

## 7. 파일 참조

| 파일 | 역할 |
|------|------|
| `frontend/src/index.css` | @theme Scale Token + :root Semantic Token 정의 |
| `frontend/seed-design.json` | Seed Design CLI 설정 |
| `frontend/seed-design/ui/` | Seed Design CLI 생성 컴포넌트 스니펫 |
| `frontend/vite.config.ts` | Seed Design Vite 플러그인 + Tailwind v4 |
| `frontend/tsconfig.app.json` | seed-design 경로 별칭 |
