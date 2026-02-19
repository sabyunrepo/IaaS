# Emerald Light Theme Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 데모 앱 전체를 Navy+Orange에서 Emerald+Teal 라이트 테마로 전환

**Architecture:** index.css에 2-tier 토큰(Scale + Semantic)을 정의하고, 모든 컴포넌트에서 시맨틱 변수로 참조. navy-*/brand-* 제거, em-*/ink-*/teal-* 도입.

**Tech Stack:** Tailwind CSS v4 (`@theme`), CSS custom properties, React TSX

**Design Doc:** `docs/plans/2026-02-20-emerald-light-theme-design.md`

---

### Task 1: Token System — `index.css` 전면 교체

**Files:**
- Modify: `frontend/src/index.css` (전체)

**Step 1: `@theme` 블록 교체**

기존 `@theme { ... }` 전체를 아래로 교체:

```css
@theme {
  /* Emerald palette (primary accent) — 랜딩 primary #2db882 기반 */
  --color-em-50:  #f0fdf8;
  --color-em-100: #ccfbe9;
  --color-em-200: #99f6d3;
  --color-em-300: #5eecb9;
  --color-em-400: #2fd990;
  --color-em-500: #2db882;
  --color-em-600: #1f9a6a;
  --color-em-700: #167a52;
  --color-em-800: #115c3d;
  --color-em-900: #0d3f2a;
  --color-em-950: #071f15;

  /* Ink palette (cool neutral / blue-gray) */
  --color-ink-50:  #f5f7fa;
  --color-ink-100: #e8ecf2;
  --color-ink-200: #ccd4e0;
  --color-ink-300: #a5b3c8;
  --color-ink-400: #7089a8;
  --color-ink-500: #4a6685;
  --color-ink-600: #344f6b;
  --color-ink-700: #253d55;
  --color-ink-800: #182c3f;
  --color-ink-900: #0f1e2e;
  --color-ink-950: #070d18;

  /* Teal (gradient partner) */
  --color-teal-400: #2dd4bf;
  --color-teal-500: #1aada0;

  /* Shadows — emerald-tinted */
  --shadow-card:       0 1px 3px 0 hsl(160 40% 20% / 0.07), 0 1px 2px -1px hsl(160 40% 20% / 0.05);
  --shadow-card-hover: 0 4px 12px -2px hsl(160 40% 20% / 0.12), 0 2px 6px -2px hsl(160 40% 20% / 0.07);
  --shadow-elevated:   0 10px 25px -5px hsl(160 40% 20% / 0.14), 0 8px 10px -6px hsl(160 40% 20% / 0.07);
}
```

**Step 2: `:root` 시맨틱 변수 추가**

`@theme` 바로 아래에 추가:

```css
:root {
  --color-bg-page: var(--color-ink-50);
  --color-bg-surface: #ffffff;
  --color-bg-surface-hover: var(--color-em-50);
  --color-bg-accent: var(--color-em-500);
  --color-bg-accent-hover: var(--color-em-600);
  --color-bg-accent-subtle: var(--color-em-50);
  --color-bg-neutral: var(--color-ink-100);
  --color-text-primary: var(--color-ink-900);
  --color-text-secondary: var(--color-ink-600);
  --color-text-tertiary: var(--color-ink-400);
  --color-text-on-accent: #ffffff;
  --color-text-accent: var(--color-em-600);
  --color-text-accent-strong: var(--color-em-700);
  --color-border-default: var(--color-ink-200);
  --color-border-subtle: var(--color-ink-100);
  --color-border-accent: var(--color-em-500);
}
```

**Step 3: 유틸리티 업데이트**

| 유틸리티 | Before | After |
|----------|--------|-------|
| `*:focus-visible` outline | `#1B3A5C` | `var(--color-border-accent)` |
| `.skip-link` background | `#1B3A5C` | `var(--color-bg-accent)` |
| `.tab-underline::after` gradient | `#1B3A5C, #E87E24` | `#2db882, #2dd4bf` |
| `.skeleton` gradient | `#f0f4f8, #d9e2ec` | `#f5f7fa, #e8ecf2` |
| scrollbar thumb | `#bcccdc` | `#ccd4e0` |
| scrollbar thumb hover | `#6d8eab` | `#7089a8` |
| print border fallback | `#d9e2ec` | `#ccd4e0` |

새 유틸리티 추가:

```css
.gradient-text-em {
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-image: linear-gradient(135deg, #2db882, #2dd4bf);
}

.glow-em-sm {
  box-shadow: 0 0 20px -5px hsl(160 60% 45% / 0.20);
}
```

**Step 4: 검증**

Run: `cd frontend && npx tsc --noEmit`
Expected: 타입 에러 없음 (CSS만 변경)

**Step 5: 커밋**

```bash
git add frontend/src/index.css
git commit -m "feat: index.css 에메랄드 라이트 토큰 시스템 교체"
```

---

### Task 2: Layout — `Layout.tsx` 배경색 교체

**Files:**
- Modify: `frontend/src/components/Layout.tsx:14`

**Step 1: 배경색 교체**

```
Before: bg-navy-50
After:  bg-[--color-bg-page]
```

**Step 2: 커밋**

```bash
git add frontend/src/components/Layout.tsx
git commit -m "feat: Layout 배경색 에메랄드 토큰으로 교체"
```

---

### Task 3: 단순 컴포넌트 — `SectionCard.tsx`

**Files:**
- Modify: `frontend/src/components/SectionCard.tsx`

**Step 1: 색상 클래스 교체 (3건)**

