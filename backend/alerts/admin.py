from django.contrib import admin
from .models import DataAlert, AlertHistory


@admin.register(DataAlert)
class DataAlertAdmin(admin.ModelAdmin):
    list_display = [
        "name", "dataset", "condition", "threshold",
        "check_interval", "is_active", "last_checked", "last_triggered",
    ]
    list_filter = ["is_active", "condition", "check_interval", "dataset"]
    search_fields = ["name", "description"]
    filter_horizontal = ["recipients"]
    readonly_fields = ["last_checked", "last_triggered", "created_at", "updated_at"]


@admin.register(AlertHistory)
class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = ["alert", "triggered_at", "actual_value", "threshold", "notification_sent"]
    list_filter = ["notification_sent", "triggered_at"]
    search_fields = ["alert__name", "message"]
    readonly_fields = ["triggered_at"]