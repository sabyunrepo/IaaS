# Seed Design Component Migration — Design Document

**Goal:** 데모 앱의 커스텀 Tailwind UI를 Seed Design React 컴포넌트로 교체하여 디자인 시스템 통일

**Date:** 2026-02-20

---

## 1. 토큰 오버라이드 전략

Seed Design은 `--seed-color-palette-carrot-*` (당근마켓 오렌지)를 brand 색상으로 사용.
`index.css`에서 carrot 팔레트 전체를 에메랄드 값으로 오버라이드:

```css
:root {
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

모든 Seed 컴포넌트의 `variant="brandSolid"` 등이 자동으로 에메랄드 렌더링.

---

## 2. 교체 대상 (12개 컴포넌트)

### Phase 1 — Simple (바로 교체)

| Seed 컴포넌트 | 교체 대상 | 파일 수 | 인스턴스 |
|---|---|---|---|
| ActionButton | CTA/submit/cancel 버튼 | ~10파일 | ~20개 |
| Badge | StatusBadge, 태그 | ~5파일 | ~8개 |
| Skeleton | 로딩 플레이스홀더 | ~3파일 | ~3그룹 |
| Divider | border-t 구분선 | ~3파일 | ~5개 |

### Phase 2 — Compound (래퍼 작성)

| Seed 컴포넌트 | 교체 대상 | 파일 수 |
|---|---|---|
| TextField | input, textarea | CreateJob, Settings |
| Avatar | 유저 프로필 이미지 | Navbar, IntelBriefTab |
| Callout | 알림/경고/정보 박스 | ~6파일 |
| Switch | 설정 토글 | SettingsPage |
| Checkbox | 레포/질문 선택 | GitHubRepoSelector, LiveInterviewTab |
| ProgressCircle | 로딩 스피너 | CreateJob, FileUpload |

### Phase 3 — Complex (구조 변경)

| Seed 컴포넌트 | 교체 대상 | 파일 |
|---|---|---|
| Tabs | ResultPage 4탭 네비게이션 | ResultPage |
| Dialog | EmailNotificationModal | EmailNotificationModal |

---

## 3. Seed Design API 요약

### ActionButton
- `variant`: brandSolid | neutralSolid | neutralWeak | criticalSolid | brandOutline | neutralOutline | ghost
- `size`: xsmall | small | medium | large
- `loading`: boolean (LoadingIndicator 자동)

### Badge
- `variant`: weak | solid | outline
- `tone`: neutral | brand | informative | positive | warning | critical
- `size`: medium | large

### TextField (Compound)
- TextFieldRoot > TextFieldInput/TextFieldTextarea
- `variant`: outline | underline
- PrefixIcon/SuffixIcon 지원

### Dialog (Compound)
- DialogRoot > DialogTrigger + DialogPositioner > DialogBackdrop + DialogContent > Header/Title/Description/Footer/Action

### Tabs (Compound)
- TabsRoot > TabsList > TabsTrigger + TabsIndicator + TabsContent
- `triggerLayout`: fill | hug
- 키보드 nav 내장

### 기타
- Skeleton: `radius`, `tone`, `height`, `width`
- Divider: `orientation`, `color`, `thickness`
- Avatar: AvatarRoot > AvatarImage + AvatarFallback
- Callout: CalloutRoot > CalloutTitle + CalloutDescription (tone 지원)
- Switch: SwitchRoot > SwitchControl + SwitchThumb + SwitchLabel
- Checkbox: CheckboxRoot > CheckboxControl + CheckboxIndicator + CheckboxLabel
- ProgressCircle: ProgressCircleRoot > Track + Range

---

## 4. 보존 규칙

- 랜딩페이지(jittda-landingpage/) 제외
- Red/Green/Blue/Amber 시맨틱 상태 색상 유지
- 기존 em-*/ink-* 커스텀 토큰과 Seed 토큰 공존
- InlineBanner (deprecated) → Callout으로 대체
