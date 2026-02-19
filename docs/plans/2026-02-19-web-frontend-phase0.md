# Web Frontend Phase 0: 모노레포 스캐폴딩 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** pnpm 모노레포 + Seed Design 기반 디자인 시스템으로 3패키지 프론트엔드 스캐폴딩 완성

**Architecture:** 기존 단일 SPA(`frontend/`)를 pnpm workspace 모노레포로 전환. @jittda/ui(공유 디자인 시스템), @jittda/public(지원자 앱), @jittda/admin(관리자 앱) 3패키지. Seed Design CLI로 컴포넌트 베이스 확보 후 Jittda 브랜드(Navy+Orange) 토큰 오버라이드.

**Tech Stack:** React 19, Vite 7, Tailwind CSS 4, pnpm workspace, @seed-design/css + @seed-design/vite-plugin, react-router-dom 7, react-i18next, TypeScript 5.9

---

## 사전 조건

- Node.js 20+, pnpm 9+ 설치
- 기존 `frontend/` 디렉토리 존재 (현재 단일 SPA)
- 설계 문서: `docs/plans/2026-02-19-web-frontend-design.md`
- 디자인 시스템 스킬: `.claude/skills/jittda-design-system/SKILL.md`

## 의존성 그래프

```
Task 1 (pnpm workspace 초기화)
  └── Task 2 (@jittda/ui 패키지)
        ├── Task 3 (Seed Design 설치 + 토큰)
        │     └── Task 4 (Jittda 색상 오버라이드)
        └── Task 5 (@jittda/public 패키지 — 빈 껍데기)
              └── Task 6 (@jittda/admin 패키지 — 기존 코드 이전)
                    └── Task 7 (통합 빌드 + 검증)
                          └── Task 8 (커밋)
```

---

### Task 1: pnpm workspace 초기화

**Files:**
- Create: `frontend/pnpm-workspace.yaml`
- Create: `frontend/package.json` (루트 — 기존 것을 루트용으로 교체)
- Create: `frontend/tsconfig.base.json`
- Backup: `frontend/package.json` → `frontend/package.json.bak`

**Step 1: 기존 package.json 백업**

```bash
cp frontend/package.json frontend/package.json.bak
```

**Step 2: pnpm-workspace.yaml 생성**

```yaml
# frontend/pnpm-workspace.yaml
packages:
  - "packages/*"
```

**Step 3: 루트 package.json 생성**

```json
{
  "name": "@jittda/frontend",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "pnpm --parallel -r run dev",
    "dev:public": "pnpm --filter @jittda/public dev",
    "dev:admin": "pnpm --filter @jittda/admin dev",
    "build": "pnpm -r run build",
    "build:public": "pnpm --filter @jittda/public build",
    "build:admin": "pnpm --filter @jittda/admin build",
    "lint": "pnpm -r run lint",
    "typecheck": "pnpm -r run typecheck",
    "clean": "pnpm -r run clean"
  },
  "engines": {
    "node": ">=20",
    "pnpm": ">=9"
  }
}
```

