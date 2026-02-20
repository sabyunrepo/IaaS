# Seed Design Component Migration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 데모 앱의 커스텀 Tailwind UI를 Seed Design React 컴포넌트로 교체하여 디자인 시스템 통일

**Architecture:** Seed Design(@seed-design/react v1.2.4)의 compound component 패턴 사용. `seed-design/ui/` 디렉토리에 스니펫(래퍼)을 생성하고, 각 페이지/컴포넌트에서 import하여 기존 `<button>`, `<input>` 등을 교체. Carrot 팔레트를 에메랄드로 오버라이드하여 brand 색상 자동 적용.

**Tech Stack:** React 19, @seed-design/react 1.2.4, @seed-design/css 1.2.2, Tailwind CSS v4, Vite

**Design Doc:** `docs/plans/2026-02-20-seed-design-migration-design.md`

---

## 보존 규칙 (모든 태스크에 적용)

- `jittda-landingpage/` 제외
- Red/Green/Blue/Amber 시맨틱 상태 색상 유지 (Seed 컴포넌트의 tone prop 활용)
- 기존 em-*/ink-* 커스텀 토큰과 Seed 토큰 공존
- 접근성(WCAG) 기존 구현 보존 (aria-*, role, keyboard nav)
- i18n `t()` 함수 호출 보존

---

## Task 1: Carrot 팔레트 에메랄드 오버라이드

**Files:**
- Modify: `frontend/src/index.css`

**Step 1: `:root` 블록에 Seed Design carrot 오버라이드 추가**

`index.css`의 기존 `:root` 블록 안에 carrot 팔레트 오버라이드를 추가한다.
이렇게 하면 Seed 컴포넌트의 `variant="brandSolid"` 등이 자동으로 에메랄드로 렌더링된다.

```css
:root {
  /* ... 기존 시맨틱 토큰들 ... */

  /* Seed Design: carrot → emerald override */
  --seed-color-palette-carrot-100: #f0fdf8;
  --seed-color-palette-carrot-200: #ccfbe9;
  --seed-color-palette-carrot-300: #99f6d3;
  --seed-color-palette-carrot-400: #5eecb9;
  --seed-color-palette-carrot-500: #2fd990;
  --seed-color-palette-carrot-600: #2db882;
  --seed-color-palette-carrot-700: #1f9a6a;
  --seed-color-palette-carrot-800: #167a52;
  --seed-color-palette-carrot-900: #115c3d;
  --seed-color-palette-carrot-1000: #071f15;
}
```

**Step 2: 브라우저에서 확인**

Run: `docker compose up -d frontend && sleep 3`
브라우저에서 `/demo/` 접속, DevTools > Elements에서 `--seed-color-palette-carrot-600`이 `#2db882`인지 확인.

**Step 3: Commit**

```bash
git add frontend/src/index.css
git commit -m "feat: Seed Design carrot 팔레트를 에메랄드로 오버라이드"
```

---

## Task 2: Seed Design 컴포넌트 스니펫 생성

**Files:**
- Create: `frontend/seed-design/ui/badge.tsx`
- Create: `frontend/seed-design/ui/skeleton.tsx`
- Create: `frontend/seed-design/ui/divider.tsx`
- Create: `frontend/seed-design/ui/text-field.tsx`
- Create: `frontend/seed-design/ui/avatar.tsx`
- Create: `frontend/seed-design/ui/callout.tsx`
- Create: `frontend/seed-design/ui/switch.tsx`
- Create: `frontend/seed-design/ui/checkbox.tsx`
- Create: `frontend/seed-design/ui/tabs.tsx`
- Create: `frontend/seed-design/ui/dialog.tsx`
- Create: `frontend/seed-design/ui/index.ts` (barrel export)

기존 스니펫(action-button, loading-indicator, progress-circle)은 이미 존재.
CLI(`npx @seed-design/cli add`)는 deprecated 컴포넌트에서 대화형 프롬프트가 발생하므로, 기존 스니펫 패턴을 참조하여 직접 작성한다.

**Step 1: 각 스니펫 파일 작성**

아래는 각 파일의 전체 코드:

### badge.tsx
```tsx
import { Badge as SeedBadge, type BadgeProps as SeedBadgeProps } from "@seed-design/react"
import * as React from "react"

export interface BadgeProps extends SeedBadgeProps {}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>((props, ref) => {
  return <SeedBadge ref={ref} {...props} />
})
Badge.displayName = "Badge"
```

