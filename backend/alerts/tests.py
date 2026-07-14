import json
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from datasets.models import Dataset
from alerts.models import DataAlert, AlertHistory
from alerts.services import _evaluate_condition, check_alert

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
            columns={
                "id": "integer", "name": "text", "amount": "real",
                "revenue": "real", "sales": "real", "count": "integer",
            },
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

    def test_alert_str_condition_below(self):
        alert = DataAlert.objects.create(
            name="Low Stock",
            dataset=self.dataset,
            condition="below",
            threshold=50.0,
            metric="count",
            aggregation="count",
            notification_channels=["email"],
            created_by=self.user,
        )
        assert str(alert) == "Low Stock (Below 50.0)"

    def test_alert_str_condition_change_percent(self):
        alert = DataAlert.objects.create(
            name="Growth",
            dataset=self.dataset,
            condition="change_percent",
            threshold=10.0,
            metric="revenue",
            aggregation="sum",
            notification_channels=["email"],
            created_by=self.user,
        )
        assert str(alert) == "Growth (Percent Change 10.0)"

    def test_alert_history_notification_sent(self):
        alert = DataAlert.objects.create(
            name="Notify Test",
            dataset=self.dataset,
            condition="above",
            threshold=100.0,
            metric="amount",
            aggregation="sum",
            notification_channels=["email"],
            created_by=self.user,
        )
        history = AlertHistory.objects.create(
            alert=alert,
            actual_value=200.0,
            threshold=100.0,
            condition="above",
            message="Triggered",
            notification_sent=True,
            notification_response='{"status": "sent"}',
        )
        assert history.notification_sent is True
        assert json.loads(history.notification_response) == {"status": "sent"}

    def test_alert_ordering_default(self):
        a1 = DataAlert.objects.create(
            name="First", dataset=self.dataset, condition="above", threshold=1,
            metric="x", aggregation="count", notification_channels=["email"],
            created_by=self.user,
        )
        a2 = DataAlert.objects.create(
            name="Second", dataset=self.dataset, condition="above", threshold=2,
            metric="y", aggregation="count", notification_channels=["email"],
            created_by=self.user,
        )
        qs = DataAlert.objects.all()
        assert list(qs) == [a2, a1]

    def test_alert_history_ordering(self):
        alert = DataAlert.objects.create(
            name="Order Test",
            dataset=self.dataset,
            condition="above",
            threshold=100.0,
            metric="amount",
            aggregation="sum",
            notification_channels=["email"],
            created_by=self.user,
        )
        h1 = AlertHistory.objects.create(
            alert=alert, actual_value=100.0, threshold=100.0, condition="above",
        )
        h2 = AlertHistory.objects.create(
            alert=alert, actual_value=200.0, threshold=100.0, condition="above",
        )
        qs = AlertHistory.objects.filter(alert=alert).order_by("-triggered_at")
        assert list(qs) == [h2, h1]


class DataAlertSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="serializeruser", password="testpass123"
        )
        self.dataset = Dataset.objects.create(
            name="Serializer Dataset",
            table_name="ser_table",
            columns={"id": "integer", "value": "real"},
            created_by=self.user,
        )

    def test_validate_name_too_short(self):
        from alerts.serializers import DataAlertSerializer

        data = {
            "name": "X",
            "dataset": self.dataset.id,
            "condition": "above",
            "threshold": 100.0,
            "metric": "value",
            "aggregation": "sum",
            "check_interval": "daily",
            "notification_channels": ["email"],
        }
        serializer = DataAlertSerializer(data=data)
        assert serializer.is_valid() is False
        assert "name" in serializer.errors

    def test_validate_threshold_zero_for_change_percent(self):
        from alerts.serializers import DataAlertSerializer

        data = {
            "name": "Valid Name",
            "dataset": self.dataset.id,
            "condition": "change_percent",
            "threshold": 0,
            "metric": "value",
            "aggregation": "sum",
            "check_interval": "daily",
            "notification_channels": ["email"],
        }
        serializer = DataAlertSerializer(data=data)
        assert serializer.is_valid() is False
        assert "threshold" in serializer.errors

    def test_validate_threshold_zero_for_above_ok(self):
        from alerts.serializers import DataAlertSerializer

        data = {
            "name": "Valid Name",
            "dataset": self.dataset.id,
            "condition": "above",
            "threshold": 0,
            "metric": "value",
            "aggregation": "sum",
            "check_interval": "daily",
            "notification_channels": ["email"],
        }
        serializer = DataAlertSerializer(data=data)
        assert serializer.is_valid() is True

    def test_serializer_create_with_recipients(self):
        from alerts.serializers import DataAlertSerializer

        user2 = User.objects.create_user(username="recipient1", password="pass")
        data = {
            "name": "With Recipients",
            "dataset": self.dataset.id,
            "condition": "above",
            "threshold": 100.0,
            "metric": "value",
            "aggregation": "sum",
            "check_interval": "daily",
            "notification_channels": ["email"],
            "recipient_ids": [user2.id],
        }
        serializer = DataAlertSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        alert = serializer.save(created_by=self.user)
        assert alert.recipients.count() == 1
        assert alert.recipients.first() == user2

    def test_serializer_update_recipients(self):
        from alerts.serializers import DataAlertSerializer

        user2 = User.objects.create_user(username="recipient2", password="pass")
        alert = DataAlert.objects.create(
            name="Update Test",
            dataset=self.dataset,
            condition="above",
            threshold=100.0,
            metric="value",
            aggregation="sum",
            check_interval="daily",
            notification_channels=["email"],
            created_by=self.user,
        )
        data = {"recipient_ids": [user2.id]}
        serializer = DataAlertSerializer(alert, data=data, partial=True)
        assert serializer.is_valid(), serializer.errors
        serializer.save()
        assert alert.recipients.count() == 1
        assert alert.recipients.first() == user2


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
            columns={
                "id": "integer", "name": "text", "amount": "real",
                "revenue": "real", "sales": "real", "count": "integer",
            },
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

    def test_create_alert_sets_created_by(self):
        url = reverse("alert-list")
        payload = {
            "name": "Auto Created By",
            "dataset": self.dataset.id,
            "condition": "above",
            "threshold": 100.0,
            "metric": "amount",
            "aggregation": "sum",
            "check_interval": "daily",
            "notification_channels": ["email"],
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["created_by_name"] == "alertuser"

    def test_update_alert(self):
        alert = DataAlert.objects.create(
            name="Old Name",
            dataset=self.dataset,
            condition="above",
            threshold=100.0,
            metric="amount",
            aggregation="sum",
            check_interval="daily",
            notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-detail", args=[alert.id])
        response = self.client.patch(url, {"name": "New Name"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "New Name"

    def test_delete_alert(self):
        alert = DataAlert.objects.create(
            name="Delete Me",
            dataset=self.dataset,
            condition="above",
            threshold=100.0,
            metric="amount",
            aggregation="sum",
            check_interval="daily",
            notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-detail", args=[alert.id])
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert DataAlert.objects.count() == 0

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

    def test_filter_by_is_active(self):
        DataAlert.objects.create(
            name="Active",
            dataset=self.dataset,
            condition="above", threshold=10.0, metric="x",
            aggregation="count", notification_channels=["email"],
            created_by=self.user, is_active=True,
        )
        DataAlert.objects.create(
            name="Inactive",
            dataset=self.dataset,
            condition="above", threshold=20.0, metric="y",
            aggregation="count", notification_channels=["email"],
            created_by=self.user, is_active=False,
        )
        url = reverse("alert-list") + "?is_active=true"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Active"

    def test_filter_by_condition(self):
        DataAlert.objects.create(
            name="Above Alert",
            dataset=self.dataset, condition="above", threshold=10.0,
            metric="x", aggregation="count", notification_channels=["email"],
            created_by=self.user,
        )
        DataAlert.objects.create(
            name="Below Alert",
            dataset=self.dataset, condition="below", threshold=10.0,
            metric="y", aggregation="count", notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-list") + "?condition=below"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Below Alert"

    def test_search_alerts(self):
        DataAlert.objects.create(
            name="Revenue Alert",
            dataset=self.dataset, condition="above", threshold=1000.0,
            metric="revenue", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        DataAlert.objects.create(
            name="Cost Alert",
            dataset=self.dataset, condition="below", threshold=500.0,
            metric="cost", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-list") + "?search=Revenue"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "Revenue Alert"

    def test_ordering(self):
        DataAlert.objects.create(
            name="A Alert", dataset=self.dataset, condition="above", threshold=1,
            metric="x", aggregation="count", notification_channels=["email"],
            created_by=self.user,
        )
        DataAlert.objects.create(
            name="B Alert", dataset=self.dataset, condition="above", threshold=2,
            metric="y", aggregation="count", notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-list") + "?ordering=name"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["name"] == "A Alert"

    def test_check_now_triggers(self):
        alert = DataAlert.objects.create(
            name="Check Now Test",
            dataset=self.dataset,
            condition="above",
            threshold=0,
            metric="amount",
            aggregation="sum",
            check_interval="daily",
            notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-check-now", args=[alert.id])
        with patch("alerts.views.check_alert") as mock_check:
            mock_check.return_value = AlertHistory.objects.create(
                alert=alert, actual_value=100.0, threshold=0,
                condition="above", message="Triggered",
            )
            response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["triggered"] is True

    def test_check_now_not_triggered(self):
        alert = DataAlert.objects.create(
            name="No Trigger",
            dataset=self.dataset, condition="above", threshold=1000.0,
            metric="amount", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-check-now", args=[alert.id])
        with patch("alerts.views.check_alert") as mock_check:
            mock_check.return_value = None
            response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["triggered"] is False

    def test_check_now_error(self):
        alert = DataAlert.objects.create(
            name="Error Alert",
            dataset=self.dataset, condition="above", threshold=100.0,
            metric="amount", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-check-now", args=[alert.id])
        with patch("alerts.views.check_alert") as mock_check:
            mock_check.side_effect = Exception("DB error")
            response = self.client.post(url)
        assert response.status_code == 500
        assert "error" in response.data

    def test_history_action(self):
        alert = DataAlert.objects.create(
            name="History Test",
            dataset=self.dataset, condition="above", threshold=100.0,
            metric="amount", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        AlertHistory.objects.create(
            alert=alert, actual_value=150.0, threshold=100.0, condition="above",
        )
        url = reverse("alert-history", args=[alert.id])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_history_action_empty(self):
        alert = DataAlert.objects.create(
            name="No History",
            dataset=self.dataset, condition="above", threshold=100.0,
            metric="amount", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        url = reverse("alert-history", args=[alert.id])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0

    def test_stats_24h_triggered(self):
        alert = DataAlert.objects.create(
            name="Stats 24h",
            dataset=self.dataset, condition="above", threshold=10.0,
            metric="x", aggregation="count", notification_channels=["email"],
            created_by=self.user,
        )
        AlertHistory.objects.create(
            alert=alert, actual_value=100.0, threshold=10.0, condition="above",
            triggered_at=timezone.now() - timedelta(hours=2),
        )
        AlertHistory.objects.create(
            alert=alert, actual_value=200.0, threshold=10.0, condition="above",
            triggered_at=timezone.now() - timedelta(hours=48),
        )
        url = reverse("alert-stats")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["triggered_last_24h"] >= 1

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        url = reverse("alert-list")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_permission_denied_create(self):
        staff_no_perm = User.objects.create_user(
            username="staffnoperm", password="pass123", is_staff=True
        )
        self.client.force_authenticate(user=staff_no_perm)
        url = reverse("alert-list")
        payload = {
            "name": "Test Alert",
            "dataset": self.dataset.id,
            "condition": "above",
            "threshold": 100.0,
            "metric": "amount",
            "aggregation": "sum",
            "check_interval": "daily",
            "notification_channels": ["email"],
        }
        response = self.client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class DataAlertServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="serviceuser", password="testpass123"
        )
        self.dataset = Dataset.objects.create(
            name="Service Dataset",
            table_name="service_table",
            columns={"id": "integer", "value": "real", "amount": "real"},
            created_by=self.user,
        )

    def test_evaluate_condition_above_true(self):
        triggered, msg = _evaluate_condition(100.0, 0, "above", 50.0)
        assert triggered is True

    def test_evaluate_condition_above_false(self):
        triggered, msg = _evaluate_condition(30.0, 0, "above", 50.0)
        assert triggered is False

    def test_evaluate_condition_below_true(self):
        triggered, msg = _evaluate_condition(30.0, 0, "below", 50.0)
        assert triggered is True

    def test_evaluate_condition_below_false(self):
        triggered, msg = _evaluate_condition(100.0, 0, "below", 50.0)
        assert triggered is False

    def test_evaluate_condition_equal_true(self):
        triggered, msg = _evaluate_condition(50.0, 0, "equals", 50.0)
        assert triggered is True

    def test_evaluate_condition_equal_false(self):
        triggered, msg = _evaluate_condition(30.0, 0, "equals", 50.0)
        assert triggered is False

    def test_evaluate_condition_change_percent_true(self):
        triggered, msg = _evaluate_condition(75.0, 50.0, "change_percent", 10.0)
        assert triggered is True

    def test_evaluate_condition_change_percent_false(self):
        triggered, msg = _evaluate_condition(55.0, 50.0, "change_percent", 10.0)
        assert triggered is False

    def test_evaluate_condition_change_percent_zero_previous(self):
        triggered, msg = _evaluate_condition(100.0, 0, "change_percent", 10.0)
        assert triggered is False

    def test_evaluate_condition_unknown(self):
        triggered, msg = _evaluate_condition(100.0, 0, "unknown", 10.0)
        assert triggered is False

    def test_check_alert_above_triggered(self):
        alert = DataAlert.objects.create(
            name="Check Above",
            dataset=self.dataset,
            condition="above",
            threshold=50.0,
            metric="value",
            aggregation="sum",
            check_interval="daily",
            notification_channels=["email"],
            created_by=self.user,
        )
        with patch("alerts.services._fetch_aggregate") as mock_fetch:
            mock_fetch.return_value = 100.0
            history = check_alert(alert.id)
        assert history is not None
        assert float(history.actual_value) == 100.0

    def test_check_alert_not_triggered(self):
        alert = DataAlert.objects.create(
            name="No Trigger",
            dataset=self.dataset, condition="above", threshold=1000.0,
            metric="value", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        with patch("alerts.services._fetch_aggregate") as mock_fetch:
            mock_fetch.return_value = 50.0
            result = check_alert(alert.id)
        assert result is None

    def test_check_alert_below_triggered(self):
        alert = DataAlert.objects.create(
            name="Below Check",
            dataset=self.dataset, condition="below", threshold=50.0,
            metric="value", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        with patch("alerts.services._fetch_aggregate") as mock_fetch:
            mock_fetch.return_value = 10.0
            history = check_alert(alert.id)
        assert history is not None
        assert float(history.actual_value) == 10.0

    def test_check_alert_inactive(self):
        alert = DataAlert.objects.create(
            name="Inactive Alert",
            dataset=self.dataset, condition="above", threshold=100.0,
            metric="value", aggregation="sum", notification_channels=["email"],
            created_by=self.user, is_active=False,
        )
        with patch("alerts.services._fetch_aggregate") as mock_fetch:
            result = check_alert(alert.id)
        assert result is None
        mock_fetch.assert_not_called()

    def test_check_alert_does_not_exist(self):
        result = check_alert(99999)
        assert result is None

    def test_check_alert_updates_last_checked(self):
        alert = DataAlert.objects.create(
            name="Last Checked",
            dataset=self.dataset, condition="above", threshold=50.0,
            metric="value", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        with patch("alerts.services._fetch_aggregate") as mock_fetch:
            mock_fetch.return_value = 100.0
            check_alert(alert.id)
        alert.refresh_from_db()
        assert alert.last_checked is not None

    def test_check_alert_updates_last_triggered(self):
        alert = DataAlert.objects.create(
            name="Last Triggered",
            dataset=self.dataset, condition="above", threshold=50.0,
            metric="value", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        with patch("alerts.services._fetch_aggregate") as mock_fetch:
            mock_fetch.return_value = 100.0
            check_alert(alert.id)
        alert.refresh_from_db()
        assert alert.last_triggered is not None

    def test_check_alert_send_email(self):
        alert = DataAlert.objects.create(
            name="Email Test",
            dataset=self.dataset, condition="above", threshold=50.0,
            metric="value", aggregation="sum", check_interval="daily",
            notification_channels=["email"], created_by=self.user,
        )
        user2 = User.objects.create_user(
            username="recipient", email="test@example.com", password="pass"
        )
        alert.recipients.add(user2)

        with (
            patch("alerts.services._fetch_aggregate") as mock_fetch,
            patch("django.core.mail.send_mail") as mock_send,
        ):
            mock_fetch.return_value = 100.0
            history = check_alert(alert.id)
        assert history is not None
        mock_send.assert_called_once()

    def test_check_alert_send_webhook(self):
        alert = DataAlert.objects.create(
            name="Webhook Test",
            dataset=self.dataset, condition="above", threshold=50.0,
            metric="value", aggregation="sum", check_interval="daily",
            notification_channels=["webhook"],
            webhook_url="https://hooks.example.com/alert",
            created_by=self.user,
        )
        with (
            patch("alerts.services._fetch_aggregate") as mock_fetch,
            patch("alerts.services.requests.post") as mock_post,
        ):
            mock_fetch.return_value = 100.0
            mock_post.return_value.status_code = 200
            mock_post.return_value.text = "OK"
            history = check_alert(alert.id)
        assert history is not None
        mock_post.assert_called_once()
        assert history.notification_sent is True

    def test_check_alert_webhook_error(self):
        alert = DataAlert.objects.create(
            name="Webhook Fail",
            dataset=self.dataset, condition="above", threshold=50.0,
            metric="value", aggregation="sum", check_interval="daily",
            notification_channels=["webhook"],
            webhook_url="https://hooks.example.com/fail",
            created_by=self.user,
        )
        with (
            patch("alerts.services._fetch_aggregate") as mock_fetch,
            patch("alerts.services.requests.post") as mock_post,
        ):
            mock_fetch.return_value = 100.0
            mock_post.side_effect = Exception("Connection refused")
            history = check_alert(alert.id)
        assert history is not None
        assert history.notification_sent is False

    def test_check_alert_send_notifications_failure(self):
        alert = DataAlert.objects.create(
            name="Notify Fail",
            dataset=self.dataset, condition="above", threshold=50.0,
            metric="value", aggregation="sum", notification_channels=["email"],
            created_by=self.user,
        )
        user2 = User.objects.create_user(
            username="failrecipient", email="fail@example.com", password="pass"
        )
        alert.recipients.add(user2)

        with (
            patch("alerts.services._fetch_aggregate") as mock_fetch,
            patch("django.core.mail.send_mail") as mock_send,
        ):
            mock_fetch.return_value = 100.0
            mock_send.side_effect = Exception("SMTP error")
            history = check_alert(alert.id)
        assert history is not None
        # notification_sent stays False because exception is caught
        assert history.notification_sent is False
