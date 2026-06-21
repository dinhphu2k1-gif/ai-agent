# AGENTS.md — Agentic-FE Codebase Guide

> **Last updated:** 2026-05-18
> **Source of truth:** `src/pages/user-management/` (sample page)

---

## 1. PROJECT OVERVIEW

| Item | Detail |
|---|---|
| **Name** | `agentic-fe` |
| **Purpose** | Enterprise admin dashboard for multi-agent AI data analysis (user/group management, early warning) |
| **Framework** | React 19 + Vite 8 |
| **Language** | TypeScript 6 (strict-ish, `noUnusedLocals`, `noUnusedParameters`) |
| **UI Library** | MUI v9 + Emotion |
| **State** | Redux Toolkit (RTK) with `combineSlices` |
| **Routing** | React Router DOM v7 (data router via `createBrowserRouter`) |
| **Forms** | React Hook Form v7 + Zod v4 |
| **HTTP** | Axios (class-based `ApiService`) |
| **Icons** | Material Symbols (Google Fonts) + @tabler/icons-react |
| **Fonts** | Inter (UI) + JetBrains Mono (data/labels) via `@fontsource/inter` |

### Folder Structure

```
src/
├── api/            # Axios ApiService base class + domain API singletons
├── assets/         # Static images (hero.png, svgs)
├── components/     # Shared reusable components
│   ├── cards/      #   MainCard wrapper
│   ├── hook-form/  #   RHF wrappers (RHFTextField, RHFSelect, etc.) + barrel
│   ├── loading/    #   Loader, Loading spinners
│   ├── tab/        #   TabPanel helper
│   └── tooltip/    #   HtmlTooltip styled component
├── layout/         # App shell
│   ├── Sidebar/    #   Collapsible sidebar (permanent/temporary drawer)
│   └── menu-items/ #   Navigation menu config objects
├── pages/          # Feature pages (one folder per feature)
│   ├── user-management/
│   │   ├── index.tsx        # Page component (state orchestrator)
│   │   └── components/      # Page-scoped components
│   └── group-management/
├── redux/          # Store setup
│   ├── index.ts             # configureStore, makeStore, types
│   ├── hooks.ts             # useAppDispatch, useAppSelector
│   ├── createAppSlice.ts    # buildCreateSlice with asyncThunk
│   └── reducers/            # Slice files + combineSlices barrel
├── routes/         # Router config
│   ├── index.tsx            # RouterProvider wrapper
│   └── main-router.tsx      # Route tree (lazy imports)
├── theme/          # MUI theme
│   ├── index.tsx            # ThemeProvider + ThemeSync
│   ├── palette.ts           # colorSchemes (light + dark, MD3 tokens)
│   ├── typography.ts        # Custom variants (displaySm, headlineAgent, etc.)
│   ├── breakpoints.ts       # Standard MUI breakpoints
│   ├── shadows.ts           # createShadow factory
│   └── overide/             # Component default overrides (TextField, Select, Tab, FormControl)
├── types/          # Shared types
│   ├── type.ts              # Domain interfaces (User, Pages, PageableRequest/Response, etc.)
│   ├── theme.d.ts           # MUI module augmentation (Palette, Typography variants)
│   ├── enum.ts              # Enums (MenuType, UserStatus, ApproveStatus, etc.)
│   ├── constant.ts          # App constants (drawerWidth, messages, options)
│   └── regex-template.ts    # Regex validation patterns
├── utils/          # Utility functions
│   ├── index.ts             # downloadFile, getNameFile, handleException, enumToValues
│   └── getFontValue.tsx     # pxToRem, remToPx, responsiveFontSizes
├── App.tsx         # Root: Provider → ThemeProvider → RouterProvider
└── main.tsx        # Entry: StrictMode → App
```

---

## 2. CODING CONVENTIONS

### Naming