### skeleton.tsx
```tsx
import { Skeleton as SeedSkeleton, type SkeletonProps as SeedSkeletonProps } from "@seed-design/react"
import * as React from "react"

export interface SkeletonProps extends SeedSkeletonProps {}

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>((props, ref) => {
  return <SeedSkeleton ref={ref} {...props} />
})
Skeleton.displayName = "Skeleton"
```

### divider.tsx
```tsx
import { Divider as SeedDivider, type DividerProps as SeedDividerProps } from "@seed-design/react"
import * as React from "react"

export interface DividerProps extends SeedDividerProps {}

export const Divider = React.forwardRef<HTMLHRElement, DividerProps>((props, ref) => {
  return <SeedDivider ref={ref} {...props} />
})
Divider.displayName = "Divider"
```

### text-field.tsx
```tsx
import {
  TextFieldRoot as SeedTextFieldRoot,
  TextFieldInput as SeedTextFieldInput,
  TextFieldTextarea as SeedTextFieldTextarea,
  TextFieldPrefixIcon,
  TextFieldSuffixIcon,
} from "@seed-design/react"

export {
  SeedTextFieldRoot as TextFieldRoot,
  SeedTextFieldInput as TextFieldInput,
  SeedTextFieldTextarea as TextFieldTextarea,
  TextFieldPrefixIcon,
  TextFieldSuffixIcon,
}
```

### avatar.tsx
```tsx
import {
  AvatarRoot as SeedAvatarRoot,
  AvatarImage as SeedAvatarImage,
  AvatarFallback as SeedAvatarFallback,
} from "@seed-design/react"

export {
  SeedAvatarRoot as AvatarRoot,
  SeedAvatarImage as AvatarImage,
  SeedAvatarFallback as AvatarFallback,
}
```

### callout.tsx
```tsx
import {
  CalloutRoot as SeedCalloutRoot,
  CalloutContent as SeedCalloutContent,
  CalloutTitle as SeedCalloutTitle,
  CalloutDescription as SeedCalloutDescription,
} from "@seed-design/react"

export {
  SeedCalloutRoot as CalloutRoot,
  SeedCalloutContent as CalloutContent,
  SeedCalloutTitle as CalloutTitle,
  SeedCalloutDescription as CalloutDescription,
}
```

### switch.tsx
```tsx
import {
  SwitchRoot as SeedSwitchRoot,
  SwitchControl as SeedSwitchControl,
  SwitchThumb as SeedSwitchThumb,
  SwitchLabel as SeedSwitchLabel,
  SwitchHiddenInput as SeedSwitchHiddenInput,
} from "@seed-design/react"

export {
  SeedSwitchRoot as SwitchRoot,
  SeedSwitchControl as SwitchControl,
  SeedSwitchThumb as SwitchThumb,
  SeedSwitchLabel as SwitchLabel,
  SeedSwitchHiddenInput as SwitchHiddenInput,
}
```

### checkbox.tsx
```tsx
import {
  CheckboxRoot as SeedCheckboxRoot,
  CheckboxControl as SeedCheckboxControl,
  CheckboxIndicator as SeedCheckboxIndicator,
  CheckboxLabel as SeedCheckboxLabel,
  CheckboxHiddenInput as SeedCheckboxHiddenInput,
} from "@seed-design/react"

export {
  SeedCheckboxRoot as CheckboxRoot,
  SeedCheckboxControl as CheckboxControl,
  SeedCheckboxIndicator as CheckboxIndicator,
  SeedCheckboxLabel as CheckboxLabel,
  SeedCheckboxHiddenInput as CheckboxHiddenInput,
}
```

### tabs.tsx
```tsx
import {
  TabsRoot as SeedTabsRoot,
  TabsList as SeedTabsList,
  TabsTrigger as SeedTabsTrigger,
  TabsContent as SeedTabsContent,
  TabsIndicator as SeedTabsIndicator,
} from "@seed-design/react"

export {
  SeedTabsRoot as TabsRoot,
  SeedTabsList as TabsList,
  SeedTabsTrigger as TabsTrigger,
  SeedTabsContent as TabsContent,
  SeedTabsIndicator as TabsIndicator,
}
```

