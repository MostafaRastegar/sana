import logging

from celery import shared_task
from django.apps import apps

from .services import check_alert

logger = logging.getLogger(__name__)


@shared_task(name="check_single_alert")
def check_single_alert(alert_id):
    """Celery task to check a single alert."""
    logger.info(f"Checking alert {alert_id}")
    check_alert(alert_id)


@shared_task(name="check_all_due_alerts")
def check_all_due_alerts():
    """Celery periodic task: check all active alerts due for evaluation."""
    from django.utils import timezone
    from datetime import timedelta

    DataAlert = apps.get_model("alerts", "DataAlert")

    now = timezone.now()
    interval_map = {
        "hourly": timedelta(hours=1),
        "daily": timedelta(days=1),
        "weekly": timedelta(weeks=1),
    }

    active_alerts = DataAlert.objects.filter(is_active=True).select_related("dataset")

    checked = 0
    for alert in active_alerts:
        interval = interval_map.get(alert.check_interval, timedelta(days=1))
        if alert.last_checked is None or (
            now - alert.last_checked
        ) >= interval:
            check_single_alert.delay(alert.id)
            checked += 1

    logger.info(f"Dispatched {checked} alert checks")


@shared_task(name="check_alert_by_id")
def check_alert_by_id(alert_id):
    """Celery task to evaluate a specific alert immediately."""
    check_alert(alert_id)