| Element | Convention | Example |
|---|---|---|
| Components | PascalCase | `UserTable`, `AddUserDrawer` |
| Component files | PascalCase `.tsx` | `TopAppBar.tsx`, `BulkActionBar.tsx` |
| Page folders | kebab-case | `user-management/`, `group-management/` |
| Hooks | camelCase, `use` prefix | `useAppSelector`, `useAppDispatch` |
| Redux slices | camelCase file, PascalCase slice var | `sidebar.ts` → `sidebarSlice` |
| Types/Interfaces | PascalCase | `UserFormData`, `SidebarState` |
| Constants | UPPER_SNAKE_CASE for objects/strings | `MESSAGE_COMMON`, `BRCD_HEAD_OFFICE` |
| Enums | PascalCase enum + PascalCase members | `UserStatus.Active` |
| Utility files | camelCase | `getFontValue.tsx` |

### Export Patterns

- **Components**: `export default` (one component per file)
- **Barrel files** (`index.tsx`/`index.ts`): Re-export via `export { default as X } from './X'`
- **Redux slices**: Named exports for actions + selectors; named export for slice itself
- **Types**: Named exports (`export interface`, `export type`, `export enum`)
- **API service**: `export default new MainApi()` (singleton instance)

### Import Ordering (observed)

```ts
// 1. React / React DOM
import { useState } from 'react'
// 2. Third-party libraries (MUI, react-router, zod, etc.)
import { Box, Typography } from '@mui/material'
// 3. Internal absolute imports (using @/ alias)
import { FormProvider } from '@/components/hook-form'
// 4. Relative imports (same feature)
import TopAppBar from './components/TopAppBar'
// 5. Type-only imports use `import type`
import type { User } from './components/UserTable'
```

---

## 3. TYPESCRIPT CONVENTIONS

### Key `tsconfig.app.json` Settings

| Setting | Value |
|---|---|
| `baseUrl` | `./src` |
| `paths` | `@/*` → `./*` |
| `target` | `es2023` |
| `module` | `esnext` |
| `moduleResolution` | `bundler` |
| `jsx` | `react-jsx` |
| `noUnusedLocals` | `true` |
| `noUnusedParameters` | `true` |
| `noFallthroughCasesInSwitch` | `true` |
| `strict` | Not explicitly set (defaults off) |

### Type Patterns

- **`interface`** for component props, API shapes, domain models
- **`type`** for unions, mapped types, `Omit<>`, `Pick<>`, inferred types (`z.infer<>`)
- **Module augmentation** for MUI theme in `types/theme.d.ts`
- **Generic patterns**: `ApiResponse<T>`, `PageableResponse<T>`, `UseFormReturn<T>`, `PayloadAction<T>`
- **`import type`** used consistently for type-only imports

---

## 4. COMPONENT ARCHITECTURE

### Page Structure

```
src/pages/<feature-name>/
├── index.tsx           # Page component — owns ALL state, passes handlers as props
├── types.ts            # Feature-scoped types & enums
├── constants.ts        # Feature-scoped constants & mock data
├── components/         # Page-scoped child components (NOT shared)
│   ├── TopAppBar.tsx
│   ├── Toolbar.tsx
│   ├── DataTable.tsx
│   └── ...
└── <sub-feature>/      # Complex sub-features get their own folder
    ├── index.tsx        # Sub-feature orchestrator
    ├── hooks/           # Sub-feature-specific hooks
    ├── components/      # Sub-feature-level shared components
    └── <step-or-section>/  # Step-based co-location (see below)
        ├── index.tsx    # Step orchestrator
        └── ChildComponent.tsx
```

### Step-Based Co-Location (Drawer / Wizard Pattern)

For multi-step drawers or wizards, each step owns its folder with co-located sub-components:

