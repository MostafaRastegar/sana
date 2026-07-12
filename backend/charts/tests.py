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
            columns=[{"name": "id", "type": "integer"}, {"name": "name", "type": "string"}, {"name": "value", "type": "decimal"}],
            created_by=self.user,
        )

    def tearDown(self):
        with connection.cursor() as c:
            c.execute("DROP TABLE IF EXISTS test_chart_data")

    def test_create_chart(self):
        resp = self.client.post("/api/charts/", {
            "name": "Test Chart",
            "dataset": self.dataset.id,
            "chart_type": "bar",
            "config": {"x_axis": "name", "y_axis": "value"},
        }, format="json")
        self.assertEqual(resp.status_code, 201)

    def test_chart_data_action(self):
        chart = Chart.objects.create(
            name="C1", dataset=self.dataset, chart_type="bar",
            config={"x_axis": "name", "y_axis": "value", "aggregate": "none"},
            created_by=self.user,
        )
        resp = self.client.get(f"/api/charts/{chart.id}/data/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("rows", resp.data["data"])
        self.assertEqual(len(resp.data["data"]["rows"]), 2)

    def test_list_charts(self):
        Chart.objects.create(
            name="C1", dataset=self.dataset, chart_type="line",
            config={"x_axis": "name", "y_axis": "value"}, created_by=self.user,
        )
        resp = self.client.get("/api/charts/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)


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
