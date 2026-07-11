from django.db import models
from django.utils.translation import gettext_lazy as _
from .encryption import encrypt_config, decrypt_config


class DataSource(models.Model):
    """External data source connection configuration."""

    SOURCE_TYPES = [
        ("postgresql", "PostgreSQL"),
        ("mysql", "MySQL"),
        ("sqlite", "SQLite"),
        ("api", "REST API"),
        ("csv", "CSV File"),
    ]

    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    source_type = models.CharField(
        max_length=20, choices=SOURCE_TYPES, verbose_name=_("Source Type")
    )
    connection_config = models.JSONField(
        default=dict, blank=True, verbose_name=_("Connection Config"),
        help_text=_("Host, port, database, credentials etc. Stored encrypted at rest."),
    )
    sync_schedule = models.CharField(
        max_length=100, blank=True, verbose_name=_("Sync Schedule"),
        help_text=_("Cron expression or 'hourly'/'daily'/'weekly'"),
    )
    auto_sync_enabled = models.BooleanField(
        default=False, verbose_name=_("Auto Sync Enabled"),
        help_text=_("Enable automatic data synchronization on schedule"),
    )
    csv_config = models.JSONField(
        default=dict, blank=True, verbose_name=_("CSV Config"),
        help_text=_("CSV-specific settings: delimiter, encoding, has_header, etc."),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))
    last_synced = models.DateTimeField(null=True, blank=True, verbose_name=_("Last Synced"))
    status = models.CharField(
        max_length=20, default="active", verbose_name=_("Status"),
        choices=[
            ("active", _("Active")),
            ("error", _("Error")),
            ("syncing", _("Syncing")),
        ],
    )
    error_message = models.TextField(blank=True, verbose_name=_("Error Message"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        app_label = "datasources"
        verbose_name = _("Data Source")
        verbose_name_plural = _("Data Sources")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.source_type})"

    def save(self, *args, **kwargs):
        # Encrypt connection_config if it's a plain dict (not already an encrypted token)
        if isinstance(self.connection_config, dict) and self.connection_config:
            self.connection_config = encrypt_config(self.connection_config)
        super().save(*args, **kwargs)

    def get_decrypted_config(self) -> dict:
        """Return decrypted connection_config as a dict."""
        if isinstance(self.connection_config, str):
            return decrypt_config(self.connection_config)
        return self.connection_config if isinstance(self.connection_config, dict) else {}


class SyncLog(models.Model):
    """Log of data synchronization runs."""

    source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, related_name="sync_logs",
        verbose_name=_("Source"),
    )
    started_at = models.DateTimeField(verbose_name=_("Started At"))
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Finished At"))
    rows_imported = models.IntegerField(default=0, verbose_name=_("Rows Imported"))
    status = models.CharField(
        max_length=20, verbose_name=_("Status"),
        choices=[("running", _("Running")), ("success", _("Success")), ("failed", _("Failed"))],
    )
    error_message = models.TextField(blank=True, verbose_name=_("Error Message"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        app_label = "datasources"
        verbose_name = _("Sync Log")
        verbose_name_plural = _("Sync Logs")
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.source.name} - {self.status} @ {self.started_at}"


class CSVImportJob(models.Model):
    """Tracks CSV import jobs with error details."""

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("processing", _("Processing")),
        ("completed", _("Completed")),
        ("failed", _("Failed")),
    ]

    source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE, related_name="csv_import_jobs",
        verbose_name=_("Source"),
    )
    file_name = models.CharField(max_length=255, verbose_name=_("File Name"))
    file_path = models.CharField(max_length=512, blank=True, verbose_name=_("File Path"))
    rows_total = models.IntegerField(default=0, verbose_name=_("Total Rows"))
    rows_imported = models.IntegerField(default=0, verbose_name=_("Rows Imported"))
    rows_failed = models.IntegerField(default=0, verbose_name=_("Rows Failed"))
    error_log = models.JSONField(default=list, blank=True, verbose_name=_("Error Log"),
                                  help_text=_("Array of {row, error} objects"))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name=_("Status"),
    )
    started_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Started At"))
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Finished At"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        app_label = "datasources"
        verbose_name = _("CSV Import Job")
        verbose_name_plural = _("CSV Import Jobs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.file_name} - {self.status}"