```
src/pages/role-management/add-permission-drawer/
├── index.tsx                     # Drawer shell (orchestrator)
├── hooks/
│   └── usePermissionForm.ts      # Centralized form state + validation
├── components/                   # Drawer-level shared components
│   ├── ContextBar.tsx
│   └── PermissionStepper.tsx
├── resource-step/                # Step 0
│   ├── index.tsx                 # Step orchestrator
│   ├── ResourceTree.tsx          # Step-scoped component
│   └── SelectedResourceInfo.tsx
├── action-effect-step/           # Step 1
│   └── index.tsx
├── modifier-step/                # Step 2
│   ├── index.tsx                 # Orchestrator (delegates by resource type)
│   ├── NoModifierSection.tsx
│   ├── RowFilterSection.tsx
│   └── column-mask/              # Complex section → subfolder
│       ├── ColumnMaskSection.tsx
│       ├── MaskTypeSelector.tsx
│       ├── PatternInput.tsx
│       ├── CharacterMap.tsx
│       ├── MaskPreview.tsx
│       ├── TestInput.tsx
│       └── maskUtils.tsx         # Shared utility (non-component)
└── review-step/                  # Step 3
    └── index.tsx
```

**Key rules:**
- Each step's children live **inside its own folder** (no cross-step imports)
- Step `index.tsx` = orchestrator, children = presentational
- Complex sections (e.g. column-mask with 6+ files) get a **subfolder**
- Shared utility functions go in dedicated files (e.g. `maskUtils.tsx`), NOT mixed with component exports (Vite Fast Refresh requirement)

### Grouped Props (Option A)

For steps with many related props, group them into typed config objects instead of flat prop drilling:

```tsx
// types.ts
interface RowFilterConfig {
  enabled: boolean
  conditionExpression: string
}

// ModifierStep receives 2 objects instead of 13 flat props
interface ModifierStepProps {
  rowFilter: RowFilterConfig
  onChangeRowFilter: (patch: Partial<RowFilterConfig>) => void
  columnMask: ColumnMaskConfig
  onChangeColumnMask: (patch: Partial<ColumnMaskConfig>) => void
}
```

### Component Patterns

- **Arrow function components** (not function declarations): `const MyComponent = () => { ... }`
- **Props typed inline** via `interface` directly above the component
- **Return type** is implicit (no explicit `React.FC`)
- **State lives in the page `index.tsx`**; child components receive data + callbacks via props
- **Drawers/Modals** receive `open`, `onClose` props; page controls their visibility
- **No CSS files** — all styling via MUI `sx` prop or `styled()`
- **Component files export ONLY components** (one `export default`). Shared functions/constants must be in separate files to preserve Vite Fast Refresh (HMR)

### Shared vs Page-Scoped Components

| Location | Use When |
|---|---|
| `src/components/` | Reusable across multiple pages/features |
| `src/pages/<feature>/components/` | Used ONLY within that feature page |
| `src/pages/<feature>/<sub-feature>/components/` | Used ONLY within that sub-feature |
| `src/pages/<feature>/<sub-feature>/<step>/` | Used ONLY within that step |

---

## 5. MUI THEME & STYLING

### Color System (MD3-based)

The palette uses **Material Design 3 tonal tokens** with both light and dark color schemes.

**Key custom palette tokens** (defined in `palette.ts`, typed in `theme.d.ts`):

| Token | Usage |
|---|---|
| `surface`, `surfaceDim`, `surfaceBright` | Background layers |
| `surfaceContainer`, `surfaceContainerLow/High/Highest/Lowest` | Card/section backgrounds |
| `onSurface`, `onSurfaceVariant` | Text on surfaces |
| `outline`, `outlineVariant` | Borders |
| `primaryContainer`, `onPrimaryContainer` | Primary accent containers |
| `secondaryContainer`, `onSecondaryContainer` | Secondary accent containers |
| `tertiaryContainer` | Tertiary elements |
| `statusActiveBg/Text/Border` | Active status chip colors |
| `roleViewerBg/Text/Border` | Role chip colors |

**Primary brand color**: `#ae1c3f` (Crimson) in light mode, `#ffb2b9` in dark mode.

### Typography Variants

