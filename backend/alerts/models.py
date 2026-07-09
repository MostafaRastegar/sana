from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class DataAlert(models.Model):
    """Model representing a data alert definition."""

    CONDITION_CHOICES = [
        ("above", _("Above")),
        ("below", _("Below")),
        ("equals", _("Equals")),
        ("change_percent", _("Percent Change")),
    ]

    INTERVAL_CHOICES = [
        ("hourly", _("Hourly")),
        ("daily", _("Daily")),
        ("weekly", _("Weekly")),
    ]

    NOTIFICATION_CHANNELS = [
        ("email", _("Email")),
        ("webhook", _("Webhook")),
    ]

    name = models.CharField(max_length=200, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name=_("Dataset"),
    )
    metric = models.CharField(
        max_length=100,
        verbose_name=_("Metric"),
        help_text=_("Column name to aggregate"),
    )
    aggregation = models.CharField(
        max_length=20,
        default="count",
        choices=[
            ("sum", _("Sum")),
            ("avg", _("Average")),
            ("count", _("Count")),
            ("min", _("Minimum")),
            ("max", _("Maximum")),
        ],
        verbose_name=_("Aggregation"),
    )
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        verbose_name=_("Condition"),
    )
    threshold = models.FloatField(verbose_name=_("Threshold"))
    check_interval = models.CharField(
        max_length=20,
        choices=INTERVAL_CHOICES,
        default="daily",
        verbose_name=_("Check Interval"),
    )
    notification_channels = models.JSONField(
        default=list,
        verbose_name=_("Notification Channels"),
        help_text=_("List of channels: 'email', 'webhook'"),
    )
    recipients = models.ManyToManyField(
        User,
        blank=True,
        related_name="data_alerts",
        verbose_name=_("Recipients"),
    )
    webhook_url = models.URLField(
        blank=True,
        verbose_name=_("Webhook URL"),
        help_text=_("URL to POST alert payload when triggered"),
    )
    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Filters"),
        help_text=_("Optional dataset filters applied before aggregation"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_alerts",
        verbose_name=_("Created By"),
    )
    last_checked = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last Checked")
    )
    last_triggered = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last Triggered")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Data Alert")
        verbose_name_plural = _("Data Alerts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_condition_display()} {self.threshold})"

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.name.strip():
            raise ValidationError(_("Alert name cannot be empty."))
        if self.condition == "change_percent" and self.threshold == 0:
            raise ValidationError(
                _("Threshold cannot be 0 for percent change condition.")
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class AlertHistory(models.Model):
    """Log of triggered alert events."""

    alert = models.ForeignKey(
        DataAlert,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name=_("Alert"),
    )
    triggered_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Triggered At")
    )
    actual_value = models.FloatField(verbose_name=_("Actual Value"))
    threshold = models.FloatField(verbose_name=_("Threshold"))
    condition = models.CharField(max_length=20, verbose_name=_("Condition"))
    message = models.TextField(blank=True, verbose_name=_("Message"))
    notification_sent = models.BooleanField(
        default=False, verbose_name=_("Notification Sent")
    )
    notification_response = models.JSONField(
        null=True, blank=True, verbose_name=_("Notification Response")
    )

    class Meta:
        verbose_name = _("Alert History")
        verbose_name_plural = _("Alert Histories")
        ordering = ["-triggered_at"]

    def __str__(self):
        return f"{self.alert.name} @ {self.triggered_at} ({self.actual_value})"