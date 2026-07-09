from django.contrib import admin
from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin configuration for Dataset model."""

    list_display = ["name", "table_name", "row_count", "created_by", "created_at"]
    search_fields = ["name", "description", "table_name"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at", "updated_at"]