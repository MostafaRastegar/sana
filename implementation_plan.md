# Implementation Plan

## Overview
Build a lightweight, modern business intelligence (BI) dashboard application inspired by Apache Superset, using React + Ant Design + Tailwind CSS (frontend), Django + Django REST Framework (backend via djankit), and Apache ECharts (visualization), delivered in incremental phases with visible output at each stage.

This project creates a data exploration and visualization platform where users can build charts using a no-code interface, organize charts into dashboards, execute SQL queries, and share insights. The backend leverages the existing **djankit** Django project (renamed to `backend/`) with its pre-configured DRF, JWT auth, Celery, PostgreSQL support, and drf-spectacular API docs. The frontend is built fresh with React + Vite + Ant Design + Tailwind CSS + Zustand.

**Key reuse from djankit:**
- `config/` — Django settings, URLs, WSGI/ASGI
- `core/` — Base exception handler, middleware, permissions, pagination, serializers
- `example/` — Existing Category, Product, Order, OrderItem models (used as seed data)
- JWT auth, CORS, drf-spectacular, Celery, Redis — all pre-configured
- Project structure (manage.py, pyproject.toml, Dockerfile, docker-compose)

**New Django apps to create:** `datasets/`, `charts/`, `dashboards/`, `query/`

---

## Implementation Status

| Phase | Status | Notes |
|-------|--------|-------|
| **1. Backend Foundation** | ✅ **Done** | 4 apps with ModelViewSet + Serializer + Router + Tests + seed_data |
| **2. Frontend Shell** | ✅ **Done** | Vite + React + Ant Design + Tailwind + Zustand + Router |
| **3. Chart Builder** | ✅ **Done** | ECharts + ChartTypeSelector + ColumnMapper + FilterBuilder + save/load |
| **4. Dashboard Builder** | ✅ **Done** | react-grid-layout + chart add/remove + layout save + CRUD |
| **5. SQL Editor** | ✅ **Done** | Monaco Editor + execute + save/load + CSV export |
| **6. Polish** | ⚠️ **Partial** | ✅ theme, loading states; ❌ CSV upload, PNG export; ⚠️ responsive |
| **Auth & Security** | ✅ **Done** | Login page + cookie-based JWT + auth guard + logout (not in original plan) |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────┐  │
│  │Dashboard │  │ Chart     │  │ SQL Editor           │  │
│  │View      │  │ Builder   │  │ (Monaco)             │  │
│  └──────────┘  └───────────┘  └──────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Zustand Store (datasets, charts, dashboards,    │  │
│  │  UI state, theme)                                │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  API Client (axios) → REST calls                 │  │
│  │  Tokens stored in **cookies** (not localStorage) │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP REST (JSON)
┌──────────────────────▼──────────────────────────────────┐
│                  Backend (Django + DRF)                  │
│  ┌────────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ ViewSets   │  │ Services  │  │ Models           │  │
│  │ (API Layer)│  │ (Business)│  │ (Data Access)    │  │
│  └────────────┘  └───────────┘  └──────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Djankit Core (auth, permissions, pagination,     │  │
│  │ exception handling, Swagger/Redoc)               │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  PostgreSQL / SQLite Database                    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Features (Phase-by-Phase)

### Phase 1: Backend Foundation (Django Apps) ✅ COMPLETE
- Rename `djankit/` → `backend/`
- Create new Django apps: `datasets`, `charts`, `dashboards`
- Define models: Dataset, Chart, Dashboard (following djankit patterns)
- Create ModelViewSets + Serializers + Routers for each
- Register URLs in `config/urls.py`
- Seed data using existing `example` app (Category, Product, Order)
- **Output**: REST API available at `/api/datasets/`, `/api/charts/`, `/api/dashboards/` with Swagger docs

### Phase 2: Frontend Shell (Ant Design + Tailwind) ✅ COMPLETE
- Create `frontend/` with Vite + React + TypeScript
- **Ant Design 5** component library (Layout, Menu, Table, Form, Button, etc.)
- **Tailwind CSS** for custom styling and responsive design
- **Zustand** for state management
- React Router v6 + Ant Design Layout shell (Sider + Header + Content)
- API client (axios) connecting to Django backend
- **Output**: Navigable UI shell with sidebar navigation

### Phase 3: Chart Builder (Core Feature) ✅ COMPLETE
- **ECharts integration** via `echarts-for-react`
- Chart type selection: Bar, Line, Pie, Scatter, Area, Heatmap
- Column mapping UI (Ant Design Select dropdowns)
- Real-time chart preview
- Save/load charts via Django API
- **Output**: Fully functional chart creation page