**Step 4: tsconfig.base.json 생성**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowImportingTsExtensions": true,
    "noEmit": true,
    "isolatedModules": true,
    "resolveJsonModule": true
  }
}
```

**Step 5: 빈 packages 디렉토리 생성**

```bash
mkdir -p frontend/packages/ui frontend/packages/public-app frontend/packages/admin-app
```

**Step 6: 검증**

```bash
cd frontend && ls pnpm-workspace.yaml tsconfig.base.json package.json packages/
```
Expected: 3개 파일 + packages/ 하위 3개 폴더 존재

**Step 7: 커밋**

```bash
but commit cs -m "chore: pnpm workspace 모노레포 초기화"
```

---

### Task 2: @jittda/ui 패키지 스캐폴딩

**Files:**
- Create: `frontend/packages/ui/package.json`
- Create: `frontend/packages/ui/tsconfig.json`
- Create: `frontend/packages/ui/src/index.ts` (barrel export)
- Create: `frontend/packages/ui/src/styles/tokens.css` (디자인 토큰)
- Create: `frontend/packages/ui/src/styles/index.css` (Tailwind 진입점)

**Step 1: package.json 생성**

```json
{
  "name": "@jittda/ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "main": "./src/index.ts",
  "types": "./src/index.ts",
  "exports": {
    ".": "./src/index.ts",
    "./styles": "./src/styles/index.css",
    "./tokens": "./src/styles/tokens.css"
  },
  "peerDependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "dependencies": {
    "@seed-design/css": "^0.0.12"
  },
  "devDependencies": {
    "typescript": "~5.9.3"
  },
  "scripts": {
    "typecheck": "tsc --noEmit",
    "clean": "rm -rf dist"
  }
}
```

**Step 2: tsconfig.json 생성**

```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src"]
}
```

**Step 3: barrel export 생성**

```typescript
// frontend/packages/ui/src/index.ts
// @jittda/ui — 공유 디자인 시스템
// 컴포넌트는 Task 3 이후 점진적으로 추가

export {};
```

**Step 4: 디자인 토큰 CSS 생성 (Seed Design 2-tier 구조)**

```css
/* frontend/packages/ui/src/styles/tokens.css */
/* ═══════════════════════════════════════════════════
   Jittda Design Tokens (Seed Design 2-tier 구조)
   Brand: Navy #1B3A5C + Orange #E87E24
   참조: .claude/skills/jittda-design-system/SKILL.md
   ═══════════════════════════════════════════════════ */

/* ─── Tier 1: Scale Tokens (raw values) ─── */
@theme {
  /* Navy palette (primary) */
  --color-navy-50: #f0f4f8;
  --color-navy-100: #d9e2ec;
  --color-navy-200: #bcccdc;
  --color-navy-300: #9fb3c8;
  --color-navy-400: #6d8eab;
  --color-navy-500: #3e6b8a;
  --color-navy-600: #2d5577;
  --color-navy-700: #1f4060;
  --color-navy-800: #1B3A5C;
  --color-navy-900: #142d47;
  --color-navy-950: #0d1f33;

  /* Brand Orange palette (accent) */
  --color-brand-50: #fff8f0;
  --color-brand-100: #feebd0;
  --color-brand-200: #fdd5a0;
  --color-brand-300: #f9b86a;
  --color-brand-400: #f29a3e;
  --color-brand-500: #E87E24;
  --color-brand-600: #cc6a17;
  --color-brand-700: #a85414;
  --color-brand-800: #874316;
  --color-brand-900: #6e3815;
  --color-brand-950: #3d1c08;

  /* Neutral (Tailwind gray 기반) */
  --color-gray-50: #f9fafb;
  --color-gray-100: #f3f4f6;
  --color-gray-200: #e5e7eb;
  --color-gray-300: #d1d5db;
  --color-gray-400: #9ca3af;
  --color-gray-500: #6b7280;
  --color-gray-600: #4b5563;
  --color-gray-700: #374151;
  --color-gray-800: #1f2937;
  --color-gray-900: #111827;
  --color-gray-950: #030712;

  /* Status colors */
  --color-red-50: #fef2f2;
  --color-red-500: #ef4444;
  --color-red-600: #dc2626;
  --color-green-50: #f0fdf4;
  --color-green-500: #22c55e;
  --color-green-600: #16a34a;
  --color-yellow-50: #fefce8;
  --color-yellow-500: #eab308;

  /* Shadows */
  --shadow-card: 0 1px 3px 0 rgba(27, 58, 92, 0.06), 0 1px 2px -1px rgba(27, 58, 92, 0.06);
  --shadow-card-hover: 0 4px 12px -2px rgba(27, 58, 92, 0.10), 0 2px 6px -2px rgba(27, 58, 92, 0.06);
  --shadow-elevated: 0 10px 25px -5px rgba(27, 58, 92, 0.12), 0 8px 10px -6px rgba(27, 58, 92, 0.06);
}

