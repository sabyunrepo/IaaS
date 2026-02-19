# Web Frontend Phase 0: 모노레포 스캐폴딩 구현 계획

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** pnpm 모노레포 + Seed Design 기반 디자인 시스템으로 3패키지 프론트엔드 스캐폴딩 완성

**Architecture:** `jittda/frontend/`에 pnpm workspace 모노레포 신규 생성 (Clean Slate). @jittda/ui(공유 디자인 시스템), @jittda/public(지원자 앱), @jittda/admin(관리자 앱) 3패키지. Seed Design CLI로 컴포넌트 베이스 확보 후 Jittda 브랜드(Navy+Orange) 토큰 오버라이드. 기존 `frontend/`는 READ-ONLY 참조만.

**Tech Stack:** React 19, Vite 7, Tailwind CSS 4, pnpm workspace, @seed-design/css + @seed-design/vite-plugin, react-router-dom 7, react-i18next, TypeScript 5.9

---

## 사전 조건

- Node.js 20+, pnpm 9+ 설치
- `jittda/` 디렉토리 하위에 신규 생성 (Clean Slate)
- 기존 `frontend/`는 READ-ONLY 참조용
- 설계 문서: `docs/plans/2026-02-19-web-frontend-design.md`
- 디자인 시스템 스킬: `.claude/skills/jittda-design-system/SKILL.md`

## 의존성 그래프

```
Task 1 (pnpm workspace 초기화)
  └── Task 2 (@jittda/ui 패키지)
        ├── Task 3 (Seed Design 설치 + 토큰)
        │     └── Task 4 (@jittda/public 패키지)
        │           └── Task 5 (@jittda/admin 패키지 — Clean Slate)
        │                 └── Task 6 (통합 빌드 + 검증)
        │                       └── Task 7 (Dockerfile)
        │                             └── Task 8 (스킬 등록 + 최종 커밋)
        └──
```

---

### Task 1: pnpm workspace 초기화

**Files:**
- Create: `jittda/frontend/pnpm-workspace.yaml`
- Create: `jittda/frontend/package.json`
- Create: `jittda/frontend/tsconfig.base.json`

**Step 1: 디렉토리 생성**

```bash
mkdir -p jittda/frontend/packages/ui jittda/frontend/packages/public-app jittda/frontend/packages/admin-app
```

**Step 2: pnpm-workspace.yaml 생성**

```yaml
# jittda/frontend/pnpm-workspace.yaml
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

**Step 5: 검증**

```bash
ls jittda/frontend/pnpm-workspace.yaml jittda/frontend/tsconfig.base.json jittda/frontend/package.json jittda/frontend/packages/
```
Expected: 3개 파일 + packages/ 하위 3개 폴더 존재

**Step 6: 커밋**

```bash
git add jittda/frontend/
git commit -m "chore: jittda/frontend pnpm workspace 모노레포 초기화"
```

---

### Task 2: @jittda/ui 패키지 스캐폴딩

**Files:**
- Create: `jittda/frontend/packages/ui/package.json`
- Create: `jittda/frontend/packages/ui/tsconfig.json`
- Create: `jittda/frontend/packages/ui/src/index.ts` (barrel export)
- Create: `jittda/frontend/packages/ui/src/styles/tokens.css` (디자인 토큰)
- Create: `jittda/frontend/packages/ui/src/styles/index.css` (Tailwind 진입점)

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
// jittda/frontend/packages/ui/src/index.ts
// @jittda/ui — 공유 디자인 시스템 (Seed Design 2-tier 토큰 기반)
// 컴포넌트는 점진적으로 추가

export {};
```

**Step 4: 디자인 토큰 CSS 생성 (Seed Design 2-tier 구조)**

```css
/* jittda/frontend/packages/ui/src/styles/tokens.css */
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

  /* Neutral */
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

  /* Status */
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
```

**Step 5: Tailwind 진입점 CSS 생성**

```css
/* jittda/frontend/packages/ui/src/styles/index.css */
@import "tailwindcss";
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
ls jittda/frontend/packages/ui/package.json jittda/frontend/packages/ui/tsconfig.json jittda/frontend/packages/ui/src/index.ts jittda/frontend/packages/ui/src/styles/tokens.css jittda/frontend/packages/ui/src/styles/index.css
```
Expected: 5개 파일 모두 존재

