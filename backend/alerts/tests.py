import json
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from datasets.models import Dataset
from .models import DataAlert, AlertHistory

User = get_user_model()


def _assign_all_perms(user):
    """Assign all DataAlert permissions to user."""
    ct = ContentType.objects.get_for_model(DataAlert)
    perms = Permission.objects.filter(content_type=ct)
    user.user_permissions.add(*perms)


class DataAlertModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.dataset = Dataset.objects.create(
            name="Test Dataset",
            table_name="test_table",
            columns={"id": "integer", "name": "text", "amount": "real", "revenue": "real", "sales": "real", "count": "integer"},
            created_by=self.user,
        )

    def test_create_alert(self):
        alert = DataAlert.objects.create(
            name="Sales Threshold",
            dataset=self.dataset,
            condition="above",
            threshold=1000.0,
            metric="amount",
            aggregation="sum",
            check_interval="daily",
            notification_channels=["email"],
            created_by=self.user,
            is_active=True,
        )
        assert alert.name == "Sales Threshold"
        assert alert.is_active is True
        assert alert.last_checked is None
        assert str(alert) == "Sales Threshold (Above 1000.0)"

    def test_alert_history(self):
        alert = DataAlert.objects.create(
            name="Test Alert",
            dataset=self.dataset,
            condition="above",
            threshold=500.0,
            metric="revenue",
            aggregation="sum",
            notification_channels=["email"],
            created_by=self.user,
        )
        history = AlertHistory.objects.create(
            alert=alert,
            actual_value=600.0,
            threshold=500.0,
            condition="above",
            message="Revenue exceeded threshold",
        )
        assert float(history.actual_value) == 600.0
        assert str(history).startswith("Test Alert")


class DataAlertAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="alertuser", password="alertpass123"
        )
        self.client.force_authenticate(user=self.user)
        _assign_all_perms(self.user)
        self.dataset = Dataset.objects.create(
            name="API Dataset",
            table_name="api_table",
            columns={"id": "integer", "name": "text", "amount": "real", "revenue": "real", "sales": "real", "count": "integer"},
            created_by=self.user,
        )

    def test_list_alerts_empty(self):
        url = reverse("alert-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_create_alert(self):
        url = reverse("alert-list")
        payload = {
            "name": "High Sales Alert",
            "dataset": self.dataset.id,
            "condition": "above",
            "threshold": 5000.0,
            "metric": "sales",
            "aggregation": "sum",
            "check_interval": "daily",
            "notification_channels": ["email"],
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        assert response.data["name"] == "High Sales Alert"

    def test_toggle_alert(self):
        alert = DataAlert.objects.create(
            name="Toggle Test",
            dataset=self.dataset,
            condition="below",
            threshold=100.0,
            metric="count",
            aggregation="count",
            notification_channels=["email"],
            created_by=self.user,
            is_active=False,
        )
        url = reverse("alert-toggle", args=[alert.id])
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is True

        # Toggle again -> back to False
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["is_active"] is False

    def test_stats(self):
        DataAlert.objects.create(
            name="Active Alert",
            dataset=self.dataset,
            condition="above",
            threshold=10.0,
            metric="x",
            aggregation="count",
            notification_channels=["email"],
            created_by=self.user,
            is_active=True,
        )
        DataAlert.objects.create(
            name="Inactive Alert",
            dataset=self.dataset,
            condition="above",
            threshold=20.0,
            metric="y",
            aggregation="count",
            notification_channels=["email"],
            created_by=self.user,
            is_active=False,
        )
        url = reverse("alert-stats")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["total_alerts"] == 2
        assert response.data["data"]["active_alerts"] == 1

    def test_filter_by_dataset(self):
        ds2 = Dataset.objects.create(
            name="Second Dataset", table_name="second_table",
            columns={"id": "integer", "name": "text", "amount": "real"},
            created_by=self.user,
        )
        # Give view-only perm so the list filter test works
        ct = ContentType.objects.get_for_model(DataAlert)
        view_perm = Permission.objects.get(content_type=ct, codename="view_dataalert")
        self.user.user_permissions.add(view_perm)
        DataAlert.objects.create(
            name="Alert 1",
            dataset=self.dataset,
            condition="above",
            threshold=10.0,
            metric="x",
            aggregation="count",
            notification_channels=["email"],
            created_by=self.user,
        )
        DataAlert.objects.create(
            name="Alert 2",
            dataset=ds2,
            condition="above",
            threshold=20.0,
            metric="y",
            aggregation="count",
            notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-list") + f"?dataset_id={self.dataset.id}"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Alert 1"