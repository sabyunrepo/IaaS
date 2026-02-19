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
Logo: Navy + Orange 건축물 (Building Tomorrow)
Primary: Navy #1B3A5C — 신뢰, 전문성, 안정
Accent:  Orange #E87E24 — 에너지, 행동, 강조
```

---

## 1. 토큰 아키텍처 (2-Tier)

### Tier 1: Scale Token (raw value)

> Tailwind v4 `@theme`에서 정의. 직접 사용 **비권장** — Semantic Token 우선.

```css
/* Navy palette */
--color-navy-50 ~ --color-navy-950

/* Brand Orange palette */
--color-brand-50 ~ --color-brand-950
```

**Tailwind 사용**: `bg-navy-800`, `text-brand-500` (Scale 직접 참조)

### Tier 2: Semantic Token (intent-based)

> **항상 이것을 먼저 사용**. 다크모드, 테마 전환 시 자동 대응.

| Semantic Token | Light 값 | 용도 |
|---------------|----------|------|
| `--color-bg-primary` | navy-50 (#f0f4f8) | 페이지 배경 |
| `--color-bg-surface` | white | 카드/섹션 배경 |
| `--color-bg-surface-hover` | navy-100 (#d9e2ec) | 카드 호버 |
| `--color-bg-accent` | brand-500 (#E87E24) | CTA 버튼 배경 |
| `--color-bg-accent-hover` | brand-600 (#cc6a17) | CTA 호버 |
| `--color-bg-brand` | navy-800 (#1B3A5C) | 네비게이션, 헤더 |
| `--color-bg-brand-hover` | navy-700 (#1f4060) | 네비 호버 |
| `--color-bg-neutral` | navy-100 (#d9e2ec) | 비활성 배경 |
| `--color-bg-danger` | red-50 | 에러 배경 |
| `--color-bg-success` | green-50 | 성공 배경 |
| `--color-text-primary` | navy-900 (#142d47) | 본문 텍스트 |
| `--color-text-secondary` | navy-600 (#2d5577) | 보조 텍스트 |
| `--color-text-tertiary` | navy-400 (#6d8eab) | 플레이스홀더, 힌트 |
| `--color-text-on-accent` | white | CTA 버튼 위 텍스트 |
| `--color-text-on-brand` | white | 네비게이션 텍스트 |
| `--color-text-accent` | brand-600 (#cc6a17) | 강조 텍스트, 링크 |
| `--color-text-danger` | red-600 | 에러 메시지 |
| `--color-text-success` | green-600 | 성공 메시지 |
| `--color-border-default` | navy-200 (#bcccdc) | 기본 테두리 |
| `--color-border-strong` | navy-400 (#6d8eab) | 강조 테두리 |
| `--color-border-accent` | brand-500 (#E87E24) | 포커스/활성 테두리 |

---

## 2. 절대 규칙 (Mandatory Rules)

### MUST
1. **모든 색상은 Semantic Token 변수명으로 작성**. Hex/RGB 하드코딩 금지.
   - `bg-[--color-bg-surface]` (O)
   - `bg-white` (X) → `bg-[--color-bg-surface]` 사용
   - `text-[#1B3A5C]` (X) → `text-[--color-text-primary]` 사용
2. **Semantic Token이 없는 경우에만 Scale Token 허용** (navy-*, brand-*).
3. **CTA(Call To Action) 버튼은 반드시 brand-accent** 사용.
4. **네비게이션/헤더는 반드시 navy-brand** 사용.
5. **포커스 링: `ring-[--color-border-accent]`** (Orange).

### MUST NOT
1. Tailwind 기본 팔레트(blue-500, orange-400) 사용 금지 — 항상 navy-*, brand-* 사용.
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
// Primary CTA
<button className="bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover] text-[--color-text-on-accent] px-6 py-3 rounded-lg font-medium transition-colors">
  지원하기
</button>

// Secondary
<button className="bg-[--color-bg-surface] hover:bg-[--color-bg-surface-hover] text-[--color-text-primary] border border-[--color-border-default] px-6 py-3 rounded-lg font-medium transition-colors">
  취소
</button>

// Brand (nav action)
<button className="bg-[--color-bg-brand] hover:bg-[--color-bg-brand-hover] text-[--color-text-on-brand] px-6 py-3 rounded-lg font-medium transition-colors">
  로그인
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
  className="w-full px-4 py-3 bg-[--color-bg-surface] border border-[--color-border-default] rounded-lg text-[--color-text-primary] placeholder:text-[--color-text-tertiary] focus:border-[--color-border-accent] focus:ring-2 focus:ring-[--color-border-accent]/20 transition-colors"
  placeholder="이메일을 입력하세요"
/>
```

---

## 6. 검증 (Audit) 체크리스트

코드 작성 후 반드시 다음을 검증:

- [ ] Hex/RGB 하드코딩 없음 (index.css @theme 제외)
- [ ] Tailwind 기본 색상(blue, green, red 등) 직접 사용 없음 — Semantic Token으로 대체
- [ ] CTA 버튼에 `--color-bg-accent` 사용 확인
- [ ] 네비게이션에 `--color-bg-brand` 사용 확인
- [ ] 포커스 스타일에 `--color-border-accent` 사용 확인
- [ ] 텍스트에 `--color-text-primary/secondary/tertiary` 사용 확인
- [ ] 반응형 간격 (모바일: p-4, 데스크톱: p-6~8)
- [ ] `prefers-reduced-motion` 대응

---

## 7. 파일 참조

| 파일 | 역할 |
|------|------|
| `frontend/packages/ui/src/styles/tokens.css` | Scale + Semantic 토큰 정의 |
| `frontend/packages/ui/src/styles/index.css` | Tailwind @import + 토큰 사용 |
| `frontend/packages/ui/tailwind.config.ts` | 토큰을 Tailwind에 매핑 |