/* ─── Tier 2: Semantic Tokens (intent-based) ─── */
:root {
  /* Backgrounds */
  --color-bg-primary: var(--color-navy-50);
  --color-bg-surface: #ffffff;
  --color-bg-surface-hover: var(--color-navy-100);
  --color-bg-accent: var(--color-brand-500);
  --color-bg-accent-hover: var(--color-brand-600);
  --color-bg-brand: var(--color-navy-800);
  --color-bg-brand-hover: var(--color-navy-700);
  --color-bg-neutral: var(--color-gray-100);
  --color-bg-danger: var(--color-red-50);
  --color-bg-success: var(--color-green-50);
  --color-bg-warning: var(--color-yellow-50);

  /* Text */
  --color-text-primary: var(--color-navy-900);
  --color-text-secondary: var(--color-navy-600);
  --color-text-tertiary: var(--color-navy-400);
  --color-text-on-accent: #ffffff;
  --color-text-on-brand: #ffffff;
  --color-text-accent: var(--color-brand-600);
  --color-text-danger: var(--color-red-600);
  --color-text-success: var(--color-green-600);

  /* Borders */
  --color-border-default: var(--color-navy-200);
  --color-border-strong: var(--color-navy-400);
  --color-border-accent: var(--color-brand-500);

  /* Focus */
  --color-focus-ring: var(--color-navy-800);

  /* Typography */
  --font-sans: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, 'Helvetica Neue', sans-serif;
}

/* Dark mode (future) */
@media (prefers-color-scheme: dark) {
  :root[data-theme="auto"],
  :root[data-theme="dark"] {
    --color-bg-primary: var(--color-navy-950);
    --color-bg-surface: var(--color-navy-900);
    --color-bg-surface-hover: var(--color-navy-800);
    --color-text-primary: var(--color-gray-100);
    --color-text-secondary: var(--color-gray-300);
    --color-text-tertiary: var(--color-gray-500);
    --color-border-default: var(--color-navy-700);
    --color-border-strong: var(--color-navy-500);
  }
}
```

**Step 5: Tailwind 진입점 CSS 생성**

```css
/* frontend/packages/ui/src/styles/index.css */
@import "tailwindcss";
@import "@seed-design/css/base.css";
@import "./tokens.css";

/* Focus ring */
*:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Skip to content */
.skip-link {
  position: absolute;
  left: -9999px;
  top: 0;
  z-index: 999;
  padding: 0.5rem 1rem;
  background: var(--color-bg-brand);
  color: var(--color-text-on-brand);
  font-size: 0.875rem;
}
.skip-link:focus { left: 0; }

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fadeIn { animation: fadeIn 0.4s ease-out forwards; }

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.animate-slideDown { animation: slideDown 0.2s ease-out forwards; }

/* Scrollbar (navy-tinted) */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--color-navy-200); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--color-navy-400); }

/* Card hover */
.card-hover { transition: transform 0.2s ease, box-shadow 0.2s ease; }
.card-hover:hover { transform: translateY(-2px); box-shadow: var(--shadow-card-hover); }

/* Tab underline */
.tab-underline { position: relative; }
.tab-underline::after {
  content: '';
  position: absolute;
  bottom: -1px; left: 0; width: 0; height: 2px;
  background: linear-gradient(to right, var(--color-navy-800), var(--color-brand-500));
  transition: width 0.3s ease;
  border-radius: 1px;
}
.tab-underline.active::after { width: 100%; }

/* Skeleton */
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
.skeleton {
  background: linear-gradient(90deg, var(--color-navy-50) 25%, var(--color-navy-100) 50%, var(--color-navy-50) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 0.5rem;
}

/* Utilities */
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
.scrollbar-hide::-webkit-scrollbar { display: none; }

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .animate-fadeIn, .animate-slideDown { animation: none; opacity: 1; transform: none; }
  .card-hover { transition: none; }
  .tab-underline::after { transition: none; }
  .skeleton { animation: none; }
}