### Phase 4: Dashboard Builder ✅ COMPLETE
- Dashboard grid layout (react-grid-layout) — drag & resize charts
- Add/remove charts from dashboard
- Auto-save layout positions
- Dashboard CRUD via Django API
- **Output**: Interactive dashboard with resizable charts

### Phase 5: SQL Editor ✅ COMPLETE
- Monaco Editor for SQL writing
- Execute queries against Django database
- Results table with Ant Design Table (pagination)
- Save queries as SavedQuery model
- CSV export
- Load/delete saved queries
- **Output**: SQL querying interface

### Phase 6: Polish & Advanced Features ⚠️ IN PROGRESS
- ✅ Dark/Light theme toggle (TopBar Switch + ConfigProvider)
- ✅ Loading/error states (all pages: Spin + Alert)
- ⚠️ Responsive design with Tailwind CSS (DashboardList uses responsive grid, others basic)
- ❌ CSV/Excel data upload → new dataset
- ❌ Dashboard export as PNG

### Authentication & Security ✅ COMPLETE (added beyond original plan)
- ✅ Login page at `/login` (username/password → `/api/token/`)
- ✅ JWT tokens stored in **cookies** (bi_access_token, bi_refresh_token) with SameSite=Strict
- ✅ Cookie-based token refresh in axios interceptor
- ✅ Auth guard (`ProtectedRoute`) — redirects to `/login` if no cookie
- ✅ Logout button (user icon in TopBar, clears cookies → `/login`)
- ✅ `CORS_ALLOW_CREDENTIALS = True` in backend settings
- ✅ Frontend axios client uses `withCredentials: true`

---

## [Types]

### Django Models (New apps)

```python
# datasets/models.py
class Dataset(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    table_name = models.CharField(max_length=100)  # actual DB table
    columns = models.JSONField(default=list)  # [{name, type, label}]
    row_count = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# charts/models.py
class Chart(models.Model):
    CHART_TYPES = [
        ('bar', 'Bar'), ('line', 'Line'), ('pie', 'Pie'),
        ('scatter', 'Scatter'), ('area', 'Area'), ('heatmap', 'Heatmap'),
    ]
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='charts')
    chart_type = models.CharField(max_length=50, choices=CHART_TYPES)
    config = models.JSONField(default=dict)  # {x_axis, y_axis, group_by, ...}
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# dashboards/models.py
class Dashboard(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layout = models.JSONField(null=True, blank=True)  # {charts: [{chart_id, x, y, w, h}]}
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

# Add to charts/models.py
class SavedQuery(models.Model):
    name = models.CharField(max_length=100)
    sql = models.TextField()
    dataset = models.ForeignKey(Dataset, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Chart Config TypeScript

```typescript
interface ChartConfig {
  xAxis: string;
  yAxis: string;
  groupBy?: string;
  filters?: Filter[];
  sort?: { column: string; direction: 'asc' | 'desc' };
  limit?: number;
  aggregate?: 'sum' | 'avg' | 'count' | 'min' | 'max' | 'none';
}

interface Filter {
  column: string;
  operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'contains';
  value: string | number | (string | number)[];
}