### dialog.tsx
```tsx
import {
  DialogRoot as SeedDialogRoot,
  DialogTrigger as SeedDialogTrigger,
  DialogPositioner as SeedDialogPositioner,
  DialogBackdrop as SeedDialogBackdrop,
  DialogContent as SeedDialogContent,
  DialogHeader as SeedDialogHeader,
  DialogTitle as SeedDialogTitle,
  DialogDescription as SeedDialogDescription,
  DialogFooter as SeedDialogFooter,
  DialogAction as SeedDialogAction,
} from "@seed-design/react"

export {
  SeedDialogRoot as DialogRoot,
  SeedDialogTrigger as DialogTrigger,
  SeedDialogPositioner as DialogPositioner,
  SeedDialogBackdrop as DialogBackdrop,
  SeedDialogContent as DialogContent,
  SeedDialogHeader as DialogHeader,
  SeedDialogTitle as DialogTitle,
  SeedDialogDescription as DialogDescription,
  SeedDialogFooter as DialogFooter,
  SeedDialogAction as DialogAction,
}
```

### index.ts (barrel export)
```ts
export { ActionButton } from "./action-button"
export { Badge } from "./badge"
export { Skeleton } from "./skeleton"
export { Divider } from "./divider"
export { ProgressCircle } from "./progress-circle"
export { LoadingIndicator } from "./loading-indicator"

export {
  TextFieldRoot, TextFieldInput, TextFieldTextarea,
  TextFieldPrefixIcon, TextFieldSuffixIcon,
} from "./text-field"

export { AvatarRoot, AvatarImage, AvatarFallback } from "./avatar"

export {
  CalloutRoot, CalloutContent, CalloutTitle, CalloutDescription,
} from "./callout"

export {
  SwitchRoot, SwitchControl, SwitchThumb, SwitchLabel, SwitchHiddenInput,
} from "./switch"

export {
  CheckboxRoot, CheckboxControl, CheckboxIndicator,
  CheckboxLabel, CheckboxHiddenInput,
} from "./checkbox"

export {
  TabsRoot, TabsList, TabsTrigger, TabsContent, TabsIndicator,
} from "./tabs"

export {
  DialogRoot, DialogTrigger, DialogPositioner, DialogBackdrop,
  DialogContent, DialogHeader, DialogTitle, DialogDescription,
  DialogFooter, DialogAction,
} from "./dialog"
```

**Step 2: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`
Expected: 0 errors

**Step 3: Commit**

```bash
git add frontend/seed-design/ui/
git commit -m "feat: Seed Design 10개 컴포넌트 스니펫 + barrel export 생성"
```

---

## Task 3: ActionButton 교체 — CTA/Submit 버튼 (10파일, ~20개)

**Files:**
- Modify: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/pages/CreateJobPage.tsx`
- Modify: `frontend/src/pages/JobListPage.tsx`
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Modify: `frontend/src/components/EmailNotificationModal.tsx`
- Modify: `frontend/src/components/ErrorBoundary.tsx`
- Modify: `frontend/src/components/FileUploadField.tsx`

**교체 규칙:**

| 기존 패턴 | Seed 교체 |
|-----------|-----------|
| Primary CTA (bg-accent, text-white) | `<ActionButton variant="brandSolid" size="medium">` |
| Secondary (bg-surface, border) | `<ActionButton variant="neutralOutline" size="medium">` |
| Danger (bg-red-*, text-white) | `<ActionButton variant="criticalSolid" size="medium">` |
| Ghost (text only, no bg) | `<ActionButton variant="ghost" size="medium">` |
| Disabled + Spinner | `<ActionButton variant="brandSolid" loading={true} disabled>` |

**Step 1: 각 파일에서 `<button>` → `<ActionButton>` 교체**

import 추가:
```tsx
import { ActionButton } from '../../seed-design/ui'
```

교체 예시 — Primary CTA:
```tsx
// Before
<button
  onClick={handleSubmit}
  disabled={saving}
  className="w-full rounded-lg bg-[--color-bg-accent] px-4 py-3 text-sm font-medium text-white ..."
>
  {saving ? t('saving') : t('settings_save')}
</button>

// After
<ActionButton
  variant="brandSolid"
  size="medium"
  onClick={handleSubmit}
  loading={saving}
  disabled={saving || !displayName.trim()}
  className="w-full"
>
  {t('settings_save')}
</ActionButton>
```

교체 예시 — Secondary:
```tsx
// Before
<button className="... bg-[--color-bg-neutral] text-[--color-text-secondary] ...">
  {t('cancel')}
</button>

// After
<ActionButton variant="neutralOutline" size="medium">
  {t('cancel')}
</ActionButton>
```

**주의사항:**
- `<a>` 태그로 감싸진 버튼(OAuth 링크)은 교체하지 않음
- `role="tab"` 버튼은 Tabs 컴포넌트로 별도 교체 (Task 12)
- 기존 레이아웃 className(`w-full`, `flex-1`, `gap-3` 등)은 ActionButton에 그대로 전달
- `loading` prop을 사용하면 LoadingIndicator가 자동 표시되므로 수동 SVG spinner 제거

