from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from reports.tasks import _update_next_run
from reports.models import ScheduledReport
from dashboards.models import Dashboard


class UpdateNextRunTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("t", "t@t.com", "p")
        self.d = Dashboard.objects.create(name="d", created_by=self.user)

    def _report(self, freq):
        kwargs = {"name": freq, "dashboard": self.d, "frequency": freq, "time": "08:00", "created_by": self.user}
        if freq == "weekly":
            kwargs["day_of_week"] = 0
        elif freq == "monthly":
            kwargs["day_of_month"] = 1
        return ScheduledReport.objects.create(**kwargs)

    def test_daily(self):
        r = self._report("daily")
        _update_next_run(r)
        r.refresh_from_db()
        self.assertIsNotNone(r.next_run)

    def test_weekly(self):
        r = self._report("weekly")
        _update_next_run(r)
        r.refresh_from_db()
        self.assertIsNotNone(r.next_run)

    def test_monthly(self):
        r = self._report("monthly")
        _update_next_run(r)
        r.refresh_from_db()
        self.assertIsNotNone(r.next_run)

    def test_uses_last_sent_if_available(self):
        r = self._report("daily")
        r.last_sent = timezone.now() - timezone.timedelta(days=2)
        r.save(update_fields=["last_sent"])
        _update_next_run(r)
        r.refresh_from_db()
        self.assertIsNotNone(r.next_run)


class CheckScheduledReportsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("t2", "t2@t.com", "p")
        self.d = Dashboard.objects.create(name="d2", created_by=self.user)

    @patch("reports.tasks.generate_and_send_report_task.delay")
    def test_check_scheduled_reports_due(self, mock_delay):
        from reports.tasks import check_scheduled_reports
        r = ScheduledReport.objects.create(
            name="Due", dashboard=self.d, frequency="daily",
            time="08:00", created_by=self.user, is_active=True,
            next_run=timezone.now() - timezone.timedelta(minutes=5),
        )
        check_scheduled_reports()
        mock_delay.assert_called_once_with(r.id)

    @patch("reports.tasks.generate_and_send_report_task.delay")
    def test_check_scheduled_reports_no_due(self, mock_delay):
        from reports.tasks import check_scheduled_reports
        ScheduledReport.objects.create(
            name="Future", dashboard=self.d, frequency="daily",
            time="08:00", created_by=self.user, is_active=True,
            next_run=timezone.now() + timezone.timedelta(days=1),
        )
        check_scheduled_reports()
        mock_delay.assert_not_called()

    @patch("reports.tasks.generate_and_send_report_task.delay")
    def test_check_scheduled_reports_inactive(self, mock_delay):
        from reports.tasks import check_scheduled_reports
        ScheduledReport.objects.create(
            name="Inactive", dashboard=self.d, frequency="daily",
            time="08:00", created_by=self.user, is_active=False,
            next_run=timezone.now() - timezone.timedelta(minutes=5),
        )
        check_scheduled_reports()
        mock_delay.assert_not_called()