interface DashboardLayout {
  charts: { chartId: number; x: number; y: number; w: number; h: number }[];
}
```

---

## [Files]

### Backend — New/Modified Files (within `backend/`)

| File | Status | Purpose |
|------|--------|---------|
| `backend/datasets/models.py` | **New** | Dataset model |
| `backend/datasets/serializers.py` | **New** | Dataset serializer |
| `backend/datasets/views.py` | **New** | Dataset ModelViewSet + data action |
| `backend/datasets/urls.py` | **New** | Dataset router |
| `backend/datasets/admin.py` | **New** | Django admin registration |
| `backend/datasets/apps.py` | **New** | App config |
| `backend/charts/models.py` | **New** | Chart + SavedQuery models |
| `backend/charts/serializers.py` | **New** | Chart serializer + chart data serializer |
| `backend/charts/views.py` | **New** | Chart ModelViewSet + data computation action |
| `backend/charts/urls.py` | **New** | Chart router |
| `backend/charts/admin.py` | **New** | Django admin registration |
| `backend/charts/apps.py` | **New** | App config |
| `backend/dashboards/models.py` | **New** | Dashboard model |
| `backend/dashboards/serializers.py` | **New** | Dashboard serializer |
| `backend/dashboards/views.py` | **New** | Dashboard ModelViewSet + layout actions |
| `backend/dashboards/urls.py` | **New** | Dashboard router |
| `backend/dashboards/admin.py` | **New** | Django admin registration |
| `backend/dashboards/apps.py` | **New** | App config |
| `backend/query/views.py` | **New** | SQL execution + saved queries endpoints |
| `backend/query/urls.py` | **New** | Query router |
| `backend/query/apps.py` | **New** | App config |
| `backend/config/urls.py` | **Modified** | Register new app routers |
| `backend/config/settings/base.py` | **Modified** | Add new apps to INSTALLED_APPS, CORS_ALLOW_CREDENTIALS=True |
| `backend/seed_data.py` | **New** | Management command to seed demo data |

### Frontend — All New Files

| File | Purpose |
|------|---------|
| `frontend/package.json` | NPM dependencies |
| `frontend/vite.config.ts` | Vite config + proxy to Django |
| `frontend/tsconfig.json` | TypeScript config |
| `frontend/tsconfig.node.json` | Node TypeScript config |
| `frontend/index.html` | HTML entry |
| `frontend/postcss.config.js` | PostCSS config for Tailwind |
| `frontend/tailwind.config.js` | Tailwind CSS config |
| `frontend/src/main.tsx` | React entry |
| `frontend/src/App.tsx` | Root with Ant Design ConfigProvider + Router + ProtectedRoute |
| `frontend/src/index.css` | Tailwind directives |
| `frontend/src/vite-env.d.ts` | Vite type declarations |
| `frontend/src/types.ts` | Shared TypeScript types |
| `frontend/src/utils/constants.ts` | Chart types, colors, etc. |
| `frontend/src/utils/chartOptions.ts` | Build ECharts option objects |
| `frontend/src/utils/cookies.ts` | Cookie get/set/remove utilities (JWT storage) |
| `frontend/src/api/client.ts` | Axios HTTP client (cookie-based token, withCredentials) |
| `frontend/src/api/datasets.ts` | Dataset API calls |
| `frontend/src/api/charts.ts` | Chart API calls |
| `frontend/src/api/dashboards.ts` | Dashboard API calls |
| `frontend/src/store/datasetStore.ts` | Zustand store for datasets |
| `frontend/src/store/chartStore.ts` | Zustand store for charts |
| `frontend/src/store/dashboardStore.ts` | Zustand store for dashboards |
| `frontend/src/store/uiStore.ts` | Zustand store for UI (theme, sidebar) |
| `frontend/src/components/Layout.tsx` | Ant Design Layout shell |
| `frontend/src/components/Sidebar.tsx` | Ant Design Menu sidebar |
| `frontend/src/components/TopBar.tsx` | Header with theme toggle + logout user icon |
| `frontend/src/pages/LoginPage.tsx` | Login form (username/password → cookie-based JWT) |
| `frontend/src/pages/DashboardList.tsx` | Dashboard list page |
| `frontend/src/pages/DashboardView.tsx` | Dashboard with grid layout |
| `frontend/src/pages/ChartBuilder.tsx` | Chart creation/editing page |
| `frontend/src/pages/ChartList.tsx` | Saved charts gallery |
| `frontend/src/pages/DatasetList.tsx` | Dataset manager |
| `frontend/src/pages/SQLEditor.tsx` | SQL query editor |
| `frontend/src/components/charts/EChartRenderer.tsx` | Generic ECharts renderer |
| `frontend/src/components/charts/ChartTypeSelector.tsx` | Chart type picker |
| `frontend/src/components/charts/ColumnMapper.tsx` | Axis column mapping |
| `frontend/src/components/charts/ChartPreview.tsx` | Live preview wrapper |
| `frontend/src/components/charts/FilterBuilder.tsx` | Filter condition UI |
| `frontend/src/hooks/useChartData.ts` | Fetch + transform chart data |

---

## [Functions]

### Backend — ViewSets (following djankit patterns)

#### `datasets/views.py` — `DatasetViewSet(viewsets.ModelViewSet)`
- Standard CRUD via ModelViewSet (list, create, retrieve, update, delete)
- `@action(detail=True, methods=['get'])` `data` — return paginated data rows from the dataset's backing table
- Uses `ModelActionPermission` from djankit core
- Uses `CustomPagination` from djankit core

#### `charts/views.py` — `ChartViewSet(viewsets.ModelViewSet)`
- Standard CRUD
- `@action(detail=True, methods=['get'])` `data` — fetch dataset rows, apply config (aggregation, filtering, grouping, sorting), return columns + rows
- Chart data computation logic (separate service function for testability)

#### `dashboards/views.py` — `DashboardViewSet(viewsets.ModelViewSet)`
- Standard CRUD
- `@action(detail=True, methods=['put'])` `layout` — update layout JSON
- `@action(detail=True, methods=['get'])` `render` — return dashboard with resolved chart data

#### `query/views.py`
- `@api_view(['POST'])` `execute_query` — execute raw SQL, return paginated results
- `@api_view(['POST'])` `save_query` — save a SavedQuery
- `@api_view(['GET'])` `saved_queries` — list saved queries

### Frontend — Stores (Zustand)

#### `store/datasetStore.ts`
- `fetchDatasets()`, `fetchDatasetById(id)`, `fetchDatasetData({id, page, pageSize})`

#### `store/chartStore.ts`
- `fetchCharts()`, `fetchChartById(id)`, `fetchChartData(id)`
- `createChart(data)`, `updateChart({id, data})`, `deleteChart(id)`

#### `store/dashboardStore.ts`
- `fetchDashboards()`, `fetchDashboardById(id)`
- `createDashboard(data)`, `updateDashboard({id, data})`, `updateLayout({id, layout})`, `deleteDashboard(id)`

#### `store/uiStore.ts`
- `theme: 'light' | 'dark'`, `sidebarCollapsed: boolean`
- `toggleTheme()`, `toggleSidebar()`

### Frontend — Chart Components
- `buildEChartsOption(chartType, labels, values, groups)` → ECharts option object
- `EChartRenderer({ option, height })` → echarts-for-react wrapper
- `ChartTypeSelector({ value, onChange })` → Ant Design Radio.Group
- `ColumnMapper({ columns, config, onChange })` → Ant Design Select
- `FilterBuilder({ columns, filters, onChange })` → dynamic filter rows
- `useChartData(chartId, config)` → { data, loading, error }

### Frontend — Auth Utilities
- `setCookie(name, value, days)` / `getCookie(name)` / `removeCookie(name)` — cookie helpers (prefix `bi_`, SameSite=Strict)
- `isAuthenticated()` → boolean (checks for `bi_access_token` cookie)

---

## [Classes]

### Backend — New Django Apps

| App | Model | ViewSet | Serializer |
|-----|-------|---------|------------|
| `datasets` | `Dataset` | `DatasetViewSet` | `DatasetSerializer` + `DatasetDataSerializer` |
| `charts` | `Chart` | `ChartViewSet` | `ChartSerializer` + `ChartDataSerializer` |
| `charts` | `SavedQuery` | (via query/views.py) | `SavedQuerySerializer` |
| `dashboards` | `Dashboard` | `DashboardViewSet` | `DashboardSerializer` + `DashboardRenderSerializer` |

### Frontend — Components (all Ant Design + Tailwind)

| Component | File | Ant Design Components Used |
|-----------|------|---------------------------|
| App | `App.tsx` | ConfigProvider (theme), ProtectedRoute (auth guard) |
| AppLayout | `Layout.tsx` | Layout, Sider, Header, Content |
| Sidebar | `Sidebar.tsx` | Menu |
| TopBar | `TopBar.tsx` | Button, Space, Switch, Dropdown (logout) |
| LoginPage | `pages/LoginPage.tsx` | Card, Form, Input, Button, Alert, Typography |
| DashboardList | `pages/DashboardList.tsx` | Card, Row, Col, Modal, Button |
| DashboardView | `pages/DashboardView.tsx` | Spin, Button, react-grid-layout |
| ChartBuilder | `pages/ChartBuilder.tsx` | Form, Select, Radio, Button, Spin, Card |
| ChartList | `pages/ChartList.tsx` | Card, Modal, Button |
| DatasetList | `pages/DatasetList.tsx` | Table, Button, Modal |
| SQLEditor | `pages/SQLEditor.tsx` | Monaco Editor, Table, Button, Spin |
| EChartRenderer | `components/charts/EChartRenderer.tsx` | echarts-for-react + Tailwind |
| ChartTypeSelector | `components/charts/ChartTypeSelector.tsx` | Radio, Tag |
| ColumnMapper | `components/charts/ColumnMapper.tsx` | Select |
| ChartPreview | `components/charts/ChartPreview.tsx` | Card, Spin |
| FilterBuilder | `components/charts/FilterBuilder.tsx` | Select, Input, Button, Space |

---

## [Dependencies]

### Backend — Already in djankit (no new packages needed)
All required Python packages are already in `pyproject.toml` / `requirements.txt`:
- `django==5.2.9`, `djangorestframework==3.16.0`
- `drf-spectacular`, `django-filter`, `django-cors-headers`
- `djangorestframework-simplejwt` (JWT auth)
- `pandas`, `numpy`, `openpyxl` (data processing/excel)
- `django-import-export` (CSV import/export)
- `psycopg2-binary`, `psycopg[binary,pool]` (PostgreSQL)
- `celery`, `redis` (background tasks)

### Frontend — `package.json`
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "antd": "^5.20.0",
    "@ant-design/icons": "^5.4.0",
    "zustand": "^4.5.0",
    "axios": "^1.7.0",
    "echarts": "^5.5.0",
    "echarts-for-react": "^3.0.0",
    "react-grid-layout": "^1.4.0",
    "monaco-editor": "^0.50.0",
    "@monaco-editor/react": "^4.6.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "@vitejs/plugin-react": "^4.3.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@types/react-grid-layout": "^1.3.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

---

## [Testing]

### Backend (15 tests, all passing)
- `backend/datasets/tests.py` — Test Dataset CRUD via APITestClient
- `backend/charts/tests.py` — Test Chart CRUD + data computation
- `backend/dashboards/tests.py` — Test Dashboard CRUD + layout
- `backend/query/tests.py` — Test SQL execution
- Run: `cd backend && python manage.py test datasets charts dashboards query`

### Frontend (0 tests)
- No frontend tests implemented yet
- Run: `cd frontend && npm test` (no test runner configured)

### Manual Testing
- Backend: `http://localhost:8000/api/docs/` — Swagger UI (already configured in djankit)
- Frontend: `http://localhost:5173` — UI interaction testing
- Login: `http://localhost:5173/login` — default credentials: admin / admin123