/* Print */
@media print {
  body { background: white !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  nav, button, .no-print { display: none !important; }
  .shadow { box-shadow: none !important; border: 1px solid var(--color-navy-100); }
  .max-w-5xl, .max-w-2xl { max-width: 100% !important; }
  .rounded-lg { break-inside: avoid; }
}
```

**Step 6: 검증**

```bash
ls frontend/packages/ui/package.json frontend/packages/ui/tsconfig.json frontend/packages/ui/src/index.ts frontend/packages/ui/src/styles/tokens.css frontend/packages/ui/src/styles/index.css
```
Expected: 5개 파일 모두 존재

**Step 7: 커밋**

```bash
but commit cs -m "feat: @jittda/ui 패키지 스캐폴딩 + Seed 2-tier 토큰"
```

---

### Task 3: Seed Design CLI 설치 + 컴포넌트 추가

**Files:**
- Create: `frontend/packages/ui/seed-design.json`
- Create: `frontend/packages/ui/seed-design/` (CLI가 생성하는 컴포넌트 소스)

**Step 1: pnpm으로 Seed Design 의존성 설치**

```bash
cd frontend && pnpm add -w @seed-design/css && pnpm add -Dw @seed-design/vite-plugin vite-tsconfig-paths
```

**Step 2: Seed Design CLI 초기화 (ui 패키지)**

```bash
cd frontend/packages/ui && npx @seed-design/cli@latest init -y
```

Expected: `seed-design.json` 생성

**Step 3: seed-design.json 수정**

```json
{
  "rsc": false,
  "tsx": true,
  "path": "./src/seed-design"
}
```

**Step 4: 핵심 컴포넌트 추가**

```bash
cd frontend/packages/ui && npx @seed-design/cli@latest add button text-field select-box checkbox
```

Interactive 프롬프트에서 overwrite 선택.
Expected: `src/seed-design/` 아래 컴포넌트 소스 생성

**Step 5: barrel export에 Seed 컴포넌트 추가**

```typescript
// frontend/packages/ui/src/index.ts
// @jittda/ui — 공유 디자인 시스템 (Seed Design 기반)

// Seed Design 컴포넌트 (소스 복사, 커스터마이징 가능)
export * from './seed-design/ui/button';
export * from './seed-design/ui/text-field';
export * from './seed-design/ui/select-box';
export * from './seed-design/ui/checkbox';
```

> Note: CLI가 생성하는 정확한 경로는 실행 후 확인 필요. `src/seed-design/` 아래 구조에 맞게 조정.

**Step 6: 검증**

```bash
ls frontend/packages/ui/seed-design.json
ls frontend/packages/ui/src/seed-design/
```
Expected: seed-design.json + 컴포넌트 폴더들

**Step 7: 커밋**

```bash
but commit cs -m "feat: Seed Design CLI 초기화 + 기본 컴포넌트 추가"
```

---

### Task 4: @jittda/public 패키지 스캐폴딩

**Files:**
- Create: `frontend/packages/public-app/package.json`
- Create: `frontend/packages/public-app/tsconfig.json`
- Create: `frontend/packages/public-app/tsconfig.app.json`
- Create: `frontend/packages/public-app/tsconfig.node.json`
- Create: `frontend/packages/public-app/vite.config.ts`
- Create: `frontend/packages/public-app/index.html`
- Create: `frontend/packages/public-app/src/main.tsx`
- Create: `frontend/packages/public-app/src/App.tsx`

**Step 1: package.json 생성**

```json
{
  "name": "@jittda/public",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router-dom": "^7.13.0",
    "i18next": "^25.8.0",
    "react-i18next": "^16.5.4",
    "@jittda/ui": "workspace:*"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.1.1",
    "@seed-design/vite-plugin": "latest",
    "vite-tsconfig-paths": "latest",
    "vite": "^7.2.4",
    "typescript": "~5.9.3",
    "tailwindcss": "^4.1.18",
    "@tailwindcss/vite": "^4.1.18"
  }
}
```

**Step 2: tsconfig 파일 3개 생성**

```json
// frontend/packages/public-app/tsconfig.json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