**Step 2: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`
Expected: 0 errors

**Step 3: 브라우저에서 시각 확인**

각 페이지에서 버튼 렌더링 확인:
- `/demo/login` — Dev 로그인 버튼
- `/demo/interview` — 새 분석 버튼
- `/demo/settings` — 저장 버튼

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: CTA/submit 버튼 ActionButton 교체 (7파일)"
```

---

## Task 4: ActionButton 교체 — 탭 내부 버튼 (4파일)

**Files:**
- Modify: `frontend/src/components/tabs/LiveInterviewTab.tsx` (~10 buttons)
- Modify: `frontend/src/components/tabs/DeepAnalysisTab.tsx` (~3 buttons)
- Modify: `frontend/src/components/tabs/IntelBriefTab.tsx` (~1 button)
- Modify: `frontend/src/components/tabs/InterviewQuestionCard.tsx` (~4 buttons)
- Modify: `frontend/src/components/QuestionCard.tsx` (~2 buttons)
- Modify: `frontend/src/pages/ResultPage.tsx` (header area buttons only, NOT tab triggers)

**교체 규칙:** Task 3과 동일

**주의사항:**
- ResultPage의 `role="tab"` 버튼은 건드리지 않음 — Task 12에서 Tabs로 교체
- 점수 버튼(1~5점)처럼 상태에 따라 스타일이 바뀌는 버튼은 `variant`를 동적으로 설정:
  ```tsx
  <ActionButton
    variant={selected ? "brandSolid" : "neutralOutline"}
    size="xsmall"
    onClick={() => setScore(n)}
  >
    {n}
  </ActionButton>
  ```

**Step 1: 각 파일에서 `<button>` → `<ActionButton>` 교체**

**Step 2: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: 탭/카드 내부 버튼 ActionButton 교체 (6파일)"
```

---

## Task 5: Badge 교체 — 상태 배지 및 태그 (~5파일, ~13개)

**Files:**
- Modify: `frontend/src/pages/JobListPage.tsx` (StatusBadge)
- Modify: `frontend/src/pages/JobStatusPage.tsx` (phase badge)
- Modify: `frontend/src/pages/ResultPage.tsx` (experience badge)
- Modify: `frontend/src/components/QuestionCard.tsx` (revision type badges)
- Modify: `frontend/src/components/tabs/DeepAnalysisTab.tsx` (skill badges)
- Modify: `frontend/src/components/tabs/IntelBriefTab.tsx` (tech stack tags)

**교체 규칙:**

| 기존 패턴 | Seed Badge |
|-----------|-----------|
| Status 배지 (bg-green-100 text-green-800) | `<Badge tone="positive" variant="weak">` |
| Status 배지 (bg-red-100 text-red-800) | `<Badge tone="critical" variant="weak">` |
| Status 배지 (bg-amber-100 text-amber-800) | `<Badge tone="warning" variant="weak">` |
| Status 배지 (bg-blue-100 text-blue-800) | `<Badge tone="informative" variant="weak">` |
| Brand 배지 (bg-em-100 text-em-800) | `<Badge tone="brand" variant="weak">` |
| Neutral 배지 (bg-ink-100 text-ink-700) | `<Badge tone="neutral" variant="weak">` |

**Step 1: import 추가 + `<span className="...badge...">` → `<Badge>` 교체**

```tsx
import { Badge } from '../../seed-design/ui'

// Before
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
  {t('status_completed')}
</span>

// After
<Badge tone="positive" variant="weak">
  {t('status_completed')}
</Badge>
```

StatusBadge 헬퍼 함수가 있다면, 내부를 Badge 컴포넌트로 교체:
```tsx
function StatusBadge({ status }: { status: string }) {
  const toneMap: Record<string, 'positive' | 'critical' | 'warning' | 'neutral' | 'informative'> = {
    completed: 'positive',
    failed: 'critical',
    running: 'informative',
    pending: 'neutral',
  }
  return <Badge tone={toneMap[status] || 'neutral'} variant="weak">{status}</Badge>
}
```

**Step 2: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: 상태 배지/태그 Seed Badge 컴포넌트 교체 (6파일)"
```

---

## Task 6: Skeleton 교체 — 로딩 플레이스홀더 (~3파일)

**Files:**
- Modify: `frontend/src/pages/ResultPage.tsx` (loading state)
- Modify: `frontend/src/pages/JobListPage.tsx` (if skeleton exists)
- Modify: `frontend/src/pages/JobStatusPage.tsx` (if skeleton exists)