**Step 7: 커밋**

```bash
git add jittda/frontend/packages/ui/
git commit -m "feat: @jittda/ui 패키지 스캐폴딩 + Seed 2-tier 토큰"
```

---

### Task 3: Seed Design CLI 설치 + 컴포넌트 추가

**Files:**
- Create: `jittda/frontend/packages/ui/seed-design.json`
- Create: `jittda/frontend/packages/ui/seed-design/` (CLI가 생성하는 컴포넌트 소스)

**Step 1: pnpm으로 Seed Design 의존성 설치**

```bash
cd jittda/frontend && pnpm add -w @seed-design/css && pnpm add -Dw @seed-design/vite-plugin vite-tsconfig-paths
```

**Step 2: Seed Design CLI 초기화 (ui 패키지)**

```bash
cd jittda/frontend/packages/ui && npx @seed-design/cli@latest init -y
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
cd jittda/frontend/packages/ui && npx @seed-design/cli@latest add button text-field select-box checkbox
```

Interactive 프롬프트에서 overwrite 선택.
Expected: `src/seed-design/` 아래 컴포넌트 소스 생성

**Step 5: barrel export에 Seed 컴포넌트 추가**

```typescript
// jittda/frontend/packages/ui/src/index.ts
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
ls jittda/frontend/packages/ui/seed-design.json
ls jittda/frontend/packages/ui/src/seed-design/
```
Expected: seed-design.json + 컴포넌트 폴더들

**Step 7: 커밋**

```bash
git add jittda/frontend/packages/ui/
git commit -m "feat: Seed Design CLI 초기화 + 기본 컴포넌트 추가"
```

---

### Task 4: @jittda/public 패키지 스캐폴딩

**Files:**
- Create: `jittda/frontend/packages/public-app/package.json`
- Create: `jittda/frontend/packages/public-app/tsconfig.json`
- Create: `jittda/frontend/packages/public-app/tsconfig.app.json`
- Create: `jittda/frontend/packages/public-app/tsconfig.node.json`
- Create: `jittda/frontend/packages/public-app/vite.config.ts`
- Create: `jittda/frontend/packages/public-app/index.html`
- Create: `jittda/frontend/packages/public-app/src/main.tsx`
- Create: `jittda/frontend/packages/public-app/src/App.tsx`

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
// jittda/frontend/packages/public-app/tsconfig.json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

```json
// jittda/frontend/packages/public-app/tsconfig.app.json
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
// jittda/frontend/packages/public-app/tsconfig.node.json
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
// jittda/frontend/packages/public-app/vite.config.ts
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
// jittda/frontend/packages/public-app/src/main.tsx
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
// jittda/frontend/packages/public-app/src/App.tsx
import { Routes, Route } from 'react-router-dom'

function PlaceholderPage({ name }: { name: string }) {
  return (
    <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-8 text-center">
        <h1 className="text-2xl font-semibold text-[--color-text-primary]">{name}</h1>
        <p className="text-[--color-text-secondary] mt-2">Phase 1에서 구현됩니다.</p>
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
ls jittda/frontend/packages/public-app/package.json jittda/frontend/packages/public-app/vite.config.ts jittda/frontend/packages/public-app/src/App.tsx
```
Expected: 모든 파일 존재

**Step 7: 커밋**

```bash
git add jittda/frontend/packages/public-app/
git commit -m "feat: @jittda/public 패키지 스캐폴딩 (4 라우트 플레이스홀더)"
```

---

### Task 5: @jittda/admin 패키지 스캐폴딩 (Clean Slate)

**Files:**
- Create: `jittda/frontend/packages/admin-app/package.json`
- Create: `jittda/frontend/packages/admin-app/tsconfig.json`
- Create: `jittda/frontend/packages/admin-app/tsconfig.app.json`
- Create: `jittda/frontend/packages/admin-app/tsconfig.node.json`
- Create: `jittda/frontend/packages/admin-app/vite.config.ts`
- Create: `jittda/frontend/packages/admin-app/index.html`
- Create: `jittda/frontend/packages/admin-app/src/main.tsx`
- Create: `jittda/frontend/packages/admin-app/src/App.tsx`

