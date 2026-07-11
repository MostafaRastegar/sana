import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import ScheduledReport
from .services import generate_and_send

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_and_send_report_task(self, report_id):
    """Celery task to generate and send a single report."""
    try:
        report = ScheduledReport.objects.get(id=report_id)
        generate_and_send(report)
        _update_next_run(report)
        return f"Report {report_id} sent."
    except ScheduledReport.DoesNotExist:
        logger.error(f"Report {report_id} not found.")
        raise
    except Exception as exc:
        logger.exception(f"Failed to generate report {report_id}")
        raise self.retry(exc=exc)


@shared_task
def check_scheduled_reports():
    """Celery beat task: find reports due and dispatch tasks."""
    now = timezone.now()
    reports = ScheduledReport.objects.filter(is_active=True)
    for report in reports:
        if report.next_run and report.next_run <= now:
            generate_and_send_report_task.delay(report.id)
            _update_next_run(report)


def _update_next_run(report):
    """Calculate and save next run time based on frequency."""
    ref = report.last_sent or timezone.now()
    if report.frequency == "daily":
        next_run = ref + timedelta(days=1)
    elif report.frequency == "weekly":
        next_run = ref + timedelta(weeks=1)
    elif report.frequency == "monthly":
        next_run = ref + timedelta(days=30)
    else:
        next_run = ref + timedelta(days=1)
    report.next_run = next_run
    report.save(update_fields=["next_run"])