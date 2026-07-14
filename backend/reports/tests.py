from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from reports.models import ScheduledReport, ReportHistory
from reports.services import _fetch_chart_data, generate_report, send_report_email, generate_and_send
from dashboards.models import Dashboard
from charts.models import Chart
from datasets.models import Dataset
from unittest.mock import patch, Mock
from django.db import connection


class ScheduledReportAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username="admin", password="admin123", email="admin@test.com"
        )
        self.client.force_authenticate(user=self.user)
        self.dashboard = Dashboard.objects.create(name="TestDash", created_by=self.user)

    def test_create_report(self):
        resp = self.client.post(
            "/api/reports/",
            {
                "name": "Weekly Summary",
                "description": "Test report",
                "dashboard": self.dashboard.id,
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
            name="R1", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        ScheduledReport.objects.create(
            name="R2", dashboard=self.dashboard, frequency="weekly",
            day_of_week=1, time="09:00", created_by=self.user,
        )
        resp = self.client.get("/api/reports/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 2)

    def test_filter_by_is_active(self):
        ScheduledReport.objects.create(
            name="R1", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user, is_active=False,
        )
        resp = self.client.get("/api/reports/?is_active=false")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_retrieve_report(self):
        r = ScheduledReport.objects.create(
            name="R1", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        resp = self.client.get(f"/api/reports/{r.id}/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["name"], "R1")

    def test_partial_update_report(self):
        r = ScheduledReport.objects.create(
            name="Old", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        resp = self.client.patch(f"/api/reports/{r.id}/", {"name": "NewName"}, format="json")
        self.assertEqual(resp.status_code, 200)
        r.refresh_from_db()
        self.assertEqual(r.name, "NewName")

    def test_delete_report(self):
        r = ScheduledReport.objects.create(
            name="Del", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        resp = self.client.delete(f"/api/reports/{r.id}/")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(ScheduledReport.objects.count(), 0)

    def test_filter_by_dashboard_id(self):
        dash2 = Dashboard.objects.create(name="Dash2", created_by=self.user)
        ScheduledReport.objects.create(
            name="R1", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        ScheduledReport.objects.create(
            name="R2", dashboard=dash2, frequency="daily",
            time="09:00", created_by=self.user,
        )
        resp = self.client.get(f"/api/reports/?dashboard_id={self.dashboard.id}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(resp.data["results"][0]["name"], "R1")

    def test_search_by_name(self):
        ScheduledReport.objects.create(
            name="UniqueName", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        resp = self.client.get("/api/reports/?search=Unique")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get("/api/reports/")
        self.assertEqual(resp.status_code, 401)

    def test_trigger_now_not_found(self):
        resp = self.client.post("/api/reports/99999/trigger_now/")
        self.assertEqual(resp.status_code, 404)

    def test_toggle_report(self):
        report = ScheduledReport.objects.create(
            name="Togglable", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user, is_active=True,
        )
        resp = self.client.post(f"/api/reports/{report.id}/toggle/")
        self.assertEqual(resp.status_code, 200)
        report.refresh_from_db()
        self.assertFalse(report.is_active)

    def test_toggle_not_found(self):
        resp = self.client.post("/api/reports/99999/toggle/")
        self.assertEqual(resp.status_code, 404)

    def test_trigger_now(self):
        report = ScheduledReport.objects.create(
            name="WithDash", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        resp = self.client.post(f"/api/reports/{report.id}/trigger_now/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("status", resp.data.get("data", {}))

    @patch("reports.views.generate_report")
    def test_preview(self, mock_gen):
        mock_gen.return_value = {"html": "<h1>Test</h1>"}
        r = ScheduledReport.objects.create(
            name="Preview", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        resp = self.client.get(f"/api/reports/{r.id}/preview/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Test", resp.content)

    @patch("reports.views.generate_report")
    def test_preview_error(self, mock_gen):
        mock_gen.side_effect = ValueError("boom")
        r = ScheduledReport.objects.create(
            name="ErrPrev", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        resp = self.client.get(f"/api/reports/{r.id}/preview/")
        self.assertEqual(resp.status_code, 500)

    @patch("reports.views.generate_report")
    def test_download(self, mock_gen):
        mock_gen.return_value = {"html": "<h1>PDF</h1>"}
        r = ScheduledReport.objects.create(
            name="Down", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        resp = self.client.get(f"/api/reports/{r.id}/download/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")

    def test_history_action(self):
        report = ScheduledReport.objects.create(
            name="H1", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        ReportHistory.objects.create(
            report=report, format="pdf", status="sent", recipients_count=2,
        )
        resp = self.client.get(f"/api/reports/{report.id}/history/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["data"]), 1)


class ReportServicesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="svc", password="p")
        self.dashboard = Dashboard.objects.create(name="DashSvc", created_by=self.user)
        self.dataset = Dataset.objects.create(
            name="SvcDS", table_name="test_svc_data",
            columns=[{"name": "x", "type": "integer", "label": "X"},
                     {"name": "y", "type": "integer", "label": "Y"}],
            created_by=self.user,
        )
        with connection.cursor() as c:
            c.execute("CREATE TABLE IF NOT EXISTS test_svc_data (x INTEGER, y INTEGER)")
            c.execute("INSERT INTO test_svc_data VALUES (1, 10), (2, 20)")
        self.chart = Chart.objects.create(
            name="SvcChart", dataset=self.dataset, chart_type="bar",
            config={"x_axis": "x", "y_axis": "y", "aggregate": "none"},
            created_by=self.user,
        )
        self.dashboard.layout = {"charts": [{"chart_id": self.chart.id}]}
        self.dashboard.save(update_fields=["layout"])
        self.report = ScheduledReport.objects.create(
            name="SvcReport", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )

    def tearDown(self):
        with connection.cursor() as c:
            c.execute("DROP TABLE IF EXISTS test_svc_data")

    def test_fetch_chart_data(self):
        result = _fetch_chart_data(self.chart)
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["rows"]), 2)
        self.assertIn("table_html", result)

    def test_fetch_chart_data_no_table(self):
        Dataset.objects.filter(id=self.dataset.id).update(table_name="")
        self.chart.dataset.refresh_from_db()
        result = _fetch_chart_data(self.chart)
        self.assertIsNotNone(result["error"])

    def test_fetch_chart_data_table_error(self):
        self.chart.dataset.table_name = "nonexistent"
        self.chart.dataset.save()
        result = _fetch_chart_data(self.chart)
        self.assertIsNotNone(result["error"])

    def test_generate_report(self):
        result = generate_report(self.report)
        self.assertIn("html", result)
        self.assertIn("SvcReport", result["html"])

    def test_generate_report_no_charts(self):
        self.dashboard.layout = {"charts": []}
        self.dashboard.save()
        result = generate_report(self.report)
        self.assertIn("html", result)

    def test_generate_report_with_chartId_key(self):
        self.dashboard.layout = {"charts": [{"chartId": self.chart.id}]}
        self.dashboard.save()
        result = generate_report(self.report)
        self.assertIn("html", result)

    @patch("reports.services.send_mail")
    def test_send_report_email(self, mock_send):
        self.report.recipients.add(self.user)
        result = send_report_email(self.report, "<html></html>")
        self.assertTrue(result)
        mock_send.assert_called_once()

    def test_send_report_email_no_recipients(self):
        result = send_report_email(self.report, "<html></html>")
        self.assertFalse(result)

    @patch("reports.services.send_report_email")
    def test_generate_and_send_success(self, mock_send):
        mock_send.return_value = True
        result = generate_and_send(self.report)
        self.assertEqual(result["status"], "sent")
        self.assertEqual(ReportHistory.objects.count(), 1)

    @patch("reports.services.send_report_email")
    def test_generate_and_send_failure(self, mock_send):
        mock_send.side_effect = ValueError("send fail")
        with self.assertRaises(ValueError):
            generate_and_send(self.report)
        self.assertEqual(ReportHistory.objects.count(), 1)


class ReportHistoryTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_superuser(
            username="admin", password="admin123"
        )
        self.client.force_authenticate(user=self.user)
        self.dashboard = Dashboard.objects.create(name="DashRH", created_by=self.user)

    def test_history_str(self):
        report = ScheduledReport.objects.create(
            name="RS1", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        history = ReportHistory.objects.create(
            report=report, format="email_html", status="sent"
        )
        self.assertIn("RS1", str(history))

    def test_history_ordering(self):
        report = ScheduledReport.objects.create(
            name="RO1", dashboard=self.dashboard, frequency="daily",
            time="08:00", created_by=self.user,
        )
        h1 = ReportHistory.objects.create(report=report, status="sent")
        h2 = ReportHistory.objects.create(report=report, status="sent")
        qs = ReportHistory.objects.all()
        self.assertEqual(qs.first(), h2)  # newest first