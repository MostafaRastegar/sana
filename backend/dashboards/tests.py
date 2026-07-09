from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from dashboards.models import Dashboard


class DashboardAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(username="admin", password="admin123", email="admin@test.com")
        self.client.force_authenticate(user=self.user)

    def test_create_dashboard(self):
        resp = self.client.post("/api/dashboards/", {
            "name": "Test Dashboard",
            "description": "A test",
        })
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Dashboard.objects.count(), 1)

    def test_list_dashboards(self):
        Dashboard.objects.create(name="D1", created_by=self.user)
        Dashboard.objects.create(name="D2", created_by=self.user)
        resp = self.client.get("/api/dashboards/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 2)

    def test_update_layout(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.user)
        layout = {"charts": [{"chart_id": 1, "x": 0, "y": 0, "w": 6, "h": 4}]}
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/layout/",
            {"layout": layout},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        dash.refresh_from_db()
        self.assertEqual(dash.layout, layout)

    def test_delete_dashboard(self):
        dash = Dashboard.objects.create(name="ToDelete", created_by=self.user)
        resp = self.client.delete(f"/api/dashboards/{dash.id}/")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Dashboard.objects.count(), 0)
