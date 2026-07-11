from django.contrib import admin

from .models import DataSource, SyncLog, CSVImportJob


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "status", "is_active", "last_synced")
    list_filter = ("source_type", "status", "is_active")
    search_fields = ("name",)


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ("source", "status", "started_at", "finished_at", "rows_imported")
    list_filter = ("status",)
    search_fields = ("source__name",)


@admin.register(CSVImportJob)
class CSVImportJobAdmin(admin.ModelAdmin):
    list_display = ("file_name", "source", "status", "rows_total", "rows_imported", "rows_failed", "created_at")
    list_filter = ("status",)
    search_fields = ("file_name", "source__name")