---

## [Implementation Order]

### Phase 1: Django Backend Apps ✅ COMPLETE
1. Rename `djankit/` → `backend/`
2. Create `datasets/` app (models.py, serializers.py, views.py, urls.py)
3. Create `charts/` app (models.py, serializers.py, views.py, urls.py)
4. Create `dashboards/` app (models.py, serializers.py, views.py, urls.py)
5. Create `query/` app (views.py, urls.py)
6. Update `config/settings/base.py` — add new apps to INSTALLED_APPS
7. Update `config/urls.py` — register new routers
8. Create `seed_data.py` management command
9. Run migrations, seed data, test via Swagger UI

### Phase 2: Frontend Shell ✅ COMPLETE
1. Create `frontend/` with Vite + React + TypeScript
2. Install dependencies
3. Configure Tailwind CSS
4. Create API client + API modules
5. Create Zustand stores
6. Create Layout, Sidebar, TopBar components
7. Create placeholder pages
8. Wire up routing + Ant Design ConfigProvider

### Phase 3: Chart Builder ✅ COMPLETE
1. Create EChartRenderer, ChartTypeSelector, ColumnMapper, FilterBuilder
2. Create chartOptions.ts utility
3. Create useChartData hook
4. Build full ChartBuilder page
5. Wire save/load to Django API