**교체 규칙:**

```tsx
import { Skeleton } from '../../seed-design/ui'

// Before (커스텀 CSS 클래스)
<div className="skeleton h-14 w-14 rounded-2xl" />
<div className="skeleton h-6 w-48" />

// After (Seed Skeleton)
<Skeleton height="3.5rem" width="3.5rem" radius="16" />
<Skeleton height="1.5rem" width="12rem" radius="8" />
```

radius 매핑:
- `rounded` / `rounded-lg` → `radius="8"`
- `rounded-xl` / `rounded-2xl` → `radius="16"`
- `rounded-full` → `radius="full"`

**Step 1: `.skeleton` CSS 클래스 사용 → `<Skeleton>` 컴포넌트 교체**

**Step 2: index.css에서 `.skeleton` CSS 정의는 유지** (다른 곳에서 사용될 수 있으므로)

**Step 3: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: 로딩 플레이스홀더 Seed Skeleton 교체"
```

---

## Task 7: Divider 교체 — 구분선 (~5개, 핵심만)

**Files:**
- Modify: `frontend/src/components/Navbar.tsx` (dropdown dividers)
- Modify: `frontend/src/pages/LoginPage.tsx` (OAuth divider)
- Modify: `frontend/src/pages/CreateJobPage.tsx` (form section divider)

28개의 `border-t`/`border-b` 중, 명확한 **섹션 구분선** 역할만 교체.
카드 내부 보더나 스타일링 일부인 것은 유지.

**교체 규칙:**

```tsx
import { Divider } from '../../seed-design/ui'

// Before
<div className="border-t border-[--color-border-default] my-4" />

// After
<Divider />
```

**Step 1: 명확한 섹션 구분선만 `<Divider>` 교체**

**Step 2: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: 섹션 구분선 Seed Divider 교체 (3파일)"
```

---

## Task 8: ProgressCircle 교체 — 로딩 스피너 (5개)

**Files:**
- Modify: `frontend/src/components/FileUploadField.tsx` (SVG spinner)
- Modify: `frontend/src/pages/CreateJobPage.tsx` (submit spinner)
- Modify: `frontend/src/pages/AuthCallbackPage.tsx` (CSS border spinner)
- Modify: `frontend/src/pages/JobStatusPage.tsx` (2 spinners)

**교체 규칙:**

```tsx
import { ProgressCircle } from '../../seed-design/ui'

// Before — SVG animate-spin
<svg className="animate-spin h-5 w-5 text-white" ...>
  <circle ... />
</svg>

// After
<ProgressCircle size="medium" tone="inherit" />

// Before — CSS border spinner (full-page loading)
<div className="h-12 w-12 rounded-full border-4 border-em-200 border-t-em-600 animate-spin" />

// After
<ProgressCircle size="large" tone="brand" />
```

size 매핑: `h-4 w-4` → `"small"`, `h-5 w-5` → `"medium"`, `h-8+ w-8+` → `"large"`

**주의:** ActionButton의 `loading` prop이 이미 ProgressCircle을 사용하므로, 버튼 내부 spinner는 Task 3-4에서 이미 제거됨. 여기서는 독립 스피너만 교체.

**Step 1: SVG/CSS spinner → `<ProgressCircle>` 교체**

**Step 2: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: 로딩 스피너 Seed ProgressCircle 교체 (4파일)"
```

---

## Task 9: TextField 교체 — 텍스트 입력 (3파일)

**Files:**
- Modify: `frontend/src/pages/CreateJobPage.tsx` (textarea JD, LinkedIn URL, Git URL)
- Modify: `frontend/src/pages/SettingsPage.tsx` (display name input)
- Modify: `frontend/src/components/GitHubRepoSelector.tsx` (search input)

**교체 규칙:**

```tsx
import { TextFieldRoot, TextFieldInput, TextFieldTextarea } from '../../seed-design/ui'

// Before — <input>
<input
  type="text"
  value={displayName}
  onChange={(e) => setDisplayName(e.target.value)}
  className="w-full rounded-lg border border-[--color-border-default] px-3 py-2 text-sm focus:border-[--color-border-accent] ..."
/>

// After
<TextFieldRoot variant="outline">
  <TextFieldInput
    value={displayName}
    onChange={(e) => setDisplayName(e.target.value)}
  />
</TextFieldRoot>

// Before — <textarea>
<textarea
  value={jobDescription}
  onChange={(e) => setJobDescription(e.target.value)}
  className="w-full rounded-lg border ... min-h-[120px]"
  rows={6}