> Clean Slate: 기존 `frontend/src/` 코드를 이전하지 않고, 11개 라우트 플레이스홀더로 새로 생성.

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
    "@tailwindcss/vite": "^4.1.18",
    "@playwright/test": "^1.50.0",
    "eslint": "^9.39.1"
  }
}
```

**Step 2: tsconfig 파일 3개 생성** (public-app과 동일 구조)

```json
// jittda/frontend/packages/admin-app/tsconfig.json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

```json
// jittda/frontend/packages/admin-app/tsconfig.app.json
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
// jittda/frontend/packages/admin-app/tsconfig.node.json
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
// jittda/frontend/packages/admin-app/vite.config.ts
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

**Step 4: index.html 생성**

```html
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Jittda Admin</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 5: main.tsx + App.tsx 생성 (11개 관리자 라우트 플레이스홀더)**

```tsx
// jittda/frontend/packages/admin-app/src/main.tsx
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
// jittda/frontend/packages/admin-app/src/App.tsx
import { Routes, Route } from 'react-router-dom'

function PlaceholderPage({ name }: { name: string }) {
  return (
    <div className="min-h-screen bg-[--color-bg-primary] flex items-center justify-center">
      <div className="bg-[--color-bg-surface] border border-[--color-border-default] rounded-xl shadow-card p-8 text-center">
        <h1 className="text-2xl font-semibold text-[--color-text-primary]">{name}</h1>
        <p className="text-[--color-text-secondary] mt-2">Phase 1에서 구현됩니다.</p>
      </div>
    </div>
  )
}

export function App() {
  return (
    <Routes>
      {/* Auth */}
      <Route path="/login" element={<PlaceholderPage name="로그인" />} />

      {/* Dashboard */}
      <Route path="/" element={<PlaceholderPage name="대시보드" />} />

      {/* Job Management */}
      <Route path="/jobs" element={<PlaceholderPage name="채용 공고 목록" />} />
      <Route path="/jobs/new" element={<PlaceholderPage name="공고 생성" />} />
      <Route path="/jobs/:jobId" element={<PlaceholderPage name="공고 상세" />} />

      {/* Candidate Management */}
      <Route path="/jobs/:jobId/candidates" element={<PlaceholderPage name="지원자 목록" />} />
      <Route path="/jobs/:jobId/candidates/:candidateId" element={<PlaceholderPage name="지원자 상세" />} />

      {/* Analysis Results */}
      <Route path="/jobs/:jobId/candidates/:candidateId/analysis" element={<PlaceholderPage name="분석 결과" />} />
      <Route path="/jobs/:jobId/candidates/:candidateId/interview" element={<PlaceholderPage name="면접 스크립트" />} />

      {/* Settings */}
      <Route path="/settings" element={<PlaceholderPage name="설정" />} />
      <Route path="/settings/company" element={<PlaceholderPage name="회사 설정" />} />
    </Routes>
  )
}
```

**Step 6: 검증**

```bash
ls jittda/frontend/packages/admin-app/package.json jittda/frontend/packages/admin-app/vite.config.ts jittda/frontend/packages/admin-app/src/App.tsx jittda/frontend/packages/admin-app/src/main.tsx
```
Expected: 모든 파일 존재

**Step 7: 커밋**

```bash
git add jittda/frontend/packages/admin-app/
git commit -m "feat: @jittda/admin 패키지 스캐폴딩 (11 라우트 플레이스홀더)"
```

---

### Task 6: pnpm install + 통합 빌드 검증

**Step 1: 의존성 설치**

```bash
cd jittda/frontend && pnpm install
```

Expected: node_modules 생성, workspace 링크 확인

**Step 2: workspace 링크 확인**

```bash
cd jittda/frontend && pnpm ls --depth 0 -r
```

Expected: `@jittda/ui`, `@jittda/public`, `@jittda/admin` 3개 패키지 표시

**Step 3: TypeScript 타입 체크**

```bash
cd jittda/frontend && pnpm typecheck
```

Expected: 에러 없음

**Step 4: public-app dev 서버 테스트**

```bash
cd jittda/frontend && pnpm dev:public &
sleep 3
curl -s http://localhost:3000/careers/test-company | head -20
kill %1
```

Expected: HTML 응답 반환

**Step 5: admin-app dev 서버 테스트**

