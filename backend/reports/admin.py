from django.contrib import admin
from .models import ScheduledReport, ReportHistory


class ReportHistoryInline(admin.TabularInline):
    model = ReportHistory
    readonly_fields = ["sent_at", "recipients_count", "format", "status", "error_message"]
    extra = 0
    can_delete = False
    max_num = 20


@admin.register(ScheduledReport)
class ScheduledReportAdmin(admin.ModelAdmin):
    list_display = ["name", "dashboard", "format", "frequency", "is_active", "last_sent"]
    list_filter = ["format", "frequency", "is_active"]
    search_fields = ["name"]
    inlines = [ReportHistoryInline]


@admin.register(ReportHistory)
class ReportHistoryAdmin(admin.ModelAdmin):
    list_display = ["report", "sent_at", "status", "format", "recipients_count"]
    list_filter = ["status", "format"]
    readonly_fields = ["sent_at", "rendered_html"]