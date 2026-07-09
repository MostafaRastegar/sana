from django.contrib import admin
from .models import Chart, SavedQuery


@admin.register(Chart)
class ChartAdmin(admin.ModelAdmin):
    """Admin configuration for Chart model."""

    list_display = ["name", "chart_type", "dataset", "created_by", "created_at"]
    search_fields = ["name", "description"]
    list_filter = ["chart_type", "created_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(SavedQuery)
class SavedQueryAdmin(admin.ModelAdmin):
    """Admin configuration for SavedQuery model."""

    list_display = ["name", "dataset", "created_by", "created_at"]
    search_fields = ["name", "sql"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at", "updated_at"]