```bash
cd jittda/frontend && pnpm dev:admin &
sleep 3
curl -s http://localhost:3001/ | head -20
kill %1
```

Expected: HTML 응답 반환

**Step 6: 빌드 테스트**

```bash
cd jittda/frontend && pnpm build
```

Expected: `packages/public-app/dist/`, `packages/admin-app/dist/` 생성

**Step 7: 커밋 (lockfile + 빌드 설정 조정)**

```bash
cd /Users/sabyun/goinfre/IaaS && git add jittda/frontend/pnpm-lock.yaml jittda/frontend/node_modules/.pnpm/lock.yaml 2>/dev/null; git add -u jittda/frontend/
git commit -m "chore: pnpm workspace 통합 빌드 검증 완료"
```

---

### Task 7: Dockerfile 멀티앱 빌드

**Files:**
- Create: `jittda/frontend/Dockerfile`
- Create: `jittda/frontend/nginx.conf`

> 기존 `frontend/Dockerfile`은 READ-ONLY. `jittda/frontend/`에 신규 Dockerfile 생성.

**Step 1: Dockerfile 생성 (멀티앱 빌드)**

```dockerfile
# jittda/frontend/Dockerfile
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

**Step 2: nginx.conf 생성**

```nginx
# jittda/frontend/nginx.conf
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (런타임 환경에서 설정)
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 256;
}
```

**Step 3: 커밋**

```bash
git add jittda/frontend/Dockerfile jittda/frontend/nginx.conf
git commit -m "chore: jittda/frontend Dockerfile 멀티앱 빌드 + nginx 설정"
```

---

### Task 8: 스킬 라우팅 등록 + 최종 커밋

**Files:**
- Modify: `CLAUDE.md` — Auto-Routing 테이블에 디자인 시스템 스킬 추가

**Step 1: CLAUDE.md Auto-Routing에 디자인 시스템 추가**

Auto-Routing 테이블에 추가:

```
| UI, component, color, design token | context7, magic | /jittda-design-system |
```

**Step 2: 최종 검증 — 전체 디렉토리 구조 확인**

```bash
find jittda/frontend -maxdepth 4 -type f \( -name "*.json" -o -name "*.ts" -o -name "*.tsx" -o -name "*.css" -o -name "*.html" -o -name "*.yaml" \) | sort
```

Expected 구조:
```
jittda/frontend/
├── pnpm-workspace.yaml
├── package.json (루트)
├── tsconfig.base.json
├── Dockerfile
├── nginx.conf
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
│   │   ├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
│   │   ├── vite.config.ts
│   │   ├── index.html
│   │   └── src/
│   │       ├── main.tsx
│   │       └── App.tsx
│   └── admin-app/
│       ├── package.json
│       ├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
│       ├── vite.config.ts
│       ├── index.html
│       └── src/
│           ├── main.tsx
│           └── App.tsx
```

**Step 3: 최종 커밋**

```bash
git add -A jittda/frontend/ CLAUDE.md
git commit -m "feat(phase-0): jittda/frontend 웹 프론트엔드 모노레포 스캐폴딩 완료

- pnpm workspace + 3패키지 (@jittda/ui, @jittda/public, @jittda/admin)
- Seed Design 2-tier 토큰 (Scale → Semantic) + Jittda 브랜드 오버라이드
- public-app 4라우트 + admin-app 11라우트 플레이스홀더
- Dockerfile 멀티앱 빌드 + nginx SPA 설정

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 완료 기준

- [ ] pnpm workspace에서 3패키지 인식 (`pnpm ls -r`)
- [ ] `pnpm dev:public` → localhost:3000 플레이스홀더 표시
- [ ] `pnpm dev:admin` → localhost:3001 플레이스홀더 표시
- [ ] `pnpm build` → 두 앱 dist/ 생성
- [ ] Semantic Token이 CSS에서 올바르게 적용
- [ ] TypeScript 타입 체크 통과

## 다음 단계 (Phase 1)

- Public App 4페이지 실제 구현 (CareersPage, JobDetailPage, ApplicationPage, ConfirmPage)
- Backend REST API 추가 (Company, Public, Application 엔드포인트)
- Docker Compose 2앱 분리
- Admin App에서 공유 컴포넌트를 @jittda/ui로 추출