/>

// After
<TextFieldRoot variant="outline">
  <TextFieldTextarea
    value={jobDescription}
    onChange={(e) => setJobDescription(e.target.value)}
    rows={6}
  />
</TextFieldRoot>
```

**주의:**
- `<input type="file">` (FileUploadField)는 교체하지 않음 — Seed Design에 파일 입력 컴포넌트 없음
- `<select>` 드롭다운은 교체하지 않음 — Seed Design SelectBox는 모바일용 시트 기반
- TextField에 label이 필요하면 `<label>` 요소를 별도로 유지

**Step 1: `<input type="text">` / `<textarea>` → `<TextFieldRoot>` + `<TextFieldInput>` / `<TextFieldTextarea>` 교체**

**Step 2: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: 텍스트 입력 Seed TextField 교체 (3파일)"
```

---

## Task 10: Avatar 교체 — 프로필 이미지 (2파일)

**Files:**
- Modify: `frontend/src/components/Navbar.tsx` (user avatar in nav)
- Modify: `frontend/src/components/tabs/IntelBriefTab.tsx` (candidate avatar)

**교체 규칙:**

```tsx
import { AvatarRoot, AvatarImage, AvatarFallback } from '../../seed-design/ui'

// Before
<div className="h-8 w-8 rounded-full bg-em-100 flex items-center justify-center ring-2 ring-em-500/30">
  {user?.picture ? (
    <img src={user.picture} className="h-8 w-8 rounded-full" />
  ) : (
    <span className="text-sm font-medium text-em-700">
      {user?.display_name?.[0]?.toUpperCase()}
    </span>
  )}
</div>

// After
<AvatarRoot size="36">
  <AvatarImage src={user?.picture} alt={user?.display_name} />
  <AvatarFallback>
    {user?.display_name?.[0]?.toUpperCase()}
  </AvatarFallback>
</AvatarRoot>
```

IntelBriefTab의 큰 아바타:
```tsx
<AvatarRoot size="64">
  <AvatarImage src={candidate.avatar_url} alt={candidate.name} />
  <AvatarFallback>{candidate.name?.[0]}</AvatarFallback>
</AvatarRoot>
```

**Step 1: 아바타 패턴 → `<AvatarRoot>` 교체**

**Step 2: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: 프로필 이미지 Seed Avatar 교체 (2파일)"
```

---

## Task 11: Callout 교체 — 알림/경고 박스

**Files:**
- Modify: files containing info/warning/alert boxes (survey after Task 3-10 for remaining instances)

**교체 규칙:**

```tsx
import { CalloutRoot, CalloutContent, CalloutTitle, CalloutDescription } from '../../seed-design/ui'

// Before — info box
<div className="bg-em-50 border border-em-200 rounded-lg p-4">
  <p className="text-sm font-medium text-em-800">알림 제목</p>
  <p className="text-sm text-em-700 mt-1">알림 내용</p>
</div>

// After
<CalloutRoot tone="informative">
  <CalloutContent>
    <CalloutTitle>알림 제목</CalloutTitle>
    <CalloutDescription>알림 내용</CalloutDescription>
  </CalloutContent>
</CalloutRoot>

// Warning box
<CalloutRoot tone="warning">
  <CalloutContent>
    <CalloutDescription>{t('warning_message')}</CalloutDescription>
  </CalloutContent>
</CalloutRoot>
```

tone 매핑:
- 정보성 (blue/em-tinted bg) → `tone="informative"`
- 경고 (amber bg) → `tone="warning"`
- 에러 (red bg) → `tone="critical"`
- 성공 (green bg) → `tone="positive"`

**Step 1: 알림/경고 박스 → `<CalloutRoot>` 교체**

**Step 2: TypeScript 컴파일 확인**

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: 알림/경고 박스 Seed Callout 교체"
```

---

## Task 12: Checkbox 교체 — 레포/질문 선택

**Files:**
- Modify: `frontend/src/components/GitHubRepoSelector.tsx` (repo checkboxes)

**교체 규칙:**

```tsx
import { CheckboxRoot, CheckboxControl, CheckboxIndicator, CheckboxLabel, CheckboxHiddenInput } from '../../seed-design/ui'

// Before
<label className="flex items-center gap-2 cursor-pointer">
  <input type="checkbox" checked={selected} onChange={toggle} className="..." />
  <span>repo-name</span>
</label>

// After
<CheckboxRoot checked={selected} onCheckedChange={toggle}>
  <CheckboxHiddenInput />
  <CheckboxControl>
    <CheckboxIndicator />
  </CheckboxControl>
  <CheckboxLabel>repo-name</CheckboxLabel>
</CheckboxRoot>
```