| Line | Before | After |
|------|--------|-------|
| 10 | `border-gray-200 bg-white` | `border-[--color-border-default] bg-[--color-bg-surface]` |
| 12 | `text-gray-900` | `text-[--color-text-primary]` |
| 16 | `text-gray-500` | `text-[--color-text-tertiary]` |

**Step 2: 커밋**

```bash
git add frontend/src/components/SectionCard.tsx
git commit -m "feat: SectionCard 에메랄드 토큰 적용"
```

---

### Task 4: `FileUploadField.tsx`

**Files:**
- Modify: `frontend/src/components/FileUploadField.tsx`

**Step 1: 색상 교체 (5건)**

| Line | Before | After |
|------|--------|-------|
| 27 | `text-gray-700` | `text-[--color-text-secondary]` |
| 47 | `border-gray-300 bg-gray-50` | `border-[--color-border-default] bg-[--color-bg-page]` |
| 47 | `hover:border-navy-600 hover:bg-navy-50/50` | `hover:border-[--color-border-accent] hover:bg-[--color-bg-surface-hover]` |
| 48 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 51 | `text-gray-600` | `text-[--color-text-secondary]` |
| 62 | `text-navy-700` | `text-[--color-text-accent-strong]` |

Green 상태 (29-35줄) 유지.

**Step 2: 커밋**

```bash
git add frontend/src/components/FileUploadField.tsx
git commit -m "feat: FileUploadField 에메랄드 토큰 적용"
```

---

### Task 5: `EmailNotificationModal.tsx`

**Files:**
- Modify: `frontend/src/components/EmailNotificationModal.tsx`

**Step 1: 색상 교체 (6건)**

| Line | Before | After |
|------|--------|-------|
| 12 | `bg-black/50` | `bg-ink-950/60 backdrop-blur-sm` |
| 13 | `bg-white` | `bg-[--color-bg-surface]` |
| 15 | `bg-navy-100` | `bg-em-100` |
| 16 | `text-navy-700` | `text-em-700` |
| 20 | `text-gray-900` | `text-[--color-text-primary]` |
| 23 | `text-gray-600` | `text-[--color-text-secondary]` |
| 30 | `text-gray-700 bg-gray-100 hover:bg-gray-200` | `text-[--color-text-secondary] bg-[--color-bg-neutral] hover:bg-ink-200` |
| 35 | `bg-navy-700 hover:bg-navy-800` | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover]` |

**Step 2: 커밋**

```bash
git add frontend/src/components/EmailNotificationModal.tsx
git commit -m "feat: EmailNotificationModal 에메랄드 토큰 적용"
```

---

### Task 6: `Navbar.tsx`

**Files:**
- Modify: `frontend/src/components/Navbar.tsx`

**Step 1: 색상 교체 (~12건)**

| Line | Before | After |
|------|--------|-------|
| 45 | `border-navy-100 bg-white/80` | `border-[--color-border-default]/50 bg-white/80` |
| 57 | `from-navy-800 to-brand-500` (logo gradient) | `from-em-700 to-teal-500` |
| 71 | `bg-navy-50 text-navy-800` (active nav) | `bg-em-50 text-em-700` |
| 72 | `text-gray-600 hover:bg-navy-50 hover:text-navy-700` | `text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover] hover:text-[--color-text-accent]` |
| 88 | `from-navy-800 to-navy-700 ... hover:from-navy-900 hover:to-navy-800` (CTA) | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover]` (no gradient) + `hover:shadow-[0_0_20px_-5px_hsl(160_60%_45%/0.2)]` |
| 100 | `hover:bg-navy-50` (avatar btn) | `hover:bg-[--color-bg-surface-hover]` |
| 108 | `ring-navy-100` (avatar ring) | `ring-em-200` |
| 111 | `from-navy-700 to-brand-500` (avatar gradient) | `from-em-500 to-teal-400` |
| 115 | `text-gray-400` (chevron) | `text-[--color-text-tertiary]` |
| 121 | `border-navy-100 bg-white` (dropdown) | `border-[--color-border-default] bg-white/90 backdrop-blur-md` |
| 122 | `border-navy-100` (dropdown dividers) | `border-[--color-border-subtle]` |
| 123 | `text-gray-900` (user name) | `text-[--color-text-primary]` |
| 124 | `text-gray-400` (role text) | `text-[--color-text-tertiary]` |
| 130 | `border-navy-100` (mobile nav border) | `border-[--color-border-subtle]` |
| 137 | `text-navy-800 bg-navy-50` / `text-gray-700 hover:bg-navy-50` (mobile nav) | `text-em-700 bg-em-50` / `text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]` |
| 146 | `text-brand-500 ... hover:bg-navy-50` (mobile create) | `text-[--color-text-accent] ... hover:bg-[--color-bg-surface-hover]` |
| 155 | `text-gray-700 hover:bg-navy-50` (settings) | `text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]` |
| 157 | `text-gray-400` (settings icon) | `text-[--color-text-tertiary]` |
| 169 | `text-gray-700 hover:bg-navy-50` (language) | `text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]` |
| 171 | `text-gray-400` (lang icon) | `text-[--color-text-tertiary]` |
| 177 | `border-navy-100` (logout divider) | `border-[--color-border-subtle]` |
| 198 | `from-navy-800 to-navy-700 ... hover:from-navy-900 hover:to-navy-800` (login btn) | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover]` |

**Step 2: 커밋**

```bash
git add frontend/src/components/Navbar.tsx
git commit -m "feat: Navbar 에메랄드 + glass 효과 적용"
```

---

### Task 7: `LoginPage.tsx`

**Files:**
- Modify: `frontend/src/pages/LoginPage.tsx`

**Step 1: 색상 교체 (~10건)**

| Line | Before | After |
|------|--------|-------|
| 59 | `border-gray-200 bg-white` | `border-[--color-border-default] bg-[--color-bg-surface]` |
| 63 | `text-gray-900` | `text-[--color-text-primary]` |
| 64 | `text-gray-600` | `text-[--color-text-secondary]` |
| 71 | `border-gray-300 ... text-gray-700 hover:border-gray-400 hover:bg-gray-50 focus:ring-navy-500` | `border-[--color-border-default] ... text-[--color-text-secondary] hover:border-ink-300 hover:bg-[--color-bg-surface-hover] focus:ring-[--color-border-accent]` |
| 91 | `border-brand-400 bg-brand-50 text-brand-700 hover:bg-brand-100 focus:ring-brand-500` | `border-[--color-border-accent] bg-[--color-bg-accent-subtle] text-[--color-text-accent-strong] hover:bg-em-100 focus:ring-[--color-border-accent]` |
| 101 | `border-gray-200` (divider) | `border-[--color-border-subtle]` |
| 104 | `bg-white ... text-gray-500` (divider text) | `bg-[--color-bg-surface] ... text-[--color-text-tertiary]` |
| 109 | `text-gray-600` (features text) | `text-[--color-text-secondary]` |
| 150 | `text-gray-500` (footer) | `text-[--color-text-tertiary]` |

Green (111, 112 줄) 유지. GitHub 버튼 (`bg-gray-900`) 유지.

**Step 2: 커밋**

```bash
git add frontend/src/pages/LoginPage.tsx
git commit -m "feat: LoginPage 에메랄드 토큰 적용"
```

---

### Task 8: `HomePage.tsx`

**Files:**
- Modify: `frontend/src/pages/HomePage.tsx`

**Step 1: 색상 교체 (~10건)**

| Line | Before | After |
|------|--------|-------|
| 20 | `text-gray-900` | `text-[--color-text-primary]` |
| 23 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 31 | `border-gray-200 bg-white ... hover:border-navy-300` | `border-[--color-border-default] bg-[--color-bg-surface] ... hover:border-[--color-border-accent]` |
| 33 | `bg-navy-50 text-navy-700` (icon) | `bg-em-50 text-em-700` |
| 38 | `text-gray-900` | `text-[--color-text-primary]` |
| 39 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 45 | `border-gray-200 bg-white ... hover:border-gray-300` | `border-[--color-border-default] bg-[--color-bg-surface] ... hover:border-ink-300` |
| 47 | `bg-gray-100 text-gray-600` (icon) | `bg-[--color-bg-neutral] text-[--color-text-tertiary]` |
| 52 | `text-gray-900` | `text-[--color-text-primary]` |
| 53 | `text-gray-500` | `text-[--color-text-tertiary]` |

**Step 2: 커밋**

```bash
git add frontend/src/pages/HomePage.tsx
git commit -m "feat: HomePage 에메랄드 토큰 적용"
```

---

### Task 9: `SettingsPage.tsx`

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`

