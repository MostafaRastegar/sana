import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal

import requests
from django.db import connection
from django.utils import timezone

from .models import DataAlert, AlertHistory

logger = logging.getLogger(__name__)


def _build_aggregate_sql(dataset_table, metric, aggregation, filters=None):
    """Build SQL to compute a single aggregate value from a dataset table."""
    agg_func = {
        "sum": "SUM",
        "avg": "AVG",
        "count": "COUNT",
        "min": "MIN",
        "max": "MAX",
    }.get(aggregation, "COUNT")

    select_col = f'{agg_func}("{metric}") AS "value"'
    sql = f'SELECT {select_col} FROM "{dataset_table}"'

    where_clauses = []
    params = []
    f = filters or {}
    col = f.get("column")
    op = f.get("operator", "eq")
    val = f.get("value")
    if col and val is not None:
        if op == "eq":
            where_clauses.append(f'"{col}" = %s')
            params.append(val)
        elif op == "neq":
            where_clauses.append(f'"{col}" != %s')
            params.append(val)
        elif op == "gt":
            where_clauses.append(f'"{col}" > %s')
            params.append(val)
        elif op == "gte":
            where_clauses.append(f'"{col}" >= %s')
            params.append(val)
        elif op == "lt":
            where_clauses.append(f'"{col}" < %s')
            params.append(val)
        elif op == "lte":
            where_clauses.append(f'"{col}" <= %s')
            params.append(val)

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    return sql, params


def _fetch_aggregate(dataset_table, metric, aggregation, filters=None):
    """Execute aggregate SQL and return the numeric value."""
    sql, params = _build_aggregate_sql(dataset_table, metric, aggregation, filters)
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        row = cursor.fetchone()
    if row is None or row[0] is None:
        return 0.0
    val = row[0]
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


def _evaluate_condition(current_value, previous_value, condition, threshold):
    """Evaluate if an alert condition is met."""
    if condition == "above":
        return current_value > threshold, (
            f"Value {current_value} is above threshold {threshold}"
        )
    elif condition == "below":
        return current_value < threshold, (
            f"Value {current_value} is below threshold {threshold}"
        )
    elif condition == "equals":
        return current_value == threshold, (
            f"Value {current_value} equals threshold {threshold}"
        )
    elif condition == "change_percent":
        if previous_value == 0:
            return False, "Previous value is 0, cannot compute percent change"
        change_pct = ((current_value - previous_value) / previous_value) * 100
        return abs(change_pct) > threshold, (
            f"Percent change {change_pct:.2f}% exceeds threshold {threshold}%"
        )
    return False, "Unknown condition"


def _get_previous_value(alert):
    """Fetch the previous period value for change_percent comparison."""
    dataset = alert.dataset
    table_name = dataset.table_name

    check_interval_map = {
        "hourly": timedelta(hours=1),
        "daily": timedelta(days=1),
        "weekly": timedelta(weeks=1),
    }
    delta = check_interval_map.get(alert.check_interval, timedelta(days=1))

    # Get the last history record to determine the previous period
    last_history = (
        AlertHistory.objects.filter(alert=alert)
        .order_by("-triggered_at")
        .first()
    )
    if not last_history:
        return 0.0

    # Use the actual_value from the most recent history entry
    return last_history.actual_value


def check_alert(alert_id):
    """Evaluate a single alert condition against current data."""
    try:
        alert = DataAlert.objects.select_related("dataset").get(id=alert_id)
    except DataAlert.DoesNotExist:
        logger.error(f"Alert {alert_id} not found")
        return

    if not alert.is_active:
        return

    dataset = alert.dataset
    table_name = dataset.table_name

    # Fetch current aggregate value
    current_value = _fetch_aggregate(
        table_name, alert.metric, alert.aggregation, alert.filters or {}
    )

    # Fetch previous value for comparison (used by change_percent)
    previous_value = _get_previous_value(alert)

    # Evaluate condition
    triggered, message = _evaluate_condition(
        current_value, previous_value, alert.condition, alert.threshold
    )

    # Record the check
    alert.last_checked = timezone.now()
    alert.save(update_fields=["last_checked"])

    if not triggered:
        return

    # Create history entry
    history = AlertHistory.objects.create(
        alert=alert,
        actual_value=current_value,
        threshold=alert.threshold,
        condition=alert.condition,
        message=message,
    )

    alert.last_triggered = timezone.now()
    alert.save(update_fields=["last_triggered"])

    # Send notifications
    _send_notifications(alert, history)

    return history


def _send_notifications(alert, history):
    """Dispatch notifications via configured channels."""
    channels = alert.notification_channels or []

    if "email" in channels:
        _send_email_notification(alert, history)

    if "webhook" in channels and alert.webhook_url:
        _send_webhook_notification(alert, history)


def _send_email_notification(alert, history):
    """Send email notification to alert recipients."""
    from django.core.mail import send_mail

    recipients = alert.recipients.values_list("email", flat=True)
    valid_emails = [e for e in recipients if e]

    if not valid_emails:
        logger.warning(f"No valid email recipients for alert {alert.id}")
        return

    subject = f"[Sana Alert] {alert.name} - Triggered"
    message = (
        f"Alert: {alert.name}\n"
        f"Dataset: {alert.dataset.name}\n"
        f"Metric: {alert.metric} ({alert.aggregation})\n"
        f"Condition: {alert.condition} {alert.threshold}\n"
        f"Actual Value: {history.actual_value}\n"
        f"Message: {history.message}\n"
        f"Triggered at: {history.triggered_at}\n"
    )

    try:
        send_mail(subject, message, None, valid_emails, fail_silently=False)
        history.notification_sent = True
        history.save(update_fields=["notification_sent"])
    except Exception as e:
        logger.error(f"Failed to send email for alert {alert.id}: {e}")


def _send_webhook_notification(alert, history):
    """Send webhook POST with alert payload."""
    payload = {
        "alert_id": alert.id,
        "alert_name": alert.name,
        "dataset": alert.dataset.name,
        "metric": alert.metric,
        "aggregation": alert.aggregation,
        "condition": alert.condition,
        "threshold": alert.threshold,
        "actual_value": history.actual_value,
        "message": history.message,
        "triggered_at": history.triggered_at.isoformat(),
    }

    try:
        resp = requests.post(
            alert.webhook_url,
            json=payload,
            timeout=10,
        )
        history.notification_sent = True
        history.notification_response = {
            "status_code": resp.status_code,
            "body": resp.text[:1000],
        }
        history.save(update_fields=["notification_sent", "notification_response"])
    except Exception as e:
        logger.error(f"Webhook failed for alert {alert.id}: {e}")
        history.notification_response = {"error": str(e)}
        history.save(update_fields=["notification_response"])