**Step 1: `<input type="checkbox">` → `<CheckboxRoot>` 교체**

**Step 2: TypeScript 컴파일 확인**

**Step 3: Commit**

```bash
git add frontend/src/
git commit -m "feat: 체크박스 Seed Checkbox 교체"
```

---

## Task 13: Tabs 교체 — ResultPage 탭 네비게이션

**Files:**
- Modify: `frontend/src/pages/ResultPage.tsx`

이 작업이 가장 복잡함. ResultPage에는 V2 탭(4개)과 V1 탭(3개) 두 세트가 있음.
기존 커스텀 `role="tab"` 구현 + 키보드 네비게이션을 Seed Tabs로 대체.

**교체 규칙:**

```tsx
import { TabsRoot, TabsList, TabsTrigger, TabsContent, TabsIndicator } from '../../seed-design/ui'

// Before (V2 tabs)
<div role="tablist" className="flex overflow-x-auto scrollbar-hide border-b ...">
  {['intel', 'analysis', 'interview', 'decision'].map(tab => (
    <button
      key={tab}
      id={`tab-${tab}`}
      role="tab"
      aria-selected={activeTab === tab}
      onClick={() => setActiveTab(tab)}
      onKeyDown={(e) => handleTabKeyDown(e, v2TabIds)}
      className={activeTab === tab ? 'border-b-2 border-em-500 text-em-700' : '...'}
    >
      {t(`tab_${tab}`)}
    </button>
  ))}
</div>
{activeTab === 'intel' && <IntelBriefTab ... />}
{activeTab === 'analysis' && <DeepAnalysisTab ... />}
...

// After
<TabsRoot
  value={activeTab}
  onValueChange={(v) => setActiveTab(v as ResultTab)}
  triggerLayout="hug"
>
  <TabsList>
    <TabsTrigger value="intel">{t('tab_intel')}</TabsTrigger>
    <TabsTrigger value="analysis">{t('tab_analysis')}</TabsTrigger>
    <TabsTrigger value="interview">{t('tab_interview')}</TabsTrigger>
    <TabsTrigger value="decision">{t('tab_decision')}</TabsTrigger>
    <TabsIndicator />
  </TabsList>
  <TabsContent value="intel"><IntelBriefTab ... /></TabsContent>
  <TabsContent value="analysis"><DeepAnalysisTab ... /></TabsContent>
  <TabsContent value="interview"><LiveInterviewTab ... /></TabsContent>
  <TabsContent value="decision"><DecisionTab ... /></TabsContent>
</TabsRoot>
```

**주의:**
- Seed Tabs는 키보드 네비게이션 내장 → `handleTabKeyDown` 함수 제거 가능
- V1 탭도 동일 패턴으로 교체
- `scrollbar-hide` 클래스 유지 필요 시 TabsList에 className 추가
- `overflow-x-auto` 모바일 대응은 Seed TabsList가 자동 처리

**Step 1: V2 탭 구현 → `<TabsRoot>` 교체**

**Step 2: V1 탭 구현 → `<TabsRoot>` 교체**

**Step 3: `handleTabKeyDown` 함수 제거 (Seed Tabs 내장)**

**Step 4: TypeScript 컴파일 확인**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`

**Step 5: 브라우저에서 탭 전환 확인** — 키보드 Arrow Left/Right, 클릭, 활성 인디케이터

**Step 6: Commit**

```bash
git add frontend/src/pages/ResultPage.tsx
git commit -m "feat: ResultPage 탭 네비게이션 Seed Tabs 교체"
```

---

## Task 14: Dialog 교체 — EmailNotificationModal

**Files:**
- Modify: `frontend/src/components/EmailNotificationModal.tsx`
- Modify: `frontend/src/pages/CreateJobPage.tsx` (Dialog 트리거 연결)

**교체 규칙:**

```tsx
import {
  DialogRoot, DialogPositioner, DialogBackdrop, DialogContent,
  DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogAction,
} from '../../seed-design/ui'
import { ActionButton } from '../../seed-design/ui'

// Before
export function EmailNotificationModal({ onAccept, onDecline }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/60 backdrop-blur-sm">
      <div className="bg-[--color-bg-surface] rounded-xl shadow-2xl p-6 max-w-sm mx-4">
        <h3>...</h3>
        <p>...</p>
        <div className="flex gap-3">
          <button onClick={onDecline}>...</button>
          <button onClick={onAccept}>...</button>
        </div>
      </div>
    </div>
  )
}