**Step 1: 색상 교체 (~10건)**

| Line | Before | After |
|------|--------|-------|
| 38 | `text-gray-900` | `text-[--color-text-primary]` |
| 39 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 43 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 44 | `text-gray-900` | `text-[--color-text-primary]` |
| 49 | `border-gray-300 ... focus:border-navy-700 focus:ring-navy-700/20` | `border-[--color-border-default] ... focus:border-[--color-border-accent] focus:ring-em-500/20` |
| 54-55 | `bg-white border-gray-200`, `text-gray-900` | surface + text-primary tokens |
| 57 | `text-gray-700` | `text-[--color-text-secondary]` |
| 59 | `bg-gray-100 ... text-gray-600` | `bg-[--color-bg-neutral] ... text-[--color-text-secondary]` |
| 83-85 | `border-navy-700 bg-navy-50 text-navy-800` / `border-gray-300 bg-white text-gray-700 hover:bg-gray-50` | `border-[--color-border-accent] bg-em-50 text-em-800` / `border-[--color-border-default] bg-[--color-bg-surface] text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]` |
| 107 | `from-navy-700 to-navy-600 ... hover:from-navy-800 hover:to-navy-700` | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover] hover:shadow-[0_0_20px_-5px_hsl(160_60%_45%/0.2)]` |

**Step 2: 커밋**

```bash
git add frontend/src/pages/SettingsPage.tsx
git commit -m "feat: SettingsPage 에메랄드 토큰 적용"
```

---

### Task 10: `GitHubRepoSelector.tsx`

**Files:**
- Modify: `frontend/src/components/GitHubRepoSelector.tsx`

**Step 1: 색상 교체 (~12건)**

| Line | Before | After |
|------|--------|-------|
| 57 | `border-brand-200 bg-brand-50` | `border-amber-200 bg-amber-50` |
| 59 | `text-brand-500` | `text-amber-500` |
| 63 | `text-brand-800` | `text-amber-800` |
| 64 | `text-brand-600` | `text-amber-600` |
| 75-79 | `border-gray-200`, `bg-gray-200`, `bg-gray-100` | `border-[--color-border-default]`, `bg-ink-200`, `bg-[--color-bg-neutral]` |
| 135,140,150 | `focus:border-navy-700 focus:ring-navy-700` | `focus:border-[--color-border-accent] focus:ring-[--color-border-accent]` |
| 159 | `text-brand-600` / `text-gray-600` | `text-[--color-text-accent]` / `text-[--color-text-secondary]` |
| 184-189 | `border-navy-200 bg-navy-50` / `border-gray-200 hover:bg-gray-50` | `border-em-200 bg-em-50` / `border-[--color-border-default] hover:bg-[--color-bg-surface-hover]` |
| 197 | `text-navy-700 focus:ring-navy-700` | `text-em-700 focus:ring-[--color-border-accent]` |
| 203 | `bg-gray-200 text-gray-600` | `bg-ink-200 text-[--color-text-secondary]` |
| 215 | `bg-navy-600` | `bg-em-600` |

**Step 2: 커밋**

```bash
git add frontend/src/components/GitHubRepoSelector.tsx
git commit -m "feat: GitHubRepoSelector 에메랄드 토큰 적용"
```

---

### Task 11: `JobListPage.tsx`

**Files:**
- Modify: `frontend/src/pages/JobListPage.tsx`

**Step 1: StatusBadge 색상 교체**

```
Line 15: bg-brand-100 text-brand-700 → bg-em-100 text-em-700 (planning)
Line 16: bg-navy-100 text-navy-800 → bg-em-100 text-em-800 (analyzing)
Line 17: bg-brand-100 text-brand-700 → bg-em-100 text-em-700 (generating)
Line 13: bg-gray-100 text-gray-700 → bg-[--color-bg-neutral] text-[--color-text-secondary] (pending)
```

Blue, cyan, green, red 유지.

**Step 2: 페이지 색상 교체 (~15건)**

| Line | Before | After |
|------|--------|-------|
| 37 | `border-gray-200 bg-gray-50/50` | `border-[--color-border-default] bg-[--color-bg-page]` |
| 38 | `from-navy-700 to-navy-600` | `from-em-500 to-teal-500` |
| 53-54 | `text-gray-900`, `text-gray-500` | `text-[--color-text-primary]`, `text-[--color-text-tertiary]` |
| 57 | `from-navy-700 to-navy-600 ... hover:from-navy-800 hover:to-navy-700` | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover]` |
| 73 | `border-gray-200 bg-white` | `border-[--color-border-default] bg-[--color-bg-surface]` |
| 76-79 | `bg-gray-200`, `bg-gray-100` | `bg-ink-200`, `bg-[--color-bg-neutral]` |
| 100,138 | `text-gray-900` | `text-[--color-text-primary]` |
| 140 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 148 | `from-navy-700 to-navy-600 ...` (CTA) | `bg-[--color-bg-accent] ...` |
| 167 | `border-gray-200 bg-white hover:border-gray-300` | `border-[--color-border-default] bg-[--color-bg-surface] hover:border-ink-300` |
| 174 | `text-gray-900 hover:text-navy-700` | `text-[--color-text-primary] hover:text-[--color-text-accent]` |
| 198 | `bg-navy-50 text-navy-800 hover:bg-navy-100` | `bg-em-50 text-em-800 hover:bg-em-100` |
| 212 | `focus-visible:outline-navy-700` | `focus-visible:outline-[--color-border-accent]` |
| 231,244 | `border-gray-300 bg-white text-gray-700 hover:bg-gray-50` | `border-[--color-border-default] bg-[--color-bg-surface] text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]` |
| 238 | `text-gray-600` | `text-[--color-text-secondary]` |

