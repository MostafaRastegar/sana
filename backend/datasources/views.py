from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import permissions as drf_permissions
from django.utils import timezone
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters

from .models import DataSource, SyncLog, CSVImportJob
from .serializers import (
    DataSourceSerializer, DataSourceListSerializer,
    SyncLogSerializer, CSVImportJobSerializer,
)
from .connectors import test_connection, sync_data
from datasets.serializers import DatasetSerializer


class DataSourceFilter(filters.FilterSet):
    source_type = filters.CharFilter(lookup_expr="iexact")
    status = filters.CharFilter(lookup_expr="iexact")
    is_active = filters.BooleanFilter()

    class Meta:
        model = DataSource
        fields = ["source_type", "status", "is_active"]


@method_decorator(cache_page(60 * 15), name="list")
class DataSourceViewSet(viewsets.ModelViewSet):
    queryset = DataSource.objects.all()
    serializer_class = DataSourceSerializer
    filterset_class = DataSourceFilter
    search_fields = ["name"]
    ordering_fields = ["created_at", "name", "status", "last_synced"]

    def perform_create(self, serializer):
        serializer.save()

    def get_serializer_class(self):
        if self.action == "list":
            return DataSourceListSerializer
        return DataSourceSerializer

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None):
        """Test connection to this data source."""
        source = self.get_object()
        success, message = test_connection(source)
        if success:
            return Response({"success": True, "message": message})
        return Response(
            {"success": False, "message": message},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """Trigger immediate sync for this data source."""
        source = self.get_object()
        source.status = "syncing"
        source.save(update_fields=["status"])

        try:
            result = sync_data(source)
        except Exception as exc:
            return Response(
                {"status": "error", "message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(result)

    @action(detail=True, methods=["get"])
    def logs(self, request, pk=None):
        """Get sync logs for this data source."""
        source = self.get_object()
        logs = source.sync_logs.all()[:50]
        serializer = SyncLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def csv_jobs(self, request, pk=None):
        """Get CSV import jobs for this data source."""
        source = self.get_object()
        jobs = source.csv_import_jobs.all()[:50]
        serializer = CSVImportJobSerializer(jobs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def create_dataset(self, request, pk=None):
        """Create a Dataset from this DataSource's synced table."""
        source = self.get_object()
        from .connectors import _auto_create_dataset, get_data

        # Fetch column metadata from the synced table
        data = get_data(source)
        columns = data.get("columns", [])

        if not columns:
            # Try syncing first
            try:
                result = sync_data(source)
                columns = result.get("columns", [])
            except Exception as exc:
                return Response(
                    {"error": {"code": "sync_failed", "message": str(exc), "details": []}},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        if not columns:
            return Response(
                {"error": {"code": "no_data", "message": "No data columns found. Sync the datasource first.", "details": []}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            _auto_create_dataset(source, columns)
        except Exception as exc:
            return Response(
                {"error": {"code": "create_failed", "message": str(exc), "details": []}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Return the created/updated dataset
        from datasets.models import Dataset
        ds = Dataset.objects.filter(datasource=source).first()
        serializer = DatasetSerializer(ds, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def datasets(self, request, pk=None):
        """Get datasets linked to this data source."""
        source = self.get_object()
        datasets = source.datasets.all()
        serializer = DatasetSerializer(datasets, many=True, context={"request": request})
        return Response(serializer.data)

    def _handle_csv_import(self, source, request):
        """Shared logic for CSV file upload and import."""
        csv_file = request.FILES.get("file")

        if not csv_file:
            return Response(
                {"error": {"code": "missing_file", "message": "file is required", "details": []}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import os
        upload_dir = os.path.join(settings.MEDIA_ROOT, "datasource_files")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, csv_file.name)
        with open(file_path, "wb+") as dest:
            for chunk in csv_file.chunks():
                dest.write(chunk)

        source.connection_config = {"file_path": file_path, "file_name": csv_file.name}
        source.status = "ready"
        source.save(update_fields=["connection_config", "status", "updated_at"])

        # Create one CSVImportJob before syncing
        job = CSVImportJob.objects.create(
            source=source,
            file_name=csv_file.name,
            file_path=file_path,
            status="pending",
        )

        try:
            result = sync_data(source)
            if result.get("status") == "failed":
                job.status = "failed"
                job.error_log = result.get("error_message", "Unknown sync error")
                job.finished_at = timezone.now()
                job.save(update_fields=["status", "error_log", "finished_at"])
                return Response(
                    {"error": {"code": "sync_failed", "message": result.get("error_message", "Sync failed"), "details": []}},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            # Update the pending job with results
            job.status = "completed"
            job.rows_total = result.get("rows_imported", 0)
            job.rows_imported = result.get("rows_imported", 0)
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "rows_total", "rows_imported", "finished_at"])
        except Exception as e:
            job.status = "failed"
            job.error_log = str(e)
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error_log", "finished_at"])
            return Response(
                {"error": {"code": "import_error", "message": str(e), "details": []}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        serializer = CSVImportJobSerializer(job)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser, FormParser],
            url_path="import-csv")
    def import_csv(self, request):
        """Non-detail endpoint: POST /datasources/import-csv/ with source_id in body."""
        source_id = request.data.get("source_id")
        if not source_id:
            return Response(
                {"error": {"code": "missing_source_id", "message": "source_id is required", "details": []}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            source = DataSource.objects.get(id=source_id)
        except DataSource.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": "DataSource not found", "details": []}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return self._handle_csv_import(source, request)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser],
            url_path="import-csv")
    def import_csv_detail(self, request, pk=None):
        """Detail endpoint: POST /datasources/{pk}/import-csv/."""
        source = self.get_object()
        return self._handle_csv_import(source, request)

    @action(detail=True, methods=["get"], url_path="records")
    def records(self, request, pk=None):
        """Return columns + rows for a data source."""
        source = self.get_object()
        from .connectors import get_data, sync_data
        data = get_data(source)
        # Auto-sync if no data (CSV wasn't synced, table doesn't exist)
        if source.source_type == "csv" and data.get("row_count", 0) == 0:
            try:
                sync_data(source)
                data = get_data(source)
            except Exception:
                pass
        return Response({
            "columns": data.get("columns", []),
            "rows": data.get("rows", []),
            "row_count": data.get("row_count", 0),
        })