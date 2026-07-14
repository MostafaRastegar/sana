from django.test import TestCase
from django.contrib.auth.models import User
from django.db import connection
from rest_framework.test import APIClient
from charts.models import Chart, SavedQuery
from datasets.models import Dataset


class ChartAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(username="admin", password="admin123", email="admin@test.com")
        self.client.force_authenticate(user=self.user)
        with connection.cursor() as c:
            c.execute("CREATE TABLE IF NOT EXISTS test_chart_data (id INTEGER, name TEXT, value REAL)")
            c.execute("INSERT INTO test_chart_data VALUES (1, 'a', 10.0), (2, 'b', 20.0)")
        self.dataset = Dataset.objects.create(
            name="Test DS", table_name="test_chart_data",
            columns=[{"name": "id", "type": "integer", "label": "ID"}, {"name": "name", "type": "string", "label": "Name"}, {"name": "value", "type": "decimal", "label": "Value"}],
            created_by=self.user,
        )
        self.chart = Chart.objects.create(
            name="C1", dataset=self.dataset, chart_type="bar",
            config={"x_axis": "name", "y_axis": "value", "aggregate": "none"},
            created_by=self.user,
        )

    def tearDown(self):
        with connection.cursor() as c:
            # drop all test tables to avoid leakage across test classes
            for tbl in ["test_chart_data"]:
                c.execute(f"DROP TABLE IF EXISTS {tbl}")

    def test_create_chart(self):
        resp = self.client.post("/api/charts/", {
            "name": "Test Chart",
            "dataset": self.dataset.id,
            "chart_type": "bar",
            "config": {"x_axis": "name", "y_axis": "value"},
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_create_chart_all_types(self):
        for ct in ["bar", "line", "pie", "area", "kpi"]:
            resp = self.client.post("/api/charts/", {
                "name": f"Chart {ct}",
                "dataset": self.dataset.id,
                "chart_type": ct,
                "config": {"x_axis": "name", "y_axis": "value"} if ct != "kpi" else {"metric": "value"},
            }, format="json")
            self.assertEqual(resp.status_code, 201, f"Failed for chart_type={ct}")

    def test_list_charts(self):
        resp = self.client.get("/api/charts/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_retrieve_chart(self):
        resp = self.client.get(f"/api/charts/{self.chart.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["name"], "C1")

    def test_update_chart(self):
        resp = self.client.put(f"/api/charts/{self.chart.id}/", {
            "name": "Updated", "dataset": self.dataset.id,
            "chart_type": "line", "config": {"x_axis": "name", "y_axis": "value"},
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.chart.refresh_from_db()
        self.assertEqual(self.chart.name, "Updated")

    def test_delete_chart(self):
        resp = self.client.delete(f"/api/charts/{self.chart.id}/")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Chart.objects.count(), 0)


    def test_chart_data_action(self):
        resp = self.client.get(f"/api/charts/{self.chart.id}/data/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("rows", resp.data["data"])
        self.assertEqual(len(resp.data["data"]["rows"]), 2)

    def test_chart_data_table_not_found(self):
        ds2 = Dataset.objects.create(
            name="NoTable", table_name="nonexistent_table",
            columns=[{"name": "x", "type": "string", "label": "X"}], created_by=self.user,
        )
        c = Chart.objects.create(
            name="Bad", dataset=ds2, chart_type="bar",
            config={"x_axis": "x", "y_axis": "y"}, created_by=self.user,
        )
        resp = self.client.get(f"/api/charts/{c.id}/data/")
        self.assertEqual(resp.status_code, 404)

    def test_preview_with_query(self):
        resp = self.client.post("/api/charts/preview/", {
            "dataset": self.dataset.id,
            "config": {"x_axis": "name", "y_axis": "value"},
            "chart_type": "bar",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("columns", resp.data)
        self.assertIn("rows", resp.data)

    def test_preview_missing_dataset(self):
        resp = self.client.post("/api/charts/preview/", {
            "config": {"x_axis": "name", "y_axis": "value"},
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_preview_dataset_not_found(self):
        resp = self.client.post("/api/charts/preview/", {
            "dataset": 99999, "config": {"x_axis": "name", "y_axis": "value"},
        }, format="json")
        self.assertEqual(resp.status_code, 404)

    def test_preview_table_not_found(self):
        ds2 = Dataset.objects.create(
            name="NoTable", table_name="nonexistent_table",
            columns=[{"name": "x", "type": "string", "label": "X"}], created_by=self.user,
        )
        resp = self.client.post("/api/charts/preview/", {
            "dataset": ds2.id, "config": {"x_axis": "x", "y_axis": "y"},
        }, format="json")
        self.assertEqual(resp.status_code, 404)

    def test_drill_down_no_target(self):
        resp = self.client.get(f"/api/charts/{self.chart.id}/drill_down/?column=name&value=a")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["data"]["rows"]), 1)

    def test_drill_down_missing_params(self):
        resp = self.client.get(f"/api/charts/{self.chart.id}/drill_down/")
        self.assertEqual(resp.status_code, 400)

    def test_drill_down_with_target(self):
        target = Chart.objects.create(
            name="Target", dataset=self.dataset, chart_type="line",
            config={"y_axis": "value"}, created_by=self.user,
        )
        resp = self.client.get(
            f"/api/charts/{self.chart.id}/drill_down/?column=name&value=a&target_chart_id={target.id}"
        )
        self.assertEqual(resp.status_code, 200)

    def test_drill_down_target_not_found(self):
        resp = self.client.get(
            f"/api/charts/{self.chart.id}/drill_down/?column=name&value=a&target_chart_id=99999"
        )
        self.assertEqual(resp.status_code, 404)

    def test_drill_down_table_not_found(self):
        ds2 = Dataset.objects.create(
            name="NoTable", table_name="nonexistent_table",
            columns=[{"name": "x", "type": "string", "label": "X"}], created_by=self.user,
        )
        c = Chart.objects.create(
            name="Bad", dataset=ds2, chart_type="bar",
            config={"x_axis": "x", "y_axis": "y"}, created_by=self.user,
        )
        resp = self.client.get(f"/api/charts/{c.id}/drill_down/?column=x&value=1")
        self.assertEqual(resp.status_code, 404)

    def test_export_csv(self):
        resp = self.client.get(f"/api/charts/{self.chart.id}/export/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/csv")

    def test_export_table_not_found(self):
        ds2 = Dataset.objects.create(
            name="NoTable", table_name="nonexistent_table",
            columns=[{"name": "x", "type": "string", "label": "X"}], created_by=self.user,
        )
        c = Chart.objects.create(
            name="Bad", dataset=ds2, chart_type="bar",
            config={"x_axis": "x", "y_axis": "y"}, created_by=self.user,
        )
        resp = self.client.get(f"/api/charts/{c.id}/export/")
        self.assertEqual(resp.status_code, 404)

    def test_filter_by_chart_type(self):
        Chart.objects.create(
            name="Line", dataset=self.dataset, chart_type="line",
            config={"x_axis": "name", "y_axis": "value"}, created_by=self.user,
        )
        resp = self.client.get("/api/charts/?chart_type=line")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["chart_type"], "line")

    def test_filter_by_dataset_id(self):
        ds2 = Dataset.objects.create(
            name="DS2", table_name="test_chart_data",
            columns=[{"name": "id", "type": "integer", "label": "ID"}], created_by=self.user,
        )
        Chart.objects.create(
            name="C2", dataset=ds2, chart_type="bar",
            config={"x_axis": "name", "y_axis": "value"}, created_by=self.user,
        )
        resp = self.client.get(f"/api/charts/?dataset_id={self.dataset.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["name"], "C1")

    def test_search_by_name(self):
        resp = self.client.get("/api/charts/?search=C1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_delete_non_existent(self):
        resp = self.client.delete("/api/charts/99999/")
        self.assertEqual(resp.status_code, 404)

    def test_chart_data_with_aggregate(self):
        c = Chart.objects.create(
            name="Agg", dataset=self.dataset, chart_type="bar",
            config={"x_axis": "name", "y_axis": "value", "aggregate": "sum"},
            created_by=self.user,
        )
        resp = self.client.get(f"/api/charts/{c.id}/data/")
        self.assertEqual(resp.status_code, 200)

    def test_chart_data_with_filters(self):
        c = Chart.objects.create(
            name="Filtered", dataset=self.dataset, chart_type="bar",
            config={
                "x_axis": "name", "y_axis": "value", "aggregate": "none",
                "filters": [{"column": "name", "operator": "eq", "value": "a"}],
            },
            created_by=self.user,
        )
        resp = self.client.get(f"/api/charts/{c.id}/data/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["data"]["rows"]), 1)

    def test_chart_data_with_global_filters(self):
        resp = self.client.get(
            f"/api/charts/{self.chart.id}/data/?global_filters=%5B%7B%22column%22%3A%20%22name%22%2C%20%22operator%22%3A%20%22eq%22%2C%20%22value%22%3A%20%22a%22%7D%5D"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["data"]["rows"]), 1)

    def test_chart_data_invalid_global_filters_ignored(self):
        resp = self.client.get(
            f"/api/charts/{self.chart.id}/data/?global_filters=not-json"
        )
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/charts/")
        self.assertEqual(resp.status_code, 401)

class SavedQueryTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(username="admin", password="admin123", email="admin@test.com")
        self.client.force_authenticate(user=self.user)

    def test_save_and_list_queries(self):
        resp = self.client.post("/api/queries/", {"name": "Q1", "sql": "SELECT 1"}, format="json")
        self.assertEqual(resp.status_code, 201)
        resp = self.client.get("/api/queries/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)