# Emerald Light Theme — Design Document

> 랜딩페이지 에메랄드/틸 색감을 라이트 모드로 반전하여 데모 앱에 적용

## Context

랜딩페이지(`jittda-landingpage/`)는 **다크 배경 + 에메랄드(`#2db882`) 액센트**를 사용. 데모 앱(`frontend/`)은 **라이트 + Navy(`#1B3A5C`) + Orange(`#E87E24`)**. 브랜드 통일을 위해 데모 앱을 에메랄드 라이트 테마로 전환.

## Design Decisions

| 항목 | 결정 |
|------|------|
| 테마 | 라이트 모드 + 에메랄드 |
| Glass 효과 | Navbar + Modal/Dropdown (카드는 solid white) |
| 폰트 | Pretendard 유지 (한글 최적화) |
| Glow | CTA 버튼 호버에만 |
| 헤더 카드 | 에메랄드→틸 그라데이션 (다크 유지) |
| 경고색 | Orange → Amber로 통일 |
| 구현 방식 | Semantic Token 전면 교체 (2-tier) |

## Color Palette

### Scale Tokens (`@theme`)

```
Emerald (Primary Accent)
em-50:  #f0fdf8    em-500: #2db882 ← 랜딩 primary
em-100: #ccfbe9    em-600: #1f9a6a
em-200: #99f6d3    em-700: #167a52
em-300: #5eecb9    em-800: #115c3d
em-400: #2fd990    em-900: #0d3f2a

Ink (Cool Neutral / Blue-gray)
ink-50:  #f5f7fa    ink-500: #4a6685
ink-100: #e8ecf2    ink-600: #344f6b
ink-200: #ccd4e0    ink-700: #253d55
ink-300: #a5b3c8    ink-800: #182c3f
ink-400: #7089a8    ink-900: #0f1e2e

Teal (Gradient Partner)
teal-400: #2dd4bf   teal-500: #1aada0
```

### Semantic Tokens (`:root` CSS variables)

| Token | Value | Role |
|-------|-------|------|
| `--color-bg-page` | ink-50 `#f5f7fa` | 페이지 배경 |
| `--color-bg-surface` | `#ffffff` | 카드/패널 배경 |
| `--color-bg-surface-hover` | em-50 `#f0fdf8` | 카드 호버 |
| `--color-bg-accent` | em-500 `#2db882` | CTA 버튼 |
| `--color-bg-accent-hover` | em-600 `#1f9a6a` | CTA 호버 |
| `--color-bg-accent-subtle` | em-50 `#f0fdf8` | 연한 액센트 배경 |
| `--color-bg-neutral` | ink-100 `#e8ecf2` | 비활성 배경 |
| `--color-text-primary` | ink-900 `#0f1e2e` | 제목/라벨 |
| `--color-text-secondary` | ink-600 `#344f6b` | 본문 |
| `--color-text-tertiary` | ink-400 `#7089a8` | 힌트/캡션 |
| `--color-text-on-accent` | `#ffffff` | CTA 위 텍스트 |
| `--color-text-accent` | em-600 `#1f9a6a` | 링크/강조 |
| `--color-text-accent-strong` | em-700 `#167a52` | 진한 강조 |
| `--color-border-default` | ink-200 `#ccd4e0` | 기본 보더 |
| `--color-border-subtle` | ink-100 `#e8ecf2` | 구분선 |
| `--color-border-accent` | em-500 `#2db882` | 포커스/활성 보더 |

### Shadows

```css
--shadow-card:       0 1px 3px 0 hsl(160 40% 20% / 0.07), 0 1px 2px -1px hsl(160 40% 20% / 0.05);
--shadow-card-hover: 0 4px 12px -2px hsl(160 40% 20% / 0.12), 0 2px 6px -2px hsl(160 40% 20% / 0.07);
--shadow-elevated:   0 10px 25px -5px hsl(160 40% 20% / 0.14), 0 8px 10px -6px hsl(160 40% 20% / 0.07);
--shadow-glow-sm:    0 0 20px -5px hsl(160 60% 45% / 0.20);
```

## Component Patterns

### Button

```tsx
// Primary CTA
className="bg-[--color-bg-accent] hover:bg-[--color-bg-accent-hover] text-white
  rounded-lg font-medium shadow-sm transition-colors
  hover:shadow-[0_0_20px_-5px_hsl(160_60%_45%/0.2)]
  focus:ring-2 focus:ring-[--color-border-accent] focus:ring-offset-2"

// Secondary
className="bg-[--color-bg-surface] hover:bg-em-50
  text-[--color-text-secondary] border border-[--color-border-default]
  rounded-lg font-medium transition-colors"

// Gradient (header sections only)
className="bg-gradient-to-r from-em-600 to-teal-500
  text-white rounded-lg font-medium shadow-lg"
```

### Card

