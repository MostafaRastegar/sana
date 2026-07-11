"""Celery tasks for data source syncing."""

from celery import shared_task
import logging

from datetime import timedelta
from django.utils import timezone

from .models import DataSource
from .connectors import sync_data

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_all_due_sources(self) -> int:
    """Check all active datasources and sync those due per their sync_schedule."""
    now = timezone.now()
    count = 0
    for source in DataSource.objects.filter(is_active=True):
        if not source.sync_schedule:
            continue
        # Simple interval parsing — extend for cron later
        interval_secs = _parse_schedule(source.sync_schedule)
        if interval_secs is None:
            continue
        if source.last_synced and (now - source.last_synced).total_seconds() < interval_secs:
            continue
        sync_datasource.delay(source.id)
        count += 1
    return count


def _parse_schedule(schedule: str) -> int | None:
    """Parse schedule string to interval in seconds. Returns None if unparseable."""
    mapping = {
        "hourly": 3600,
        "daily": 86400,
        "weekly": 604800,
    }
    lower = schedule.strip().lower()
    if lower in mapping:
        return mapping[lower]
    # Try integer minutes
    try:
        minutes = int(lower)
        return minutes * 60
    except ValueError:
        pass
    return None


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_datasource(self, source_id: int) -> dict:
    """Async task to sync a data source."""
    try:
        source = DataSource.objects.get(id=source_id)
    except DataSource.DoesNotExist:
        logger.error(f"DataSource {source_id} not found")
        return {"status": "failed", "error": "DataSource not found"}

    source.status = "syncing"
    source.save(update_fields=["status"])

    try:
        result = sync_data(source)
        return result
    except Exception as exc:
        logger.exception(f"Sync task failed for {source.name}")
        raise self.retry(exc=exc)