```json
// frontend/packages/public-app/tsconfig.app.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "paths": {
      "@jittda/ui": ["../ui/src"],
      "@jittda/ui/*": ["../ui/src/*"]
    }
  },
  "include": ["src"]
}
```

```json
// frontend/packages/public-app/tsconfig.node.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true
  },
  "include": ["vite.config.ts"]
}
```

**Step 3: vite.config.ts 생성**

```typescript
// frontend/packages/public-app/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    tsconfigPaths(),
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': { target: 'http://localhost:8000' },
    },
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-i18n': ['i18next', 'react-i18next'],
        },
      },
    },
  },
})
```

**Step 4: index.html 생성**

```html
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Jittda Careers</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 5: main.tsx + App.tsx 생성**

```tsx
// frontend/packages/public-app/src/main.tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@jittda/ui/styles'
import { App } from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
```

```tsx
// frontend/packages/public-app/src/App.tsx
import { Routes, Route } from 'react-router-dom'

function PlaceholderPage({ name }: { name: string }) {
  return (
    <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-8 text-center">
        <h1 className="text-2xl font-semibold text-[--color-text-primary]">{name}</h1>
        <p className="text-[--color-text-secondary] mt-2">이 페이지는 Phase 1에서 구현됩니다.</p>
      </div>
    </div>
  )
}

export function App() {
  return (
    <Routes>
      <Route path="/careers/:slug" element={<PlaceholderPage name="커리어 페이지" />} />
      <Route path="/careers/:slug/:jobId" element={<PlaceholderPage name="공고 상세" />} />
      <Route path="/careers/:slug/:jobId/apply" element={<PlaceholderPage name="지원 폼" />} />
      <Route path="/apply/confirm" element={<PlaceholderPage name="지원 확인" />} />
    </Routes>
  )
}
```

**Step 6: 검증**

```bash
ls frontend/packages/public-app/package.json frontend/packages/public-app/vite.config.ts frontend/packages/public-app/src/App.tsx
```
Expected: 모든 파일 존재

**Step 7: 커밋**

```bash
but commit cs -m "feat: @jittda/public 패키지 스캐폴딩 (4 라우트 플레이스홀더)"
```

---

### Task 5: @jittda/admin 패키지 스캐폴딩

**Files:**
- Create: `frontend/packages/admin-app/package.json`
- Create: `frontend/packages/admin-app/tsconfig.json`
- Create: `frontend/packages/admin-app/tsconfig.app.json`
- Create: `frontend/packages/admin-app/tsconfig.node.json`
- Create: `frontend/packages/admin-app/vite.config.ts`
- Create: `frontend/packages/admin-app/index.html`
- Create: `frontend/packages/admin-app/src/main.tsx`
- Create: `frontend/packages/admin-app/src/App.tsx`
- Move: `frontend/src/` → `frontend/packages/admin-app/src/` (기존 코드 이전)

**Step 1: package.json 생성**

```json
{
  "name": "@jittda/admin",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "test:e2e": "playwright test",
    "clean": "rm -rf dist"
  },
  "dependencies": {
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router-dom": "^7.13.0",
    "tailwindcss": "^4.1.18",
    "@tailwindcss/vite": "^4.1.18",
    "i18next": "^25.8.0",
    "react-i18next": "^16.5.4",
    "@jittda/ui": "workspace:*"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.1.1",
    "@seed-design/vite-plugin": "latest",
    "vite-tsconfig-paths": "latest",
    "vite": "^7.2.4",
    "typescript": "~5.9.3",
    "@playwright/test": "^1.50.0",
    "eslint": "^9.39.1"
  }
}
```

**Step 2: tsconfig 파일 3개 생성** (public-app과 동일 구조)

```json
// frontend/packages/admin-app/tsconfig.json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

```json
// frontend/packages/admin-app/tsconfig.app.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "paths": {
      "@jittda/ui": ["../ui/src"],
      "@jittda/ui/*": ["../ui/src/*"]
    }
  },
  "include": ["src"]
}
```