| Variant | Font | Size | Weight | Use |
|---|---|---|---|---|
| `displaySm` | Inter | 24px | 600 | Page titles |
| `headlineAgent` | Inter | 16px | 600 | Section headers, agent names |
| `bodyMain` | Inter | 14px | 400 | Body text (maps to `body1`) |
| `bodyData` | Inter | 13px | 400 | Table data (maps to `body2`) |
| `labelMono` | JetBrains Mono | 12px | 500 | Labels, tags, code |
| `caption` | Inter | 12px | 400 | Captions, hints |

### Styling Approach

1. **`sx` prop** — Primary method for component-level styling
2. **`styled()`** — For reusable styled variants (StatusChip, GroupChip, Sidebar Drawer)
3. **CSS Variables** — Access palette via `var(--mui-palette-<token>)` in styled components
4. **Direct palette keys** — Use shorthand in `sx`: `bgcolor: 'surfaceContainer'`, `color: 'onSurface'`
5. **NO inline CSS files** — Zero `.css` imports in components

### Color Access Patterns

```tsx
// In sx prop — use palette key shorthand
sx={{ bgcolor: 'surfaceContainerLow', color: 'onSurface', borderColor: 'outlineVariant' }}

// In sx prop — use nested palette
sx={{ color: 'primary.main', bgcolor: 'background.default' }}

// In styled() — use CSS variables
backgroundColor: 'var(--mui-palette-surfaceContainer)'

// In styled() — use theme object
color: theme.palette.onSurfaceVariant
```

### Component Overrides (`theme/overide/`)

| Component | Defaults |
|---|---|
| `MuiTextField` | `variant: 'outlined'`, `size: 'small'`, `fullWidth: true`, surfaceContainer bg |
| `MuiSelect` | `variant: 'outlined'`, `size: 'small'`, surfaceContainer bg |
| `MuiFormControl` | `variant: 'outlined'`, `size: 'small'` |
| `MuiTab` | `iconPosition: 'start'`, `minHeight: 48` |

### Dark/Light Mode

- Managed via Redux (`themeSlice`) → synced to MUI via `useColorScheme()` in `ThemeSync` component
- Uses MUI's `colorSchemes` API with `cssVariables` and `data-mui-color-scheme` selector
- Default mode: `'system'`

---

## 6. FORM PATTERNS

### React Hook Form + Zod

```tsx
// 1. Define Zod schema
const userSchema = z.object({
  fullName: z.string().min(2, 'Name is too short'),
  email: z.email('Invalid email address'),
  groups: z.array(z.string()).min(1, 'Select at least one group'),
})

// 2. Infer type from schema
export type UserFormData = z.infer<typeof userSchema>

// 3. Initialize form with zodResolver
const methods = useForm<UserFormData>({
  resolver: zodResolver(userSchema),
  defaultValues: { fullName: '', email: '', groups: [] },
})

// 4. Wrap with FormProvider
<FormProvider methods={methods} onSubmit={handleSubmit(onSubmit)} sx={{ ... }}>
  <RHFTextField name="fullName" placeholder="e.g., Jane Doe" />
  <RHFSelect name="groups" multiple ...>
    {options.map(o => <MenuItem key={o} value={o}>{o}</MenuItem>)}
  </RHFSelect>
</FormProvider>
```

### Form Field Labels

Use `labelMono` variant for field labels, placed ABOVE the input:

```tsx
<Box>
  <Typography variant="labelMono" sx={{ color: 'var(--mui-palette-onSurfaceVariant)', mb: 0.5, display: 'block' }}>
    Field Label
  </Typography>
  <RHFTextField name="fieldName" placeholder="..." />
</Box>
```

### Available RHF Components

All in `src/components/hook-form/`:
- `FormProvider` — wraps `react-hook-form`'s FormProvider + form element
- `RHFTextField` — controlled TextField
- `RHFSelect` — controlled Select with FormControl
- `RHFAutocomplete` — controlled Autocomplete
- `RHFCheckBox` — controlled Checkbox
- `RHFRadioGroup` — controlled RadioGroup
- `RHFSwitch` — controlled Switch

---

## 7. STATE MANAGEMENT

