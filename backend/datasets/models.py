from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Dataset(models.Model):
    """Model representing a dataset backed by a database table."""

    name = models.CharField(max_length=100, unique=True, verbose_name=_("Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    table_name = models.CharField(
        max_length=100, verbose_name=_("Table Name"),
        help_text=_("Actual database table name backing this dataset"),
    )
    columns = models.JSONField(
        default=list, verbose_name=_("Columns"),
        help_text=_("List of {name, type, label} column definitions"),
    )
    row_count = models.IntegerField(null=True, blank=True, verbose_name=_("Row Count"))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_datasets",
        verbose_name=_("Created By"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Dataset")
        verbose_name_plural = _("Datasets")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def clean(self):
        """Custom validation."""
        from django.core.exceptions import ValidationError
        if not self.name.strip():
            raise ValidationError(_("Dataset name cannot be empty."))
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)