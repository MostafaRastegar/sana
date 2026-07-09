from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Dashboard(models.Model):
    """Model representing a dashboard containing charts."""

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    layout = models.JSONField(
        null=True, blank=True, verbose_name=_("Layout"),
        help_text=_("Dashboard layout: {charts: [{chart_id, x, y, w, h}]}"),
    )
    filters = models.JSONField(
        default=list, blank=True, verbose_name=_("Filters"),
        help_text=_("Global filter definitions: [{id, name, type, column, dataset, defaultValue, options}]"),
    )
    is_public = models.BooleanField(default=False, verbose_name=_("Is Public"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_dashboards",
        verbose_name=_("Created By"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Dashboard")
        verbose_name_plural = _("Dashboards")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.name.strip():
            raise ValidationError(_("Dashboard name cannot be empty."))
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DashboardPermission(models.Model):
    """Model representing user permissions on a dashboard."""

    PERMISSION_CHOICES = [
        ("view", _("View")),
        ("edit", _("Edit")),
        ("admin", _("Admin")),
    ]

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name="permissions",
        verbose_name=_("Dashboard"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="dashboard_permissions",
        verbose_name=_("User"),
    )
    permission = models.CharField(
        max_length=10,
        choices=PERMISSION_CHOICES,
        default="view",
        verbose_name=_("Permission"),
    )
    shared_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shared_dashboards",
        verbose_name=_("Shared By"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Dashboard Permission")
        verbose_name_plural = _("Dashboard Permissions")
        unique_together = ["dashboard", "user"]

    def __str__(self):
        return f"{self.user.username} - {self.dashboard.name} ({self.permission})"