### Redux Toolkit Setup

- **Store**: `configureStore` with `combineSlices` (auto-combines by `reducerPath`)
- **Typed hooks**: `useAppDispatch`, `useAppSelector` in `redux/hooks.ts`
- **Slice pattern**: Uses RTK's `createSlice` with callback syntax for reducers + built-in `selectors`

### Current Slices

| Slice | State | Purpose |
|---|---|---|
| `sidebar` | `{ isOpen: boolean }` | Sidebar open/close state |
| `theme` | `{ mode: 'light' \| 'dark' \| 'system' }` | Theme mode |
| `messageToast` | `{ snackbar: { children, severity } \| null }` | Global alert/toast |

### Slice Pattern Template

```ts
import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export interface MyState { /* ... */ }

const initialState: MyState = { /* ... */ }

export const mySlice = createSlice({
  name: 'mySlice',
  initialState,
  reducers: (create) => ({
    setFoo: create.reducer((state, action: PayloadAction<string>) => {
      state.foo = action.payload
    }),
  }),
  selectors: {
    selectFoo: (state) => state.foo,
  },
})

export const { setFoo } = mySlice.actions
export const { selectFoo } = mySlice.selectors
```

---

## 8. API & DATA FETCHING

### ApiService Class (`api/index.ts`)

- Base class with Axios interceptors (auth token, error handling)
- Generic methods: `get<T>()`, `post<T, D>()`, `put<T, D>()`, `delete<T>()`
- Auto-handles 403 → redirect to login
- `x-exception` header flag for centralized error dispatch to Redux alert

### Domain API Pattern (`api/MainApi.ts`)

```ts
import { ApiService } from '.'

class MainApi extends ApiService {
  constructor() {
    super(import.meta.env.VITE_APP_API_URL)
  }
  // Add domain-specific methods here
}

export default new MainApi()
```

### Response Type

```ts
export type ApiResponse<T> = {
  message: string
  success: boolean
  data: T
}
```

### Pagination Types (in `types/type.ts`)

```ts
export interface PageableRequest {
  page: number; pageSize: number; sort?: string; orderBy?: string
}
export interface PageableResponse<T> {
  data: T[]; currentPage: number; totalItems: number; totalPages: number
}
```

### Environment Variables

- `VITE_APP_API_URL` — API base URL
- `VITE_LOGIN_URL` — Login redirect URL

---

## 9. ROUTING

### Structure

```ts
// routes/index.tsx — creates browser router
export default function RouterProvider() {
  const router = createBrowserRouter([MainRouter])
  return <RRDRouterProvider router={router} />
}

// routes/main-router.tsx — route tree
const MainRouter: RouteObject = {
  path: '/',
  element: <MainLayout />,     // Sidebar + <Outlet />
  children: [
    { path: 'admin', children: [
      { path: 'users', element: <UserManagementPage /> },  // lazy loaded
      { path: 'group-user', children: [...] },
    ]},
    { path: 'early-warning', children: [...] },
    { path: '*', element: <div>404</div> },
  ],
}
```

### Key Patterns

- **Lazy loading**: `const Page = lazy(() => import('@/pages/feature-name'))`
- **Layout**: `MainLayout` provides Sidebar + `<Outlet />`
- **Error**: `errorElement` on root route
- **No route guards yet** (auth redirect is handled at API interceptor level)

---

## 10. ESLINT & PRETTIER CONFIG

### ESLint (`eslint.config.js`)

- Flat config with `defineConfig`
- Extends: `js.configs.recommended`, `tseslint.configs.recommended`, `reactHooks`, `reactRefresh`, `eslintConfigPrettier`
- Ignores: `dist`, `node_modules`, `agents`
- Applies to: `**/*.{ts,tsx}`

### Prettier (`.prettierrc`)

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### Critical Rules for Agents

