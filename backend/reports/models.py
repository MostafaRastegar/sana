from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ReportHistory(models.Model):
    """Tracks each report generation event."""

    STATUS_CHOICES = [
        ("sent", _("Sent")),
        ("failed", _("Failed")),
    ]

    report = models.ForeignKey(
        "ScheduledReport",
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name=_("Report"),
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Sent At"))
    recipients_count = models.IntegerField(default=0, verbose_name=_("Recipients"))
    format = models.CharField(
        max_length=20, default="email_html", verbose_name=_("Format")
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="sent", verbose_name=_("Status")
    )
    error_message = models.TextField(blank=True, verbose_name=_("Error"))
    rendered_html = models.TextField(
        blank=True, verbose_name=_("Rendered HTML")
    )
    pdf_file = models.FileField(
        upload_to="reports/",
        null=True, blank=True,
        verbose_name=_("PDF File"),
    )

    class Meta:
        verbose_name = _("Report History")
        verbose_name_plural = _("Report History")
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.report.name} @ {self.sent_at.isoformat()}"


class ScheduledReport(models.Model):
    """Model representing a scheduled report configuration."""

    FORMAT_CHOICES = [
        ("pdf", _("PDF")),
        ("email_html", _("HTML Email")),
    ]

    FREQUENCY_CHOICES = [
        ("daily", _("Daily")),
        ("weekly", _("Weekly")),
        ("monthly", _("Monthly")),
    ]

    name = models.CharField(max_length=200, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    dashboard = models.ForeignKey(
        "dashboards.Dashboard",
        on_delete=models.CASCADE,
        related_name="scheduled_reports",
        verbose_name=_("Dashboard"),
    )
    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES,
        default="pdf",
        verbose_name=_("Format"),
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        verbose_name=_("Frequency"),
    )
    day_of_week = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Day of Week"),
        help_text=_("0=Monday, 6=Sunday (for weekly)"),
    )
    day_of_month = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Day of Month"),
        help_text=_("1-31 (for monthly)"),
    )
    time = models.TimeField(verbose_name=_("Time"))
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        verbose_name=_("Timezone"),
    )
    recipients = models.ManyToManyField(
        User,
        blank=True,
        related_name="scheduled_reports",
        verbose_name=_("Recipients"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    last_sent = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last Sent")
    )
    next_run = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Next Run")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_reports",
        verbose_name=_("Created By"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Scheduled Report")
        verbose_name_plural = _("Scheduled Reports")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.name.strip():
            raise ValidationError(_("Report name cannot be empty."))
        if self.frequency == "weekly" and self.day_of_week is None:
            raise ValidationError(_("Day of week is required for weekly frequency."))
        if self.frequency == "monthly" and self.day_of_month is None:
            raise ValidationError(_("Day of month is required for monthly frequency."))
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)