# Sana Frontend Rules (React + TypeScript + Vite)

## Stack
- React 18+, TypeScript 5+, Vite.
- State management: Zustand stores in `frontend/src/store/`.
- HTTP client: Axios (configured in `frontend/src/api/client.ts`).
- UI: Ant Design 5+ with Tailwind CSS utility classes.
- Routing: React Router v6 (createBrowserRouter).
- Charts: ECharts via `echarts-for-react`.

## Project Structure
- `frontend/src/api/` — one file per domain (alerts.ts, charts.ts, etc.), exports domain functions only.
- `frontend/src/store/` — one Zustand store per domain, uses `create<State>()` pattern.
- `frontend/src/pages/` — page components that compose UI from `components/`.
- `frontend/src/components/` — reusable UI components, grouped by domain.
- `frontend/src/hooks/` — custom React hooks.
- `frontend/src/utils/` — utility functions.
- `frontend/src/types.ts` — ALL TypeScript interfaces/types in one file.

## API Layer
- ALWAYS use the `client` instance from `api/client.ts` (Axios pre-configured with auth and error handling).
- Each `api/{domain}.ts` file imports `client` and exports async functions.
- Endpoint paths are relative (e.g. `/alerts/`, `/alerts/{id}/`).
- The response interceptor auto-unwraps `{success: true, data: ...}` envelope — domain functions receive raw data.
- NEVER create custom Axios instances; NEVER bypass `client.ts`.

## Stores (Zustand)
- Store interface declared at top of file, exported as `{Domain}State`.
- Store export: `export const use{Domain}Store = create<{Domain}State>()((set) => ({...}))`.
- Actions call API functions, call `set()` for loading/error/data state.
- Error type: always `(error as Error).message`.

## Types
- ALL interfaces/types in `frontend/src/types.ts` — never split across files.
- Export domain-specific sub-types (e.g. `AlertCondition`, `ChartType`).
- Match backend serializer field types exactly (snake_case).

## Routing
- Defined in `App.tsx` using `createBrowserRouter`.
- Protected routes wrapped in `ProtectedLayout` (checks auth cookie, redirects to `/login`).
- All routes under `/*` protected; only `/login` is public.

## Auth
- JWT access/refresh tokens stored in cookies (prefix `bi_`).
- Token handling via `utils/cookies.ts` (getCookie, setCookie, removeCookie).
- Auth check: `isAuthenticated()` from `api/client.ts`.

## UI Components
- Use Ant Design components as primitives (Layout, Table, Form, Button, etc.).
- Tailwind CSS for spacing/layout utilities (p-4, h-screen, flex, etc.).
- Keep component files under 200 lines; extract sub-components when exceeding.

## Naming
- Files: PascalCase for components (`ChartPreview.tsx`), camelCase for utils/hooks (`chartOptions.ts`, `useChartData.ts`).
- Functions: camelCase.
- Types/interfaces: PascalCase.

## Error Handling in Components
- Show errors via Ant Design `notification.error()` — already handled globally by `client.ts` interceptor.
- Local loading state: use `loading` from store with Ant Design `Spin` component.