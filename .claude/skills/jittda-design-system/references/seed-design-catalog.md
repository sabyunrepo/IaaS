# Seed Design Component Catalog & Reference

> Seed Design (당근마켓) React 컴포넌트 라이브러리 참조.
> 공식 문서: https://seed-design.io

## MCP 도구 (seed-docs)

| 도구 | 용도 |
|------|------|
| `list_react_components` | React 컴포넌트 전체 목록 |
| `get_react_component` | 특정 컴포넌트 API/사용법 |
| `get_react_changelog` | React 변경 이력 |
| `list_docs_components` | 디자인 가이드 컴포넌트 목록 |
| `get_docs_component` | 디자인 가이드 상세 |
| `list_foundation` | Foundation 토큰 목록 |
| `get_foundation` | Foundation 상세 (색상, 타이포 등) |
| `list_icons` | 아이콘 전체 목록 |
| `search_icons` | 아이콘 검색 |
| `get_icon_details` | 아이콘 상세 |
| `get_rootage` | 원본 JSON 데이터 |

## llms.txt URL 패턴

| 대상 | URL |
|------|-----|
| React 전체 | `https://seed-design.io/react/llms-full.txt` |
| React 목록 | `https://seed-design.io/react/llms.txt` |
| Design 전체 | `https://seed-design.io/docs/llms-full.txt` |
| Design 목록 | `https://seed-design.io/docs/llms.txt` |
| 개별 React 컴포넌트 | `https://seed-design.io/llms/react/components/{name}.txt` |
| 개별 Foundation | `https://seed-design.io/llms/docs/foundation/{name}.txt` |

## CLI 명령어

```bash
# 초기화 (seed-design.json 생성)
npx @seed-design/cli@latest init

# 컴포넌트 추가
npx @seed-design/cli@latest add ui:{component-name}

# 예시
npx @seed-design/cli@latest add ui:action-button
npx @seed-design/cli@latest add ui:alert-dialog
npx @seed-design/cli@latest add ui:tabs
```

## React 컴포넌트 카탈로그 (71개)

### Action / Button
| 컴포넌트 | 설명 |
|---------|------|
| `ActionButton` | 기본 액션 버튼 (Primary/Secondary/Danger) |
| `ToggleButton` | 토글 버튼 |
| `FAB` | 플로팅 액션 버튼 |
| `ExtendedFab` | 확장 플로팅 액션 버튼 |
| `FloatingActionButton` | 플로팅 액션 버튼 (신규) |
| `ContextualFloatingButton` | 컨텍스트 플로팅 버튼 |
| `ReactionButton` | 리액션 버튼 |
| `FieldButton` | 필드 버튼 |

### Chip / Tag
| 컴포넌트 | 설명 |
|---------|------|
| `Chip` | 칩 |
| `ActionChip` | 액션 칩 |
| `ControlChip` | 컨트롤 칩 (Button/Toggle/Radio) |
| `ChipTabs` | 칩 탭 |
| `TagGroup` | 태그 그룹 |

### Form / Input
| 컴포넌트 | 설명 |
|---------|------|
| `TextFieldInput` | 텍스트 입력 필드 |
| `TextFieldTextarea` | 텍스트 영역 |
| `Checkbox` | 체크박스 |
| `RadioGroup` | 라디오 그룹 |
| `SelectBox` | 셀렉트 박스 |
| `Switch` | 스위치 |
| `Slider` | 슬라이더 |

### Layout
| 컴포넌트 | 설명 |
|---------|------|
| `Box` | 기본 박스 |
| `Flex` | 플렉스 컨테이너 |
| `Grid` | 그리드 레이아웃 |
| `HStack` | 가로 스택 |
| `VStack` | 세로 스택 |
| `Stack` | 스택 (deprecated → VStack) |
| `Columns` | 컬럼 레이아웃 |
| `Float` | 플로팅 레이아웃 |
| `Inline` | 인라인 레이아웃 (deprecated → HStack) |

