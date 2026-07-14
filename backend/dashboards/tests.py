import json
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from dashboards.models import Dashboard, DashboardPermission
from datasets.models import Dataset


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

    def test_layout_none_returns_400(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.user)
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/layout/",
            {"layout": None},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_layout_non_dict_returns_400(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.user)
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/layout/",
            {"layout": "not-a-dict"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_update_filters(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.user)
        filters = [{"id": "f1", "name": "Date Range", "type": "date"}]
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/filters/",
            {"filters": filters},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        dash.refresh_from_db()
        self.assertEqual(dash.filters, filters)

    def test_filters_none_returns_400(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.user)
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/filters/",
            {"filters": None},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_filters_non_list_returns_400(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.user)
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/filters/",
            {"filters": "not-a-list"},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_filter_by_name(self):
        Dashboard.objects.create(name="Alpha", created_by=self.user)
        Dashboard.objects.create(name="Beta", created_by=self.user)
        resp = self.client.get("/api/dashboards/?name=Alpha")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["name"], "Alpha")

    def test_retrieve_dashboard(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.user)
        resp = self.client.get(f"/api/dashboards/{dash.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["name"], "D1")

    def test_update_dashboard(self):
        dash = Dashboard.objects.create(name="Old", created_by=self.user)
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/",
            {"name": "New", "description": "Updated"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        dash.refresh_from_db()
        self.assertEqual(dash.name, "New")

    def test_partial_update_dashboard(self):
        dash = Dashboard.objects.create(name="Old", created_by=self.user)
        resp = self.client.patch(
            f"/api/dashboards/{dash.id}/",
            {"description": "Patched"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        dash.refresh_from_db()
        self.assertEqual(dash.description, "Patched")

    def test_non_existent_dashboard(self):
        resp = self.client.get("/api/dashboards/99999/")
        self.assertEqual(resp.status_code, 404)


class TestDashboardPermissions(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = User.objects.create_user(username="owner", password="pass123")
        self.other = User.objects.create_user(username="other", password="pass123")
        Dataset.objects.create(
            name="ds", table_name="t", columns=[{"name": "x", "type": "int"}],
            created_by=self.owner,
        )

    def test_private_dashboard_denies_unauthenticated(self):
        Dashboard.objects.create(name="Private", created_by=self.owner, is_public=False)
        # Permission class rejects unauthenticated users before get_queryset
        resp = self.client.get("/api/dashboards/")
        self.assertEqual(resp.status_code, 401)

    def test_public_dashboard_still_denies_unauthenticated_list(self):
        """Permission class blocks unauthenticated users at the API level."""
        Dashboard.objects.create(name="Public", created_by=self.owner, is_public=True)
        resp = self.client.get("/api/dashboards/")
        self.assertEqual(resp.status_code, 401)

    def test_public_dashboard_still_protected_for_write(self):
        dash = Dashboard.objects.create(name="Public", created_by=self.owner, is_public=True)
        self.client.force_authenticate(user=self.other)
        resp = self.client.delete(f"/api/dashboards/{dash.id}/")
        self.assertEqual(resp.status_code, 403)

    def test_non_owner_cannot_update_private(self):
        """Non-owner gets 404 because get_queryset excludes private dashboards of other users."""
        dash = Dashboard.objects.create(name="D1", created_by=self.owner, is_public=False)
        self.client.force_authenticate(user=self.other)
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/",
            {"name": "Hacked"},
            format="json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_shared_user_can_view(self):
        dash = Dashboard.objects.create(name="Shared", created_by=self.owner, is_public=False)
        DashboardPermission.objects.create(
            dashboard=dash, user=self.other, permission="view", shared_by=self.owner,
        )
        self.client.force_authenticate(user=self.other)
        resp = self.client.get(f"/api/dashboards/{dash.id}/")
        self.assertEqual(resp.status_code, 200)

    def test_shared_user_can_edit_layout(self):
        dash = Dashboard.objects.create(name="Shared", created_by=self.owner, is_public=False)
        DashboardPermission.objects.create(
            dashboard=dash, user=self.other, permission="edit", shared_by=self.owner,
        )
        self.client.force_authenticate(user=self.other)
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/layout/",
            {"layout": {"charts": []}},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)

    def test_view_only_user_cannot_edit(self):
        dash = Dashboard.objects.create(name="Shared", created_by=self.owner, is_public=False)
        DashboardPermission.objects.create(
            dashboard=dash, user=self.other, permission="view", shared_by=self.owner,
        )
        self.client.force_authenticate(user=self.other)
        resp = self.client.put(
            f"/api/dashboards/{dash.id}/layout/",
            {"layout": {"charts": []}},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_permissions_endpoint_get(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.owner, is_public=False)
        DashboardPermission.objects.create(
            dashboard=dash, user=self.other, permission="view", shared_by=self.owner,
        )
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get(f"/api/dashboards/{dash.id}/permissions/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_permissions_endpoint_create(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.owner)
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(
            f"/api/dashboards/{dash.id}/permissions/",
            {"user": self.other.id, "permission": "view"},
            format="json",
        )
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(DashboardPermission.objects.count(), 1)

    def test_permissions_endpoint_delete(self):
        dash = Dashboard.objects.create(name="D1", created_by=self.owner)
        perm = DashboardPermission.objects.create(
            dashboard=dash, user=self.other, permission="view", shared_by=self.owner,
        )
        self.client.force_authenticate(user=self.owner)
        resp = self.client.delete(
            f"/api/dashboards/{dash.id}/permissions/",
            {"id": perm.id},
            format="json",
        )
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(DashboardPermission.objects.count(), 0)

    def test_permissions_denied_for_non_owner(self):
        """Non-owner gets 404 (queryset filter) before reaching permissions endpoint."""
        dash = Dashboard.objects.create(name="D1", created_by=self.owner)
        self.client.force_authenticate(user=self.other)
        resp = self.client.get(f"/api/dashboards/{dash.id}/permissions/")
        self.assertEqual(resp.status_code, 404)

    def test_non_owner_cannot_delete(self):
        """Non-owner gets 404 (get_queryset filter) before reaching perform_destroy."""
        dash = Dashboard.objects.create(name="D1", created_by=self.owner)
        self.client.force_authenticate(user=self.other)
        resp = self.client.delete(f"/api/dashboards/{dash.id}/")
        self.assertEqual(resp.status_code, 404)