// After
export function EmailNotificationModal({ open, onAccept, onDecline }: Props) {
  return (
    <DialogRoot open={open} onOpenChange={(e) => { if (!e.open) onDecline() }}>
      <DialogPositioner>
        <DialogBackdrop />
        <DialogContent>
          <DialogHeader>
            <div className="w-12 h-12 bg-em-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-em-700" ...>...</svg>
            </div>
            <DialogTitle>{t('email_notification_title')}</DialogTitle>
            <DialogDescription>{t('email_notification_desc')}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogAction onClick={onDecline}>
              <ActionButton variant="neutralOutline">{t('email_notification_no')}</ActionButton>
            </DialogAction>
            <DialogAction onClick={onAccept}>
              <ActionButton variant="brandSolid">{t('email_notification_yes')}</ActionButton>
            </DialogAction>
          </DialogFooter>
        </DialogContent>
      </DialogPositioner>
    </DialogRoot>
  )
}
```

**주의:**
- Props에 `open: boolean` 추가 필요
- CreateJobPage에서 모달 상태 관리 방식을 `open` prop으로 전달하도록 수정
- Dialog는 ESC 키로 닫기, backdrop 클릭으로 닫기 자동 지원

**Step 1: EmailNotificationModal Props + 구조 교체**

**Step 2: CreateJobPage에서 Dialog 연결 수정**

**Step 3: TypeScript 컴파일 확인**

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: EmailNotificationModal Seed Dialog 교체"
```

---

## Task 15: 최종 검증 + 정리

**Files:**
- Modify: `frontend/src/index.css` (필요 시 사용하지 않는 CSS 정리)

**Step 1: TypeScript 전체 빌드**

Run: `cd /home/sabyun/IaaS/frontend && npx tsc --noEmit`
Expected: 0 errors

**Step 2: Vite 프로덕션 빌드**

Run: `cd /home/sabyun/IaaS/frontend && npm run build`
Expected: 빌드 성공, 번들 사이즈 확인

**Step 3: Grep 검증 — 교체 완료 확인**

```bash
# 커스텀 spinner가 남아있지 않은지
grep -r "animate-spin" frontend/src/ --include="*.tsx" | grep -v node_modules

# 커스텀 skeleton CSS 클래스 사용이 없는지
grep -r 'className="skeleton' frontend/src/ --include="*.tsx"

# seed-design import가 올바른지
grep -r "from.*seed-design/ui" frontend/src/ --include="*.tsx"
```

**Step 4: 브라우저 시각 테스트**

Docker 재빌드 후 각 페이지 확인:
1. `/demo/login` — 버튼, 입력 필드
2. `/demo/interview` — 목록, 배지, 버튼
3. `/demo/interview/new` — 폼, 텍스트 필드, 체크박스
4. `/demo/interview/{id}/status` — 스피너, 진행 상태
5. `/demo/interview/{id}/result` — 탭, 배지, 아바타, 버튼, 구분선
6. `/demo/settings` — 입력 필드, 버튼

**Step 5: index.css 정리 (선택)**

사용하지 않는 CSS 정의가 있으면 제거:
- `.skeleton` 클래스 (Seed Skeleton으로 전면 교체된 경우)
- `.tab-underline` 관련 (Seed Tabs 사용 시)

**Step 6: 최종 Commit**

```bash
git add -A
git commit -m "chore: Seed Design 마이그레이션 최종 검증 + CSS 정리"
```

---

## 실행 순서 요약

```
Task 1:  index.css carrot 오버라이드 ─────────┐
Task 2:  스니펫 10개 생성 ─────────────────────┤
Task 3:  ActionButton — CTA/Submit (7파일) ────┤
Task 4:  ActionButton — 탭 내부 (6파일) ───────┤ Phase 1: Simple
Task 5:  Badge (6파일) ────────────────────────┤
Task 6:  Skeleton (3파일) ─────────────────────┤
Task 7:  Divider (3파일) ──────────────────────┤
Task 8:  ProgressCircle (4파일) ───────────────┘
Task 9:  TextField (3파일) ────────────────────┐
Task 10: Avatar (2파일) ───────────────────────┤ Phase 2: Compound
Task 11: Callout (N파일) ──────────────────────┤
Task 12: Checkbox (1파일) ─────────────────────┘
Task 13: Tabs — ResultPage ────────────────────┐ Phase 3: Complex
Task 14: Dialog — EmailNotificationModal ──────┘
Task 15: 최종 검증 + 정리
```

총 15 Tasks, 예상 커밋 15개.
