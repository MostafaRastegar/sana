from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from reports.models import ScheduledReport, ReportHistory


class ScheduledReportAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@test.com"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_report(self):
        resp = self.client.post(
            "/api/reports/",
            {
                "name": "Weekly Summary",
                "description": "Test report",
                "dashboard": None,  # will be ignored/override in perform_create
                "format": "pdf",
                "frequency": "weekly",
                "day_of_week": 0,
                "time": "08:00:00",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, 201)

    def test_list_reports(self):
        ScheduledReport.objects.create(
            name="R1",
            dashboard=None,
            frequency="daily",
            time="08:00",
            created_by=self.user,
        )
        ScheduledReport.objects.create(
            name="R2",
            dashboard=None,
            frequency="weekly",
            day_of_week=1,
            time="09:00",
            created_by=self.user,
        )
        resp = self.client.get("/api/reports/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 2)

    def test_filter_by_is_active(self):
        r = ScheduledReport.objects.create(
            name="R1",
            dashboard=None,
            frequency="daily",
            time="08:00",
            created_by=self.user,
            is_active=False,
        )
        resp = self.client.get("/api/reports/?is_active=false")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_toggle_report(self):
        report = ScheduledReport.objects.create(
            name="Togglable",
            dashboard=None,
            frequency="daily",
            time="08:00",
            created_by=self.user,
            is_active=True,
        )
        resp = self.client.post(f"/api/reports/{report.id}/toggle/")
        self.assertEqual(resp.status_code, 200)
        report.refresh_from_db()
        self.assertFalse(report.is_active)

    def test_trigger_now_no_dashboard(self):
        """trigger_now should gracefully handle report without dashboard."""
        report = ScheduledReport.objects.create(
            name="NoDash",
            dashboard=None,
            frequency="daily",
            time="08:00",
            created_by=self.user,
        )
        resp = self.client.post(f"/api/reports/{report.id}/trigger_now/")
        self.assertEqual(resp.status_code, 200)
        # Should return error status because no dashboard to generate from
        self.assertIn("status", resp.data.get("data", {}))

    def test_history_action(self):
        report = ScheduledReport.objects.create(
            name="H1",
            dashboard=None,
            frequency="daily",
            time="08:00",
            created_by=self.user,
        )
        ReportHistory.objects.create(
            report=report,
            format="pdf",
            status="sent",
            recipients_count=2,
        )
        resp = self.client.get(f"/api/reports/{report.id}/history/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["data"]), 1)


class ReportHistoryTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username="admin", password="admin123"
        )
        self.client.force_authenticate(user=self.user)

    def test_history_str(self):
        report = ScheduledReport.objects.create(
            name="RS1",
            dashboard=None,
            frequency="daily",
            time="08:00",
            created_by=self.user,
        )
        history = ReportHistory.objects.create(
            report=report, format="email_html", status="sent"
        )
        self.assertIn("RS1", str(history))

    def test_history_ordering(self):
        report = ScheduledReport.objects.create(
            name="RO1",
            dashboard=None,
            frequency="daily",
            time="08:00",
            created_by=self.user,
        )
        h1 = ReportHistory.objects.create(report=report, status="sent")
        h2 = ReportHistory.objects.create(report=report, status="sent")
        qs = ReportHistory.objects.all()
        self.assertEqual(qs.first(), h2)  # newest first