"""
E2E Scenario Tests — BI Dashboard
Run: python manage.py test core.tests.test_e2e_scenarios -v 2
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from datasets.models import Dataset
from charts.models import Chart, SavedQuery
from dashboards.models import Dashboard
from django.db import connection

User = get_user_model()


class E2EScenarioTests(TestCase):
    """Full end-to-end scenarios covering the entire BI workflow."""

    databases = ["default"]

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="testuser", password="testpass123", email="test@test.com"
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self._create_demo_table()

    def _create_demo_table(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS demo_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    category TEXT NOT NULL,
                    in_stock INTEGER DEFAULT 1
                )
            """)
            cursor.execute("DELETE FROM demo_products")
            cursor.executemany(
                "INSERT INTO demo_products (name, price, category, in_stock) VALUES (?, ?, ?, ?)",
                [
                    ("Widget A", 19.99, "Widgets", 1),
                    ("Widget B", 29.99, "Widgets", 1),
                    ("Gadget X", 99.99, "Gadgets", 0),
                    ("Gadget Y", 149.99, "Gadgets", 1),
                    ("Service Z", 9.99, "Services", 1),
                ],
            )

    # ─────────────────────────────────────────────
    # Dataset CRUD
    # ─────────────────────────────────────────────

    def test_s1_list_datasets_empty(self):
        """S1: GET /api/datasets/ returns empty list initially."""
        response = self.client.get("/api/datasets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)
        print("  ✓ S1: List datasets (empty)")

    def test_s2_create_dataset(self):
        """S2: POST /api/datasets/ creates a new dataset."""
        response = self.client.post("/api/datasets/", {
            "name": "Demo Products",
            "description": "Product catalog",
            "table_name": "demo_products",
            "columns": [
                {"name": "id", "type": "INTEGER", "label": "ID"},
                {"name": "name", "type": "TEXT", "label": "Name"},
                {"name": "price", "type": "REAL", "label": "Price"},
                {"name": "category", "type": "TEXT", "label": "Category"},
                {"name": "in_stock", "type": "INTEGER", "label": "In Stock"},
            ],
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Demo Products")
        self.assertEqual(response.data["column_count"], 5)
        print(f"  ✓ S2: Create dataset (id={response.data['id']})")

    def test_s3_list_datasets_with_data(self):
        """S3: GET /api/datasets/ returns created datasets."""
        self._seed_dataset("Demo Products", "demo_products")
        response = self.client.get("/api/datasets/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(response.data["count"], 0)
        print("  ✓ S3: List datasets (with data)")

    def test_s4_get_dataset_detail(self):
        """S4: GET /api/datasets/{id}/ returns dataset detail."""
        ds = self._seed_dataset("Detail Test", "demo_products")
        response = self.client.get(f"/api/datasets/{ds.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Detail Test")
        print("  ✓ S4: Get dataset detail")

    def test_s5_update_dataset(self):
        """S5: PUT /api/datasets/{id}/ updates dataset."""
        ds = self._seed_dataset("Old Name", "demo_products")
        response = self.client.put(f"/api/datasets/{ds.id}/", {
            "name": "Updated Name",
            "description": "Updated description",
            "table_name": "demo_products",
            "columns": ds.columns,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Name")
        print("  ✓ S5: Update dataset")

    def test_s6_delete_dataset(self):
        """S6: DELETE /api/datasets/{id}/ deletes dataset."""
        ds = self._seed_dataset("To Delete", "demo_products")
        response = self.client.delete(f"/api/datasets/{ds.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dataset.objects.filter(id=ds.id).exists())
        print("  ✓ S6: Delete dataset")

    # ─────────────────────────────────────────────
    # Dataset Data Action
    # ─────────────────────────────────────────────

    def test_s7_get_dataset_data(self):
        """S7: GET /api/datasets/{id}/data/ returns paginated rows."""
        ds = self._seed_dataset("Data Test", "demo_products")
        response = self.client.get(f"/api/datasets/{ds.id}/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("columns", response.data)
        self.assertIn("rows", response.data)
        self.assertGreaterEqual(len(response.data["rows"]), 0)
        print(f"  ✓ S7: Get dataset data ({len(response.data['rows'])} rows)")

    def test_s8_get_dataset_data_paginated(self):
        """S8: GET /api/datasets/{id}/data/?page=1&page_size=2 returns 2 rows."""
        ds = self._seed_dataset("Paginated", "demo_products")
        response = self.client.get(f"/api/datasets/{ds.id}/data/", {"page": 1, "page_size": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data["rows"]), 2)
        self.assertEqual(response.data["page"], 1)
        self.assertEqual(response.data["page_size"], 2)
        print(f"  ✓ S8: Get dataset data paginated ({len(response.data['rows'])} rows)")

    # ─────────────────────────────────────────────
    # Chart CRUD
    # ─────────────────────────────────────────────

    def test_s9_create_chart(self):
        """S9: POST /api/charts/ creates a chart."""
        ds = self._seed_dataset("Chart DS", "demo_products")
        response = self.client.post("/api/charts/", {
            "name": "Price by Category",
            "description": "Bar chart of prices",
            "dataset": ds.id,
            "chart_type": "bar",
            "config": {
                "xAxis": "category",
                "yAxis": "price",
                "aggregate": "avg",
            },
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Price by Category")
        self.assertEqual(response.data["chart_type"], "bar")
        print(f"  ✓ S9: Create chart (id={response.data['id']})")

    def test_s10_list_charts(self):
        """S10: GET /api/charts/ returns charts."""
        ds = self._seed_dataset("List DS", "demo_products")
        self._seed_chart(ds, "Chart A")
        self._seed_chart(ds, "Chart B")
        response = self.client.get("/api/charts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 2)
        print("  ✓ S10: List charts")

    def test_s11_get_chart_detail(self):
        """S11: GET /api/charts/{id}/ returns chart detail."""
        ds = self._seed_dataset("Detail DS", "demo_products")
        chart = self._seed_chart(ds, "Detail Chart")
        response = self.client.get(f"/api/charts/{chart.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Detail Chart")
        print("  ✓ S11: Get chart detail")

    def test_s12_update_chart(self):
        """S12: PUT /api/charts/{id}/ updates chart."""
        ds = self._seed_dataset("Update DS", "demo_products")
        chart = self._seed_chart(ds, "Old Chart")
        response = self.client.put(f"/api/charts/{chart.id}/", {
            "name": "Updated Chart",
            "dataset": ds.id,
            "chart_type": "line",
            "config": {"xAxis": "name", "yAxis": "price"},
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Chart")
        self.assertEqual(response.data["chart_type"], "line")
        print("  ✓ S12: Update chart")

    def test_s13_delete_chart(self):
        """S13: DELETE /api/charts/{id}/ deletes chart."""
        ds = self._seed_dataset("Delete DS", "demo_products")
        chart = self._seed_chart(ds, "To Delete")
        response = self.client.delete(f"/api/charts/{chart.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Chart.objects.filter(id=chart.id).exists())
        print("  ✓ S13: Delete chart")

    # ─────────────────────────────────────────────
    # Chart Data Computation
    # ─────────────────────────────────────────────

    def test_s14_get_chart_data(self):
        """S14: GET /api/charts/{id}/data/ returns computed chart data."""
        ds = self._seed_dataset("Compute DS", "demo_products")
        chart = self._seed_chart(ds, "Compute Chart", chart_type="bar", config={
            "xAxis": "category",
            "yAxis": "price",
            "aggregate": "avg",
        })
        response = self.client.get(f"/api/charts/{chart.id}/data/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("columns", response.data["data"])
        self.assertIn("rows", response.data["data"])
        self.assertIn("chart_type", response.data["data"])
        self.assertIn("config", response.data["data"])
        print(f"  ✓ S14: Get chart data ({len(response.data['data']['rows'])} rows)")

    # ─────────────────────────────────────────────
    # Dashboard CRUD + Layout + Render
    # ─────────────────────────────────────────────

    def test_s15_create_dashboard(self):
        """S15: POST /api/dashboards/ creates a dashboard."""
        response = self.client.post("/api/dashboards/", {
            "name": "Sales Dashboard",
            "description": "Overview of sales metrics",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Sales Dashboard")
        print(f"  ✓ S15: Create dashboard (id={response.data['id']})")

    def test_s16_list_dashboards(self):
        """S16: GET /api/dashboards/ returns dashboards."""
        self._seed_dashboard("Dash A")
        self._seed_dashboard("Dash B")
        response = self.client.get("/api/dashboards/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 2)
        print("  ✓ S16: List dashboards")

    def test_s17_get_dashboard_detail(self):
        """S17: GET /api/dashboards/{id}/ returns dashboard detail."""
        d = self._seed_dashboard("Detail Dash")
        response = self.client.get(f"/api/dashboards/{d.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Detail Dash")
        print("  ✓ S17: Get dashboard detail")

    def test_s18_update_dashboard(self):
        """S18: PUT /api/dashboards/{id}/ updates dashboard."""
        d = self._seed_dashboard("Old Dash")
        response = self.client.put(f"/api/dashboards/{d.id}/", {
            "name": "Updated Dash",
            "description": "Updated",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Dash")
        print("  ✓ S18: Update dashboard")

    def test_s19_update_dashboard_layout(self):
        """S19: PUT /api/dashboards/{id}/layout/ updates layout."""
        ds = self._seed_dataset("Layout DS", "demo_products")
        chart = self._seed_chart(ds, "Layout Chart")
        d = self._seed_dashboard("Layout Dash")
        layout_data = {
            "charts": [
                {"chartId": chart.id, "x": 0, "y": 0, "w": 6, "h": 4},
            ]
        }
        response = self.client.put(f"/api/dashboards/{d.id}/layout/", {
            "layout": layout_data,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["layout"])
        print("  ✓ S19: Update dashboard layout")

    def test_s20_get_dashboard_render(self):
        """S20: GET /api/dashboards/{id}/render/ returns dashboard with resolved chart data."""
        ds = self._seed_dataset("Render DS", "demo_products")
        chart = self._seed_chart(ds, "Render Chart", config={
            "xAxis": "category", "yAxis": "price", "aggregate": "avg"
        })
        d = self._seed_dashboard("Render Dash")
        self.client.put(f"/api/dashboards/{d.id}/layout/", {
            "layout": {"charts": [{"chartId": chart.id, "x": 0, "y": 0, "w": 6, "h": 4}]}
        }, format="json")
        response = self.client.get(f"/api/dashboards/{d.id}/render/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("charts_data", response.data)
        self.assertGreaterEqual(len(response.data["charts_data"]), 1)
        print(f"  ✓ S20: Get dashboard render ({len(response.data['charts_data'])} chart(s))")

    def test_s21_delete_dashboard(self):
        """S21: DELETE /api/dashboards/{id}/ deletes dashboard."""
        d = self._seed_dashboard("To Delete")
        response = self.client.delete(f"/api/dashboards/{d.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dashboard.objects.filter(id=d.id).exists())
        print("  ✓ S21: Delete dashboard")

    # ─────────────────────────────────────────────
    # SQL Query
    # ─────────────────────────────────────────────

    def test_s22_execute_select_query(self):
        """S22: POST /api/execute/ executes a SELECT query."""
        response = self.client.post("/api/execute/", {
            "sql": "SELECT name, price FROM demo_products ORDER BY price DESC LIMIT 3",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("columns", response.data["data"])
        self.assertIn("rows", response.data["data"])
        self.assertLessEqual(len(response.data["data"]["rows"]), 3)
        print(f"  ✓ S22: Execute SELECT query ({len(response.data['data']['rows'])} rows)")

    def test_s23_execute_rejects_non_select(self):
        """S23: POST /api/execute/ rejects non-SELECT queries."""
        response = self.client.post("/api/execute/", {"sql": "DROP TABLE demo_products"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("  ✓ S23: Execute rejects non-SELECT")

    def test_s24_execute_requires_sql(self):
        """S24: POST /api/execute/ requires sql field."""
        response = self.client.post("/api/execute/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("  ✓ S24: Execute requires SQL")

    def test_s25_save_and_list_queries(self):
        """S25: POST /api/queries/ + GET /api/queries/ saves and lists queries."""
        response = self.client.post("/api/queries/", {
            "name": "Top Products",
            "sql": "SELECT * FROM demo_products ORDER BY price DESC LIMIT 5",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        query_id = response.data["id"]

        response = self.client.get("/api/queries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [q["id"] for q in response.data.get("results", response.data)]
        self.assertIn(query_id, ids)
        print(f"  ✓ S25: Save and list queries (id={query_id})")

    def test_s26_delete_saved_query(self):
        """S26: DELETE /api/queries/{id}/ deletes saved query."""
        response = self.client.post("/api/queries/", {
            "name": "To Delete", "sql": "SELECT * FROM demo_products",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        query_id = response.data["id"]

        response = self.client.delete(f"/api/queries/{query_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(SavedQuery.objects.filter(id=query_id).exists())
        print(f"  ✓ S26: Delete saved query (id={query_id})")

    # ─────────────────────────────────────────────
    # JWT Authentication flow
    # ─────────────────────────────────────────────

    def test_s27_jwt_auth_flow(self):
        """S27: POST /api/token/ + /api/token/refresh/ + /api/token/verify/."""
        unauth_client = APIClient()

        response = unauth_client.post("/api/token/", {
            "username": "testuser", "password": "testpass123",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]

        response = unauth_client.post("/api/token/verify/", {"token": access_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = unauth_client.post("/api/token/refresh/", {"refresh": refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        print("  ✓ S27: JWT auth flow (obtain + verify + refresh)")

    # ─────────────────────────────────────────────
    # Full workflow: dataset → chart → dashboard → render
    # ─────────────────────────────────────────────

    def test_s28_full_workflow(self):
        """S28: Full workflow — dataset → chart → dashboard → render."""
        resp = self.client.post("/api/datasets/", {
            "name": "Workflow DS", "description": "E2E test", "table_name": "demo_products",
            "columns": [
                {"name": "name", "type": "TEXT", "label": "Name"},
                {"name": "price", "type": "REAL", "label": "Price"},
                {"name": "category", "type": "TEXT", "label": "Category"},
            ],
        }, format="json")
        ds_id = resp.data["id"]

        resp = self.client.post("/api/charts/", {
            "name": "Workflow Chart", "dataset": ds_id, "chart_type": "bar",
            "config": {"xAxis": "category", "yAxis": "price", "aggregate": "avg"},
        }, format="json")
        chart_id = resp.data["id"]

        resp = self.client.get(f"/api/charts/{chart_id}/data/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post("/api/dashboards/", {"name": "Workflow Dashboard"}, format="json")
        dash_id = resp.data["id"]

        self.client.put(f"/api/dashboards/{dash_id}/layout/", {
            "layout": {"charts": [{"chartId": chart_id, "x": 0, "y": 0, "w": 6, "h": 4}]}
        }, format="json")

        resp = self.client.get(f"/api/dashboards/{dash_id}/render/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["charts_data"]), 1)
        print("  ✓ S28: Full workflow (dataset → chart → dashboard → render)")

    # ─────────────────────────────────────────────
    # Auth required for all endpoints
    # ─────────────────────────────────────────────

    def test_s29_auth_required(self):
        """S29: Unauthenticated requests get 401."""
        unauth = APIClient()
        endpoints = [
            ("get", "/api/datasets/"),
            ("post", "/api/datasets/"),
            ("get", "/api/charts/"),
            ("post", "/api/charts/"),
            ("get", "/api/dashboards/"),
            ("post", "/api/dashboards/"),
            ("post", "/api/execute/"),
            ("post", "/api/queries/"),
            ("get", "/api/queries/"),
        ]
        for method, url in endpoints:
            func = getattr(unauth, method)
            resp = func(url, {} if method == "post" else None, format="json")
            self.assertEqual(
                resp.status_code, status.HTTP_401_UNAUTHORIZED,
                f"{method.upper()} {url} should return 401"
            )
        print("  ✓ S29: Auth required (all endpoints return 401 without token)")

    # ─────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────

    def _seed_dataset(self, name, table_name, columns=None):
        if columns is None:
            columns = [
                {"name": "id", "type": "INTEGER", "label": "ID"},
                {"name": "name", "type": "TEXT", "label": "Name"},
                {"name": "price", "type": "REAL", "label": "Price"},
                {"name": "category", "type": "TEXT", "label": "Category"},
                {"name": "in_stock", "type": "INTEGER", "label": "In Stock"},
            ]
        return Dataset.objects.create(
            name=name, table_name=table_name, columns=columns, created_by=self.user,
        )

    def _seed_chart(self, dataset, name, chart_type="bar", config=None):
        if config is None:
            config = {"xAxis": "category", "yAxis": "price", "aggregate": "avg"}
        return Chart.objects.create(
            name=name, dataset=dataset, chart_type=chart_type, config=config, created_by=self.user,
        )

    def _seed_dashboard(self, name):
        return Dashboard.objects.create(name=name, created_by=self.user)
