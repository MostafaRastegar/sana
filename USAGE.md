# Usage Guide — BI Dashboard

## Prerequisites

- Python 3.11+
- Node.js 18+
- pnpm

## 1. Backend

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate

# Run migrations (already applied)
python manage.py migrate

# Seed demo data (creates tables + sample charts/dashboards)
python manage.py seed_data

# Start dev server
python manage.py runserver 0.0.0.0:8000
```

Backend runs at `http://localhost:8000`

## 2. Frontend

```bash
cd frontend

# Install dependencies (already done)
pnpm install

# Start dev server
pnpm dev
```

Frontend runs at `http://localhost:5173` — proxies `/api` to backend.

## 3. Login

Open `http://localhost:5173` in browser.

Default credentials:
- **Username:** `admin`
- **Password:** `admin123`

The frontend redirects unauthenticated users to `/login`. Tokens are stored in **cookies** (not localStorage) with automatic refresh via axios interceptor. Use the user icon (top-right) to logout.

## 4. What to See

| Page | URL | Description |
|------|-----|-------------|
| Dashboard List | `/dashboards` | CRUD dashboards; "Sales Overview" pre-seeded |
| Dashboard View | `/dashboards/:id` | Drag/resize charts via `react-grid-layout` |
| Chart List | `/charts` | Gallery of saved charts |
| Chart Builder | `/charts/new` | Select dataset → map columns → pick chart type → fetch preview → save |
| Datasets | `/datasets` | Browse available datasets |
| SQL Editor | `/sql` | Write SQL against `demo_*` tables, execute, export CSV |

## 5. API (Swagger)

`http://localhost:8000/api/docs/`

## 6. Running Tests

```bash
cd backend
python manage.py test datasets charts dashboards query
```