```tsx
// Standard
className="bg-[--color-bg-surface] border border-[--color-border-default]
  rounded-xl shadow-card hover:shadow-card-hover transition-all"

// Header (dark gradient)
className="bg-gradient-to-r from-em-600 to-teal-500
  text-white rounded-xl shadow-lg"
```

### Input

```tsx
className="w-full px-4 py-3 bg-[--color-bg-surface]
  border border-[--color-border-default] rounded-lg
  text-[--color-text-primary] placeholder:text-[--color-text-tertiary]
  focus:border-[--color-border-accent] focus:ring-2 focus:ring-em-500/20"
```

### Navbar

```tsx
className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg
  border-b border-[--color-border-default]/50"
// Active nav: bg-em-50 text-em-700
// CTA button: bg-[--color-bg-accent]
// Avatar gradient: from-em-500 to-teal-400
```

### Modal

```tsx
// Backdrop: bg-ink-950/60 backdrop-blur-sm
// Panel: bg-[--color-bg-surface] rounded-2xl shadow-elevated
```

### Badge

```tsx
// Match/Success: bg-em-100 text-em-800
// Warning:       bg-amber-100 text-amber-800
// Neutral:       bg-ink-100 text-ink-700
```

## Mapping Rules

| Before | After |
|--------|-------|
| `bg-white` | `bg-[--color-bg-surface]` |
| `bg-gray-50` | `bg-[--color-bg-page]` |
| `border-gray-200` | `border-[--color-border-default]` |
| `text-gray-900` | `text-[--color-text-primary]` |
| `text-gray-600/700` | `text-[--color-text-secondary]` |
| `text-gray-400/500` | `text-[--color-text-tertiary]` |
| `bg-navy-*` | `bg-em-*` (accent) or `bg-ink-*` (neutral) |
| `text-navy-*` | `text-em-*` or `text-[--color-text-accent]` |
| `from-navy-700 to-navy-600` | `from-em-600 to-teal-500` |
| `bg-brand-*` (accent) | `bg-em-*` |
| `bg-brand-*` (warning) | `bg-amber-*` |
| `ring-navy-*` | `ring-em-500` |

## Preserve (No Change)

- Red: error/danger (`bg-red-50`, `text-red-600`)
- Green: success (`bg-green-50`, `text-green-600`)
- Blue: LinkedIn brand (`bg-blue-50`, `text-blue-700`)
- GitHub button: `bg-gray-900`
- Google button: OAuth icon colors

## Files to Modify (18)

1. `frontend/src/index.css` — token system
2. `frontend/src/components/SectionCard.tsx`
3. `frontend/src/components/FileUploadField.tsx`
4. `frontend/src/components/EmailNotificationModal.tsx`
5. `frontend/src/components/Navbar.tsx`
6. `frontend/src/components/QuestionCard.tsx`
7. `frontend/src/components/charts/RadarChart.tsx`
8. `frontend/src/components/charts/ContributionChart.tsx`
9. `frontend/src/pages/LoginPage.tsx`
10. `frontend/src/pages/HomePage.tsx`
11. `frontend/src/pages/JobListPage.tsx`
12. `frontend/src/pages/CreateJobPage.tsx`
13. `frontend/src/pages/JobStatusPage.tsx`
14. `frontend/src/pages/ResultPage.tsx`
15. `frontend/src/components/tabs/IntelBriefTab.tsx`
16. `frontend/src/components/tabs/DeepAnalysisTab.tsx`
17. `frontend/src/components/tabs/LiveInterviewTab.tsx`
18. `frontend/src/components/tabs/DecisionTab.tsx`
19. `.claude/skills/jittda-design-system/SKILL.md`

## Chart Colors

### RadarChart

```
Grid:     stroke="#ccd4e0" (ink-200)
Axis:     stroke="#a5b3c8" (ink-300)
Required: stroke="#344f6b" fill="hsl(220 37% 24% / 0.10)" dashed
Candidate: stroke="#2db882" fill="hsl(160 60% 45% / 0.25)"
Points:   fill="#2db882"
Labels:   fill="#344f6b" (ink-600)
```

### ContributionChart

```
Default color: #2db882 (em-500)
Grid:   stroke="#ccd4e0" (ink-200)
Labels: fill="#7089a8" (ink-400) / fill="#4a6685" (ink-500)
```

## Global CSS Updates

- `*:focus-visible` → `outline: 2px solid var(--color-border-accent)`
- `.skip-link` → `background: var(--color-bg-accent)`
- `.tab-underline::after` → `linear-gradient(to right, #2db882, #2dd4bf)`
- `.skeleton` → `ink-50 → ink-100` gradient
- Scrollbar → `ink-200` / `ink-400`
- `body` → `background-color: var(--color-bg-page)`
- New: `.gradient-text-em`, `.glow-em-sm`