### Phase 4: Dashboard Builder ✅ COMPLETE
1. Create DashboardView with react-grid-layout
2. Implement chart add/remove modal
3. Implement layout save on drag end
4. Create full DashboardList with CRUD

### Phase 5: SQL Editor ✅ COMPLETE
1. Create execute_query + saved_queries endpoints
2. Integrate Monaco Editor
3. Build results table with Ant Design Table
4. Implement CSV export
5. Add load/delete saved queries

### Phase 6: Polish ⚠️ PARTIAL
1. ❌ CSV upload for datasets
2. ✅ Dark/Light theme toggle
3. ❌ Dashboard PNG export
4. ⚠️ Responsive design (Tailwind configured, DashboardList uses responsive grid)
5. ✅ Loading/error states (Spin + Alert on all pages)

### Authentication ✅ COMPLETE (added after original plan)
1. Create cookie utility (`utils/cookies.ts`) — setCookie, getCookie, removeCookie
2. Rewrite axios client (`api/client.ts`) — read token from cookie, withCredentials, token refresh
3. Create LoginPage (`pages/LoginPage.tsx`) — form → `/api/token/` → set cookies → redirect `/dashboards`
4. Add ProtectedRoute in App.tsx — redirect `/login` if unauthenticated
5. Add logout to TopBar — clear cookies → `/login`
6. Update backend CORS — `CORS_ALLOW_CREDENTIALS = True`, add `localhost:5173`