- **NO semicolons** (`semi: false`)
- **Single quotes** for strings
- **Trailing commas** in ES5 positions (objects, arrays, function params)
- **100 char line width** max
- **2-space indentation**, no tabs
- **Always parentheses** around arrow function params: `(x) => x`
- **LF line endings** (not CRLF)
- **No unused variables or parameters** (TS compiler enforced)
- **No fallthrough in switch** statements

---

## 11. SAMPLE PAGE ANALYSIS — User Management

The `src/pages/user-management/` page is the **source of truth** for all patterns.

### Architecture

```
index.tsx (Page)
├── State: selectedIds, drawerOpen, addUserOpen, isBulkGroupOpen, etc.
├── Handlers: handleSelectAll, handleRowClick, handleAddUser, etc.
└── Renders:
    ├── TopAppBar          — sticky header with breadcrumb
    ├── Toolbar            — search + filter + "Add User" CTA
    ├── UserTable          — data table with checkboxes, chips
    ├── BulkActionBar      — floating pill bar (Fade transition)
    ├── UserDetailDrawer   — right drawer (view/edit user)
    ├── AddUserDrawer      — right drawer (form with RHF+Zod)
    ├── AddGroupDrawer     — right drawer (bulk assign groups)
    ├── AddRoleDrawer      — right drawer (bulk assign roles)
    └── ConfirmDeactivateModal — Dialog confirmation
```

### DO's ✅

1. **Keep all page state in `index.tsx`** — child components are presentational
2. **Use `interface` for props** directly above the component
3. **Use `export default` for components**, one per file
4. **Use MUI `sx` prop** for styling — leverage palette tokens directly
5. **Use custom typography variants** (`headlineAgent`, `bodyData`, `labelMono`, etc.)
6. **Use MD3 surface tokens** for backgrounds (`surfaceContainer`, `surfaceContainerLow`, etc.)
7. **Use `outlineVariant`** for borders, `divider` for separators
8. **Use `styled()` for reusable chip/styled variants** with theme access
9. **Drawer pattern**: `anchor="right"`, `slotProps.paper.sx` for paper styling, `backgroundImage: 'none'`
10. **Dialog pattern**: `slotProps.paper.sx` for paper styling, separate Header/Content/Footer sections
11. **Form pattern**: Zod schema → `z.infer<>` → `useForm` with `zodResolver` → `FormProvider` wrapper
12. **Icons**: Use `<span className="material-symbols-outlined">icon_name</span>` (Google Material Symbols)
13. **Use `import type`** for type-only imports
14. **Use `@/` path alias** for absolute imports

### DON'Ts ❌

1. **DON'T use CSS files** — no `.css` imports in components
2. **DON'T use `React.FC`** — use arrow functions with implicit return type
3. **DON'T hardcode colors** — always use palette tokens or CSS variables
4. **DON'T put shared state in child components** — lift state up to page
5. **DON'T use semicolons** — Prettier enforces `semi: false`
6. **DON'T use double quotes** — use single quotes
7. **DON'T use `className` for styling** (except for Material Symbols icons)
8. **DON'T create global CSS** — use MUI theme overrides instead
9. **DON'T use `React.FC<Props>`** — type props via destructuring
10. **DON'T mix `var(--mui-palette-*)` and palette shorthand** inconsistently — prefer shorthand in `sx`, CSS vars in `styled()`

---

## 12. AGENT INSTRUCTIONS

### Pre-Flight Checklist (Before Creating Any File)

- [ ] Read this AGENTS.md fully
- [ ] Check if a similar component/pattern already exists in `src/components/` or other pages
- [ ] Confirm the file location: shared → `src/components/`, page-specific → `src/pages/<feature>/components/`
- [ ] Identify which MUI theme tokens to use (check `palette.ts` and `theme.d.ts`)
- [ ] Identify which typography variants to use (check `typography.ts`)
- [ ] Plan the component interface (props) before writing JSX
- [ ] Ensure Prettier rules are followed (no semicolons, single quotes, trailing commas)

### New Page Template

