from django.contrib import admin
from .models import Dashboard


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    """Admin configuration for Dashboard model."""

    list_display = ["name", "created_by", "created_at"]
    search_fields = ["name", "description"]
    list_filter = ["created_at"]
    readonly_fields = ["created_at", "updated_at"]