### Overlay / Modal
| 컴포넌트 | 설명 |
|---------|------|
| `AlertDialog` | 알림 다이얼로그 |
| `BottomSheet` | 바텀 시트 |
| `ActionSheet` | 액션 시트 |
| `ExtendedActionSheet` | 확장 액션 시트 |
| `MenuSheet` | 메뉴 시트 |
| `HelpBubble` | 도움말 버블 |

### Feedback / Status
| 컴포넌트 | 설명 |
|---------|------|
| `Snackbar` | 스낵바 |
| `InlineBanner` | 인라인 배너 |
| `PageBanner` | 페이지 배너 |
| `Callout` | 콜아웃 |
| `ErrorState` | 에러 상태 |
| `ProgressCircle` | 진행 원형 |
| `Skeleton` | 스켈레톤 |
| `LoadingIndicator` | 로딩 인디케이터 |

### Navigation / Tab
| 컴포넌트 | 설명 |
|---------|------|
| `Tabs` | 탭 |
| `SegmentedControl` | 세그먼트 컨트롤 |

### Display / Content
| 컴포넌트 | 설명 |
|---------|------|
| `Avatar` | 아바타 |
| `Badge` | 뱃지 |
| `Divider` | 구분선 |
| `List` | 리스트 |
| `Article` | 아티클 |
| `ImageFrame` | 이미지 프레임 |
| `AspectRatio` | 종횡비 |
| `LinkContent` | 링크 콘텐츠 |
| `ResultSection` | 결과 섹션 |
| `IdentityPlaceholder` | 아이덴티티 플레이스홀더 |
| `MannerTemp` | 매너 온도 |
| `MannerTempBadge` | 매너 온도 뱃지 |

### Typography
| 컴포넌트 | 설명 |
|---------|------|
| `Text` | 텍스트 컴포넌트 |

### Utility
| 컴포넌트 | 설명 |
|---------|------|
| `ScrollFog` | 스크롤 안개 효과 |
| `PullToRefresh` | 당겨서 새로고침 |

## Foundation 문서

| 항목 | URL |
|------|-----|
| Color Palette | `/llms/docs/foundation/color/palette.txt` |
| Color Role | `/llms/docs/foundation/color/color-role.txt` |
| Color System | `/llms/docs/foundation/color/color-system.txt` |
| Typography | `/llms/docs/foundation/typography/overview.txt` |
| Design Token | `/llms/docs/foundation/design-token.txt` |
| Token Reference | `/llms/docs/foundation/design-token-reference.txt` |
| Spacing | `/llms/docs/foundation/spacing.txt` |
| Radius | `/llms/docs/foundation/radius.txt` |
| Elevation | `/llms/docs/foundation/elevation.txt` |
| Motion | `/llms/docs/foundation/motion.txt` |
| Gradient | `/llms/docs/foundation/gradient.txt` |
| State | `/llms/docs/foundation/state.txt` |
| Icon Overview | `/llms/docs/foundation/iconography/overview.txt` |
| Icon Library | `/llms/docs/foundation/iconography/library.txt` |
| Icon Usage | `/llms/docs/foundation/iconography/usage.txt` |

## 프로젝트 설정

### 설치 패키지
```json
{
  "dependencies": {
    "@seed-design/react": "^1.2.4",
    "@seed-design/css": "^1.2.2",
    "@karrotmarket/react-monochrome-icon": "^1.11.0"
  },
  "devDependencies": {
    "@seed-design/vite-plugin": "^1.1.0"
  }
}
```

### seed-design.json
```json
{
  "rsc": false,
  "tsx": true,
  "path": "./src/seed-design",
  "telemetry": false
}
```

### Vite 설정
```typescript
import { seedDesignPlugin } from "@seed-design/vite-plugin"
// plugins: [..., seedDesignPlugin(), ...]
```

### CSS 진입점
```css
@import "@seed-design/css/base.css";
```