```tsx
import { useState } from 'react'
import { Box } from '@mui/material'

// components
import TopAppBar from './components/TopAppBar'

const MyFeaturePage = () => {
  const [someState, setSomeState] = useState<string[]>([])

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        bgcolor: 'background.default',
        position: 'relative',
      }}
    >
      <TopAppBar />
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 2, gap: 2, overflow: 'hidden' }}>
        {/* Page content */}
      </Box>
    </Box>
  )
}

export default MyFeaturePage
```

### New Component Template

```tsx
import { Box, Typography } from '@mui/material'

interface MyComponentProps {
  title: string
  onAction: () => void
}

const MyComponent = ({ title, onAction }: MyComponentProps) => {
  return (
    <Box sx={{ p: 2, bgcolor: 'surfaceContainer', borderRadius: 2, border: 1, borderColor: 'outlineVariant' }}>
      <Typography variant="headlineAgent" sx={{ color: 'onSurface' }}>
        {title}
      </Typography>
    </Box>
  )
}

export default MyComponent
```

### New Redux Slice Template

```tsx
import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

export interface MyFeatureState {
  items: string[]
}

const initialState: MyFeatureState = {
  items: [],
}

export const myFeatureSlice = createSlice({
  name: 'myFeature',
  initialState,
  reducers: (create) => ({
    setItems: create.reducer((state, action: PayloadAction<string[]>) => {
      state.items = action.payload
    }),
  }),
  selectors: {
    selectItems: (state) => state.items,
  },
})

export const { setItems } = myFeatureSlice.actions
export const { selectItems } = myFeatureSlice.selectors
```

### New Drawer Template

```tsx
import { Drawer, Box, Typography, IconButton, Button } from '@mui/material'

interface MyDrawerProps {
  open: boolean
  onClose: () => void
}

const MyDrawer = ({ open, onClose }: MyDrawerProps) => {
  return (
    <Drawer
      anchor="right"
      open={open}
      slotProps={{
        paper: {
          sx: {
            width: 440,
            bgcolor: 'var(--mui-palette-surface)',
            display: 'flex',
            flexDirection: 'column',
            backgroundImage: 'none',
          },
        },
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerLow)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography variant="headlineAgent" sx={{ color: 'var(--mui-palette-onSurface)' }}>
          Title
        </Typography>
        <IconButton onClick={onClose} size="small">
          <span className="material-symbols-outlined">close</span>
        </IconButton>
      </Box>

      {/* Body */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
        {/* Content */}
      </Box>

      {/* Footer */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'var(--mui-palette-outlineVariant)',
          bgcolor: 'var(--mui-palette-surfaceContainerLow)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: 2,
        }}
      >
        <Button onClick={onClose} sx={{ color: 'var(--mui-palette-onSurfaceVariant)', textTransform: 'none' }}>
          Cancel
        </Button>
        <Button variant="contained">Submit</Button>
      </Box>
    </Drawer>
  )
}

export default MyDrawer
```

### New Route Registration

```tsx
// In routes/main-router.tsx
const MyPage = lazy(() => import('@/pages/my-feature'))

// Add to children array:
{ path: 'my-feature', element: <MyPage /> }
```

### Common Mistakes to Avoid

| Mistake | Fix |
|---|---|
| Using semicolons | Remove all semicolons |
| Using double quotes | Use single quotes |
| Using `React.FC` | Use plain arrow function with typed props |
| Hardcoding colors like `#333` | Use palette tokens: `'onSurface'`, `'surfaceContainer'` |
| Using `className` for layout | Use MUI `sx` prop |
| Importing from `@mui/material/styles` without type | Use `import type` for type-only |
| Creating `.css` files | Use `sx` or `styled()` |
| Managing state in child components | Lift state to page `index.tsx` |
| Not adding new slices to `reducers/index.ts` | Add to `combineSlices()` call |
| Using `useSelector`/`useDispatch` directly | Use `useAppSelector`/`useAppDispatch` |
| Forgetting `backgroundImage: 'none'` on Drawer paper | MUI adds a gradient by default in dark mode |