```json
// frontend/packages/admin-app/tsconfig.node.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true
  },
  "include": ["vite.config.ts"]
}
```

**Step 3: vite.config.ts 생성**

```typescript
// frontend/packages/admin-app/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    tsconfigPaths(),
  ],
  server: {
    port: 3001,
    proxy: {
      '/api': { target: 'http://localhost:8000' },
      '/auth': { target: 'http://localhost:8000' },
    },
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-i18n': ['i18next', 'react-i18next'],
        },
      },
    },
  },
})
```

**Step 4: 기존 소스코드 이전**

```bash
# 기존 frontend/src/를 admin-app/src/로 복사
cp -r frontend/src/* frontend/packages/admin-app/src/

# 기존 설정 파일 복사
cp frontend/index.html frontend/packages/admin-app/index.html
cp frontend/eslint.config.js frontend/packages/admin-app/eslint.config.js

# E2E 테스트 복사
cp -r frontend/e2e frontend/packages/admin-app/e2e
cp frontend/playwright.config.ts frontend/packages/admin-app/playwright.config.ts

# 정적 자산 복사
cp -r frontend/public frontend/packages/admin-app/public
```

**Step 5: admin-app의 index.css를 @jittda/ui 스타일로 교체**

`frontend/packages/admin-app/src/index.css` 내용을 다음으로 교체:

```css
/* @jittda/ui 공유 스타일 사용 — 토큰은 @jittda/ui/styles에 정의 */
@import "@jittda/ui/styles";
```

또는 `main.tsx`에서 import:

```tsx
// frontend/packages/admin-app/src/main.tsx (기존 import 수정)
import '@jittda/ui/styles'  // 기존 './index.css' 대신
```

**Step 6: 검증 — 파일 존재 확인**

```bash
ls frontend/packages/admin-app/package.json frontend/packages/admin-app/vite.config.ts frontend/packages/admin-app/src/App.tsx frontend/packages/admin-app/src/main.tsx
```
Expected: 모든 파일 존재

**Step 7: 커밋**

```bash
but commit cs -m "feat: @jittda/admin 패키지 스캐폴딩 — 기존 코드 이전"
```

---

### Task 6: pnpm install + 통합 빌드 검증

**Step 1: 의존성 설치**

```bash
cd frontend && pnpm install
```

Expected: node_modules 생성, workspace 링크 확인

**Step 2: workspace 링크 확인**

```bash
cd frontend && pnpm ls --depth 0 -r
```

Expected: `@jittda/ui`, `@jittda/public`, `@jittda/admin` 3개 패키지 표시

**Step 3: TypeScript 타입 체크**

```bash
cd frontend && pnpm typecheck
```

Expected: 에러 없음 (또는 기존 코드에서 경로 변경 관련 에러만)

**Step 4: public-app dev 서버 테스트**

```bash
cd frontend && pnpm dev:public
```

Expected: `http://localhost:3000`에서 플레이스홀더 페이지 표시
`/careers/test-company` 접속 시 "커리어 페이지" 플레이스홀더 렌더링

**Step 5: admin-app dev 서버 테스트**

```bash
cd frontend && pnpm dev:admin
```

Expected: `http://localhost:3001`에서 기존 관리자 앱 작동

**Step 6: 빌드 테스트**

```bash
cd frontend && pnpm build
```

Expected: `packages/public-app/dist/`, `packages/admin-app/dist/` 생성

> Note: 기존 코드의 import 경로 오류가 있을 수 있음. 필요시 수정 (index.css import, 상대 경로 등)

**Step 7: 커밋**

```bash
but commit cs -m "chore: pnpm workspace 통합 빌드 검증 완료"
```

---

### Task 7: 기존 frontend/ 루트 정리 + Docker 업데이트

**Step 1: 기존 루트 파일 보존/정리**

```bash
# 기존 src/는 admin-app으로 이전 완료 — 원본은 백업 후 삭제
# (이미 package.json.bak으로 백업됨)

# 기존 루트의 Vite/TS 설정은 더 이상 불필요
# 삭제 대상: frontend/vite.config.ts, frontend/tsconfig.app.json, frontend/tsconfig.node.json
# 보존: frontend/Dockerfile, frontend/nginx.conf (업데이트 필요)
```

