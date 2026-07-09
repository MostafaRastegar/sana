from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Chart(models.Model):
    """Model representing a chart configuration."""

    CHART_TYPES = [
        ("bar", _("Bar")),
        ("line", _("Line")),
        ("pie", _("Pie")),
        ("scatter", _("Scatter")),
        ("area", _("Area")),
        ("heatmap", _("Heatmap")),
    ]

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.CASCADE,
        related_name="charts",
        verbose_name=_("Dataset"),
    )
    chart_type = models.CharField(
        max_length=50, choices=CHART_TYPES, verbose_name=_("Chart Type")
    )
    config = models.JSONField(
        default=dict, verbose_name=_("Config"),
        help_text=_("Chart configuration: x_axis, y_axis, group_by, filters, etc."),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_charts",
        verbose_name=_("Created By"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Chart")
        verbose_name_plural = _("Charts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_chart_type_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.name.strip():
            raise ValidationError(_("Chart name cannot be empty."))
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class SavedQuery(models.Model):
    """Model representing a saved SQL query."""

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    sql = models.TextField(verbose_name=_("SQL Query"))
    dataset = models.ForeignKey(
        "datasets.Dataset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="saved_queries",
        verbose_name=_("Dataset"),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="saved_queries",
        verbose_name=_("Created By"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Saved Query")
        verbose_name_plural = _("Saved Queries")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name