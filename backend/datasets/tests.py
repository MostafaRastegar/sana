from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from datasets.models import Dataset


class DatasetAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(username="admin", password="admin123", email="admin@test.com")
        self.client.force_authenticate(user=self.user)

    def test_list_datasets(self):
        Dataset.objects.create(
            name="Test DS", table_name="test_table", columns=[{"name": "id", "type": "integer"}],
            created_by=self.user,
        )
        resp = self.client.get("/api/datasets/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_create_dataset(self):
        resp = self.client.post("/api/datasets/", {
            "name": "New Dataset",
            "table_name": "new_table",
            "columns": [{"name": "id", "type": "integer", "label": "ID"}],
        }, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Dataset.objects.count(), 1)

    def test_dataset_data_action_missing_table(self):
        ds = Dataset.objects.create(
            name="Test", table_name="nonexistent_table", columns=[{"name": "id", "type": "integer"}],
            created_by=self.user,
        )
        resp = self.client.get(f"/api/datasets/{ds.id}/data/")
        self.assertEqual(resp.status_code, 404)

    def test_delete_dataset(self):
        ds = Dataset.objects.create(
            name="ToDelete", table_name="t", columns=[{"name": "id", "type": "integer"}],
            created_by=self.user,
        )
        resp = self.client.delete(f"/api/datasets/{ds.id}/")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(Dataset.objects.count(), 0)