**Step 2: Dockerfile 업데이트 (멀티앱 빌드)**

`frontend/Dockerfile`을 2개 앱 빌드 지원으로 수정:

```dockerfile
# frontend/Dockerfile
# ARG로 빌드 대상 선택
ARG APP=admin-app

# Stage 1: Build
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY packages/ packages/
RUN pnpm install --frozen-lockfile
ARG APP
RUN pnpm --filter @jittda/${APP} build

# Stage 2: Serve
FROM nginx:alpine
ARG APP
COPY --from=builder /app/packages/${APP}/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Step 3: docker-compose 업데이트는 Phase 0 범위 밖 (기록만)**

기존 `docker-compose.yml`의 `frontend` 서비스를 `frontend-admin` + `frontend-public`으로 분리하는 작업은 Phase 1에서 진행.

**Step 4: 커밋**

```bash
but commit cs -m "chore: 모노레포 전환 — 루트 정리 + Dockerfile 멀티앱"
```

---

### Task 8: 디자인 시스템 스킬 라우팅 등록 + 최종 커밋

**Files:**
- Modify: `.claude/skills/routing/SKILL.md` — jittda-design-system 등록
- Modify: `CLAUDE.md` — Auto-Routing 테이블에 추가

**Step 1: 라우팅에 디자인 시스템 스킬 등록**

CLAUDE.md Auto-Routing 테이블에 추가:

```
| UI, component, color, design | context7, magic | /jittda-design-system |
```

**Step 2: 최종 검증 — 전체 디렉토리 구조 확인**

```bash
find frontend/packages -maxdepth 3 -type f -name "*.json" -o -name "*.ts" -o -name "*.tsx" -o -name "*.css" -o -name "*.html" | sort
```

Expected 구조:
```
frontend/
├── pnpm-workspace.yaml
├── package.json (루트)
├── tsconfig.base.json
├── Dockerfile
├── packages/
│   ├── ui/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── seed-design.json
│   │   └── src/
│   │       ├── index.ts
│   │       ├── seed-design/   (Seed CLI가 생성)
│   │       └── styles/
│   │           ├── tokens.css
│   │           └── index.css
│   ├── public-app/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── vite.config.ts
│   │   ├── index.html
│   │   └── src/
│   │       ├── main.tsx
│   │       └── App.tsx
│   └── admin-app/
│       ├── package.json
│       ├── tsconfig.json
│       ├── vite.config.ts
│       ├── index.html
│       └── src/ (기존 frontend/src/ 이전)
```

**Step 3: 최종 커밋 + 태그**

```bash
but commit cs -m "feat(phase-0): 웹 프론트엔드 모노레포 스캐폴딩 완료

- pnpm workspace + 3패키지 (@jittda/ui, @jittda/public, @jittda/admin)
- Seed Design 2-tier 토큰 (Scale → Semantic) + Jittda 브랜드 오버라이드
- 기존 단일 SPA → admin-app으로 이전
- public-app 4라우트 플레이스홀더

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 완료 기준

- [ ] pnpm workspace에서 3패키지 인식 (`pnpm ls -r`)
- [ ] `pnpm dev:public` → localhost:3000 플레이스홀더 표시
- [ ] `pnpm dev:admin` → localhost:3001 기존 앱 작동
- [ ] `pnpm build` → 두 앱 dist/ 생성
- [ ] Semantic Token이 CSS에서 올바르게 적용
- [ ] TypeScript 타입 체크 통과

## 다음 단계 (Phase 1)

- Public App 4페이지 실제 구현 (CareersPage, JobDetailPage, ApplicationPage, ConfirmPage)
- Backend REST API 추가 (Company, Public, Application 엔드포인트)
- Docker Compose 2앱 분리
- Admin App에서 공유 컴포넌트를 @jittda/ui로 추출