**Step 3: 커밋**

```bash
git add frontend/src/pages/JobListPage.tsx
git commit -m "feat: JobListPage 에메랄드 토큰 적용"
```

---

### Task 12: `CreateJobPage.tsx`

**Files:**
- Modify: `frontend/src/pages/CreateJobPage.tsx`

**Step 1: 색상 교체 (~12건)**

| Line | Before | After |
|------|--------|-------|
| 189 | `from-navy-700 to-navy-600` | `from-em-500 to-teal-500` |
| 195 | `text-gray-900` | `text-[--color-text-primary]` |
| 196 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 213 | `border-gray-300 text-gray-900 placeholder-gray-400 focus:border-navy-700 focus:ring-navy-700/20` | `border-[--color-border-default] text-[--color-text-primary] placeholder-[--color-text-tertiary] focus:border-[--color-border-accent] focus:ring-em-500/20` |
| 271,287,306 | `text-gray-700` (labels) | `text-[--color-text-secondary]` |
| 276,293,320,340 | `border-gray-300 text-gray-900 focus:border-navy-700 focus:ring-navy-700/20` (inputs/selects) | `border-[--color-border-default] text-[--color-text-primary] focus:border-[--color-border-accent] focus:ring-em-500/20` |
| 311,331 | `text-gray-400` (icons) | `text-[--color-text-tertiary]` |
| 323 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 356 | `border-gray-200` | `border-[--color-border-default]` |
| 360 | `border-gray-300 bg-white text-gray-700 hover:bg-gray-50` | `border-[--color-border-default] bg-[--color-bg-surface] text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]` |
| 367 | `from-navy-700 to-navy-600 ... hover:from-navy-800 hover:to-navy-700 disabled:from-gray-400 disabled:to-gray-400` | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover] hover:shadow-[0_0_20px_-5px_hsl(160_60%_45%/0.2)] disabled:bg-ink-300` |

Red 에러 상태 (347-351) 유지.

**Step 2: 커밋**

```bash
git add frontend/src/pages/CreateJobPage.tsx
git commit -m "feat: CreateJobPage 에메랄드 토큰 적용"
```

---

### Task 13: `JobStatusPage.tsx`

**Files:**
- Modify: `frontend/src/pages/JobStatusPage.tsx`

**Step 1: PHASE_CONFIG 색상 교체**

```
Line 20: bg-gray-100 text-gray-600 → bg-[--color-bg-neutral] text-[--color-text-secondary] (pending)
Line 22: bg-brand-100 text-brand-600 → bg-em-100 text-em-600 (planning)
Line 23: bg-navy-100 text-navy-700 → bg-em-100 text-em-700 (analyzing)
Line 24: bg-brand-100 text-brand-600 → bg-em-100 text-em-600 (generating)
```

Blue, cyan, green, red 유지.

**Step 2: 컴포넌트 색상 교체 (~12건)**

| Line | Before | After |
|------|--------|-------|
| 101 | `bg-navy-100 text-navy-700 ring-4 ring-navy-50` | `bg-em-100 text-em-700 ring-4 ring-em-50` |
| 104 | `bg-gray-100 text-gray-400` | `bg-[--color-bg-neutral] text-[--color-text-tertiary]` |
| 120 | `text-navy-700` (spinner) | `text-em-700` |
| 182 | `border-navy-200 border-t-navy-700` | `border-em-200 border-t-em-700` |
| 184 | `from-navy-700 to-navy-600` | `from-em-500 to-teal-500` |
| 187 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 209,257 | `border-gray-200 bg-white` | `border-[--color-border-default] bg-[--color-bg-surface]` |
| 228-232 | `text-gray-400`, `text-gray-600` | `text-[--color-text-tertiary]`, `text-[--color-text-secondary]` |
| 241,258 | `text-gray-700`, `text-gray-900` | `text-[--color-text-secondary]`, `text-[--color-text-primary]` |
| 244 | `bg-gray-200` | `bg-ink-200` |
| 247 | `from-navy-700 to-navy-600` (progress bar) | `from-em-500 to-teal-500` |
| 270 | `bg-gray-200` (pending connector) | `bg-ink-200` |

Green 성공/Red 실패 카드 유지.

**Step 3: 커밋**

```bash
git add frontend/src/pages/JobStatusPage.tsx
git commit -m "feat: JobStatusPage 에메랄드 토큰 적용"
```

---

### Task 14: Charts — `RadarChart.tsx` + `ContributionChart.tsx`

**Files:**
- Modify: `frontend/src/components/charts/RadarChart.tsx`
- Modify: `frontend/src/components/charts/ContributionChart.tsx`

**Step 1: RadarChart SVG 색상 교체 (6건)**

| Line | Before | After |
|------|--------|-------|
| 114 | `stroke="#e5e7eb"` (grid) | `stroke="#ccd4e0"` |
| 127 | `stroke="#d1d5db"` (axis) | `stroke="#a5b3c8"` |
| 135 | `fill="rgba(27, 58, 92, 0.2)" stroke="#1B3A5C"` (required) | `fill="rgba(52, 79, 107, 0.10)" stroke="#344f6b"` |
| 196 | `bg-emerald-500` (candidate legend) | 유지 |
| 200 | `bg-navy-700` (required legend) | `bg-ink-600` |
| 187 | `fill-gray-600` (labels) | `fill-ink-600` |
| 197,201 | `text-gray-600` (legend text) | `text-[--color-text-secondary]` |

**Step 2: ContributionChart 색상 교체 (3건)**

| Line | Before | After |
|------|--------|-------|
| 31 | `color = '#6366f1'` | `color = '#2db882'` |
| 73 | `stroke="#e5e7eb"` | `stroke="#ccd4e0"` |
| 81 | `fill-gray-400` | `fill-ink-400` |
| 131 | `fill-gray-500` | `fill-ink-500` |

**Step 3: 커밋**

```bash
git add frontend/src/components/charts/RadarChart.tsx frontend/src/components/charts/ContributionChart.tsx
git commit -m "feat: 차트 에메랄드 색상 적용"
```

---

### Task 15: `QuestionCard.tsx`

**Files:**
- Modify: `frontend/src/components/QuestionCard.tsx`

**Step 1: 색상 교체 (~18건)**

| Line | Before | After |
|------|--------|-------|
| 36 | `text-gray-600` (confidence fallback) | `text-[--color-text-secondary]` |
| 54,58 | `bg-brand-100 text-brand-700` (badge) | `bg-em-100 text-em-700` |
| 61 | `bg-gray-100 text-gray-700` (badge fallback) | `bg-[--color-bg-neutral] text-[--color-text-secondary]` |
| 88 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 91 | `hover:bg-gray-50` | `hover:bg-[--color-bg-surface-hover]` |
| 98 | `bg-navy-100 text-navy-800` (Q number) | `bg-em-100 text-em-800` |
| 124 | `text-gray-900` | `text-[--color-text-primary]` |
| 129 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 133 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 142 | `border-gray-100` | `border-[--color-border-subtle]` |
| 146 | `bg-gray-50 border-gray-200` | `bg-[--color-bg-page] border-[--color-border-default]` |
| 147 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 148 | `text-gray-600` | `text-[--color-text-secondary]` |
| 187,201 | `text-gray-700` | `text-[--color-text-secondary]` |
| 190 | `text-gray-600 ... border-gray-200` | `text-[--color-text-secondary] ... border-[--color-border-default]` |
| 204 | `bg-brand-50 border-brand-200` (terminology) | `bg-em-50 border-em-200` |
| 205 | `text-brand-800` | `text-em-800` |
| 206 | `text-brand-700` | `text-em-700` |
| 215 | `bg-navy-50 border-navy-200` (interviewer note) | `bg-em-50 border-em-200` |
| 216 | `text-navy-800` | `text-em-800` |
| 217 | `text-navy-800` | `text-em-800` |
| 226 | `border-gray-100` | `border-[--color-border-subtle]` |
| 227 | `text-gray-600` | `text-[--color-text-secondary]` |
| 235 | `bg-navy-700 text-white border-navy-700` (selected score) | `bg-[--color-bg-accent] text-white border-[--color-border-accent]` |
| 237 | `bg-white text-gray-600 border-gray-200 hover:border-navy-600 hover:text-navy-700` | `bg-[--color-bg-surface] text-[--color-text-secondary] border-[--color-border-default] hover:border-[--color-border-accent] hover:text-[--color-text-accent]` |

Blue/Green/Yellow/Red semantic colors 유지.

**Step 2: 커밋**

```bash
git add frontend/src/components/QuestionCard.tsx
git commit -m "feat: QuestionCard 에메랄드 토큰 적용"
```

---

### Task 16: `ResultPage.tsx`

**Files:**
- Modify: `frontend/src/pages/ResultPage.tsx`

**Step 1: 색상 교체 (~15건)**

| Line | Before | After |
|------|--------|-------|
| 111 | `border-gray-200 bg-gray-50` | `border-[--color-border-default] bg-[--color-bg-page]` |
| 112 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 115 | `text-gray-800` | `text-[--color-text-primary]` |
| 137 | `from-navy-700 to-navy-600` | `from-em-500 to-teal-500` |
| 143 | `text-gray-900` | `text-[--color-text-primary]` |
| 144 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 151 | `bg-navy-100 text-navy-800` (badge) | `bg-em-100 text-em-800` |
| 162 | `border-navy-200 bg-navy-50` (score box) | `border-em-200 bg-em-50` |
| 163 | `text-navy-700` | `text-em-700` |
| 166 | `text-navy-800` | `text-em-800` |
| 175,184 | `border-gray-300 bg-white text-gray-700 hover:bg-gray-50` | `border-[--color-border-default] bg-[--color-bg-surface] text-[--color-text-secondary] hover:bg-[--color-bg-surface-hover]` |
| 198,270 | `border-gray-200` (tab bar) | `border-[--color-border-default]` |
| 207-260 | `text-navy-800` (active tab) | `text-em-700` |
| 207-260 | `text-gray-500 hover:text-gray-700` (inactive tab) | `text-[--color-text-tertiary] hover:text-[--color-text-secondary]` |
| 360 | `border-gray-200 bg-gray-50` | `border-[--color-border-default] bg-[--color-bg-page]` |
| 361 | `text-gray-300` | `text-ink-300` |
| 364 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 395 | `text-gray-500 hover:text-gray-700` | `text-[--color-text-tertiary] hover:text-[--color-text-secondary]` |

Red 에러 상태 유지.

**Step 2: 커밋**

```bash
git add frontend/src/pages/ResultPage.tsx
git commit -m "feat: ResultPage 에메랄드 토큰 적용"
```

---

### Task 17: `IntelBriefTab.tsx`

**Files:**
- Modify: `frontend/src/components/tabs/IntelBriefTab.tsx`

**Step 1: 색상 교체 (~25건)**

주요 변경:

| Line | Before | After |
|------|--------|-------|
| 26 | `from-navy-700 to-navy-600` (header gradient) | `from-em-600 to-teal-500` |
| 42,48,54,60,66 | `text-navy-100` | `text-em-100` |
| 75 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 76 | `text-gray-900` | `text-[--color-text-primary]` |
| 77 | `text-navy-700` (JD icon) | `text-em-700` |
| 84,190,194 | `text-gray-900` | `text-[--color-text-primary]` |
| 85,107,114,175,176,183,187,191,195,285,286 | `text-gray-500`/`text-gray-400` | `text-[--color-text-tertiary]` |
| 90,123,143,226 | `text-gray-700` | `text-[--color-text-secondary]` |
| 113,155,174,284 | `bg-gray-50 border-gray-200`/`border-gray-100` | `bg-[--color-bg-page] border-[--color-border-default]` |
| 126,444,462 | `text-gray-600` | `text-[--color-text-secondary]` |
| 127 | `text-navy-700` (bullet) | `text-em-700` |
| 138,165,244 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 166,245 | `text-gray-900` | `text-[--color-text-primary]` |
| 167 | `text-gray-700` (GitHub icon) | `text-[--color-text-secondary]` |
| 182,186 | `text-navy-700` (stats) | `text-em-700` |
| 200 | `bg-navy-50 border-navy-200` (tech match) | `bg-em-50 border-em-200` |
| 202 | `text-navy-900` / `text-brand-600` | `text-em-900` / `text-[--color-text-accent]` |
| 215 | `bg-navy-100 text-navy-800` (tech tags) | `bg-em-100 text-em-800` |
| 233,271 | `bg-brand-50 border-brand-200` / `text-brand-800` (warnings) | `bg-amber-50 border-amber-200` / `text-amber-800` |
| 333 | `text-navy-700` (skills icon) | `text-em-700` |
| 345-349 | `bg-navy-50 text-navy-800 border-navy-200` (non-match skill) | `bg-ink-100 text-ink-800 border-ink-200` |
| 387,409 | `text-brand-600` (projects/honors icon) | `text-em-600` |
| 394,416 | `bg-brand-50 border-brand-200` | `bg-em-50 border-em-200` |
| 419 | `text-brand-700` | `text-em-700` |
| 432-439 | `bg-brand-50 border-brand-200 text-brand-*` (recommendations) | `bg-em-50 border-em-200 text-em-*` |
| 487 | `border-gray-200` (bottom divider) | `border-[--color-border-default]` |

Emerald/blue/teal/green 시맨틱 색상 유지.

**Step 2: 커밋**

```bash
git add frontend/src/components/tabs/IntelBriefTab.tsx
git commit -m "feat: IntelBriefTab 에메랄드 토큰 적용"
```

---

### Task 18: `DeepAnalysisTab.tsx`

**Files:**
- Modify: `frontend/src/components/tabs/DeepAnalysisTab.tsx`

**Step 1: 색상 교체 (~15건)**

| Line | Before | After |
|------|--------|-------|
| 36 | `from-navy-700 to-navy-600` (header) | `from-em-600 to-teal-500` |
| 40 | `text-navy-100` | `text-em-100` |
| 47 | `bg-brand-400/20 text-brand-100 hover:bg-brand-400/30` (medium conf) | `bg-amber-400/20 text-amber-100 hover:bg-amber-400/30` |
| 65 | `text-navy-200 hover:text-white` | `text-em-200 hover:text-white` |
| 80,86,87 | `text-navy-100`, `text-navy-200` | `text-em-100`, `text-em-200` |
| 91,95,99 | `text-navy-100` | `text-em-100` |
| 108 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 109 | `text-gray-900` | `text-[--color-text-primary]` |
| 110 | `text-navy-700` (radar icon) | `text-em-700` |
| 148 | `bg-gray-100` (score bar bg) | `bg-[--color-bg-neutral]` |
| 158,162 | `text-gray-400`, `text-gray-500` | `text-[--color-text-tertiary]` |
| 173 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 176 | `hover:bg-gray-50` | `hover:bg-[--color-bg-surface-hover]` |
| 179 | `text-navy-700` | `text-em-700` |
| 182 | `text-gray-900` | `text-[--color-text-primary]` |
| 183,185,191 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 190 | `border-gray-100` | `border-[--color-border-subtle]` |
| 195 | `bg-navy-100 text-navy-700` (source badge) | `bg-em-100 text-em-700` |
| 198 | `text-gray-700` | `text-[--color-text-secondary]` |
| 229 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 230 | `text-gray-900` | `text-[--color-text-primary]` |
| 231 | `text-navy-700` | `text-em-700` |
| 241-246 | `text-gray-500` (table headers) | `text-[--color-text-tertiary]` |
| 251 | `hover:bg-gray-50` | `hover:bg-[--color-bg-surface-hover]` |
| 252 | `text-gray-900` | `text-[--color-text-primary]` |
| 253 | `text-gray-700` | `text-[--color-text-secondary]` |
| 257 | `bg-brand-100 text-brand-800` (partial match) | `bg-amber-100 text-amber-800` |
| 258 | `bg-gray-100 text-gray-800` (none) | `bg-[--color-bg-neutral] text-[--color-text-primary]` |
| 267 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 270 | `bg-brand-50 text-brand-700` (medium conf) | `bg-amber-50 text-amber-700` |
| 287 | `bg-navy-50 text-navy-800` (Q badge) | `bg-em-50 text-em-800` |
| 293 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 298 | `bg-gray-100` (conf bar bg) | `bg-[--color-bg-neutral]` |
| 303 | `bg-brand-500` (40-60 bar) | `bg-amber-500` |
| 309 | `text-gray-700` | `text-[--color-text-secondary]` |

Red/emerald/blue 시맨틱 유지.

**Step 2: 커밋**

```bash
git add frontend/src/components/tabs/DeepAnalysisTab.tsx
git commit -m "feat: DeepAnalysisTab 에메랄드 토큰 적용"
```

---

### Task 19: `LiveInterviewTab.tsx`

**Files:**
- Modify: `frontend/src/components/tabs/LiveInterviewTab.tsx`

**Step 1: 색상 교체 (~15건)**

| Line | Before | After |
|------|--------|-------|
| 113 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 116 | `text-gray-900` | `text-[--color-text-primary]` |
| 117 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 124 | `text-navy-700 hover:bg-navy-50` (select all) | `text-em-700 hover:bg-em-50` |
| 131 | `bg-navy-700 hover:bg-navy-800 disabled:bg-gray-300` (start btn) | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover] disabled:bg-ink-300` |
| 143 | `text-gray-700` | `text-[--color-text-secondary]` |
| 145 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 153-157 | `bg-navy-50 border-navy-300 ring-navy-200` / `bg-white border-gray-200 hover:border-gray-300` | `bg-em-50 border-em-300 ring-em-200` / `bg-[--color-bg-surface] border-[--color-border-default] hover:border-ink-300` |
| 160-164 | `bg-navy-700 border-navy-700` / `border-gray-300` (checkbox) | `bg-em-600 border-em-600` / `border-ink-300` |
| 181 | `bg-brand-100 text-brand-700` (medium diff badge) | `bg-amber-100 text-amber-700` |
| 196 | `text-gray-600` | `text-[--color-text-secondary]` |
| 234-235 | `text-gray-900`, `text-gray-500` | `text-[--color-text-primary]`, `text-[--color-text-tertiary]` |
| 238 | `text-navy-700` (score %) | `text-em-700` |
| 241 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 255-256 | `text-gray-700`, `text-gray-500` | `text-[--color-text-secondary]`, `text-[--color-text-tertiary]` |
| 258 | `bg-gray-100` (score bar bg) | `bg-[--color-bg-neutral]` |
| 262 | `bg-brand-500` (40-70 bar) | `bg-amber-500` |
| 276 | `text-gray-700 bg-white border-gray-300 hover:bg-gray-50` | `text-[--color-text-secondary] bg-[--color-bg-surface] border-[--color-border-default] hover:bg-[--color-bg-surface-hover]` |
| 282 | `bg-navy-700 hover:bg-navy-800` (new interview btn) | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover]` |
| 303 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 303 | `hover:bg-navy-50` (back btn) | `hover:bg-em-50` |
| 313 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 322 | `text-gray-500 hover:text-gray-700` | `text-[--color-text-tertiary] hover:text-[--color-text-secondary]` |
| 323 | `text-gray-300` | `text-ink-300` |
| 324 | `text-gray-900` | `text-[--color-text-primary]` |
| 329 | `text-gray-500` / `text-navy-700` | `text-[--color-text-tertiary]` / `text-em-700` |
| 331 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 335 | `bg-gray-100` | `bg-[--color-bg-neutral]` |
| 337 | `bg-navy-500` (progress bar) | `bg-em-500` |
| 357 | `text-gray-700 bg-white border-gray-300 hover:bg-gray-50` | `text-[--color-text-secondary] bg-[--color-bg-surface] border-[--color-border-default] hover:bg-[--color-bg-surface-hover]` |
| 371 | `bg-navy-700 hover:bg-navy-800` (next btn) | `bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover]` |

Green finish 버튼 유지.

**Step 2: 커밋**

```bash
git add frontend/src/components/tabs/LiveInterviewTab.tsx
git commit -m "feat: LiveInterviewTab 에메랄드 토큰 적용"
```

---

### Task 20: `DecisionTab.tsx`

**Files:**
- Modify: `frontend/src/components/tabs/DecisionTab.tsx`

**Step 1: 색상 교체 (~10건)**

| Line | Before | After |
|------|--------|-------|
| 43 | `from-brand-500 to-orange-600` (amber gradient) | `from-amber-500 to-amber-600` |
| 61 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 62 | `text-gray-700` | `text-[--color-text-secondary]` |
| 63 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 70 | `bg-brand-400` (40-60 bar segment) | `bg-amber-400` |
| 75 | `bg-gray-900` (score indicator) | `bg-ink-900` |
| 79 | `text-gray-500` | `text-[--color-text-tertiary]` |
| 82,86,90,94 | `text-gray-400` | `text-[--color-text-tertiary]` |
| 85 | `text-brand-600` (40-60 label) | `text-amber-600` |
| 100 | `bg-white ... border-gray-200` | `bg-[--color-bg-surface] ... border-[--color-border-default]` |
| 101 | `text-gray-900` | `text-[--color-text-primary]` |
| 102 | `text-navy-700` (decision icon) | `text-em-700` |
| 110 | `bg-navy-50 border-navy-200` (evidence box) | `bg-em-50 border-em-200` |
| 111 | `text-navy-900` | `text-em-900` |
| 112 | `text-navy-800` | `text-em-800` |
| 133 | `bg-brand-50 border-brand-200` (concerns card) | `bg-amber-50 border-amber-200` |
| 134 | `text-brand-900` | `text-amber-900` |
| 139 | `text-brand-800` | `text-amber-800` |
| 140 | `text-brand-500` (bullet) | `text-amber-500` |

Emerald/green strengths 유지. Red 유지.

**Step 2: 커밋**

```bash
git add frontend/src/components/tabs/DecisionTab.tsx
git commit -m "feat: DecisionTab 에메랄드 토큰 적용"
```

---

### Task 21: 최종 검증

**Step 1: TypeScript 빌드 체크**

```bash
cd frontend && npx tsc --noEmit
```

Expected: 에러 없음.

**Step 2: 잔여 navy/brand 참조 검사**

```bash
grep -rn 'navy-\|brand-\|#1B3A5C\|#E87E24' frontend/src/ --include='*.tsx' --include='*.ts' --include='*.css'
```

Expected: 결과 없음 (모두 제거됨).

**Step 3: Docker 빌드 & 시각 확인**

```bash
docker compose up -d --build frontend
```

브라우저에서 각 페이지 확인:
- `/demo/login` — 에메랄드 CTA, glass 없음 (카드 solid)
- `/demo/` — 에메랄드 아이콘, 호버 시 에메랄드 보더
- `/demo/interview/new` — 에메랄드 submit 버튼 + glow
- `/demo/interview` — 에메랄드 StatusBadge, CTA
- `/demo/interview/:id` — 에메랄드 progress bar
- `/demo/interview/:id/result` — 에메랄드 헤더 gradient, 차트 색상
- Navbar — glass 효과 (backdrop-blur)

**Step 4: 커밋 (검증 완료)**

```bash
git add -A
git commit -m "feat: 에메랄드 라이트 테마 최종 검증 완료"
```

---

### Task 22: 디자인 시스템 스킬 업데이트

**Files:**
- Modify: `.claude/skills/jittda-design-system/SKILL.md`

**Step 1: Brand Identity 업데이트**

기존 Navy+Orange → Emerald+Teal 반영. Demo App Theme 섹션 추가. Scale token/Semantic token 테이블 업데이트. 컴포넌트 패턴 예제를 에메랄드 토큰으로 교체.

**Step 2: 커밋**

```bash
git add .claude/skills/jittda-design-system/SKILL.md
git commit -m "docs: 디자인 시스템 스킬 에메랄드 테마 반영"
```
