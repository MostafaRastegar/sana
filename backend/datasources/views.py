import logging
from rest_framework import viewsets, status
from rest_framework import filters as drf_filters
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django_filters import rest_framework as filters

from core.base_exception import DmvnException
from core.response import success_response
from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from .models import DataSource, SyncLog, CSVImportJob
from .serializers import (
    DataSourceSerializer, DataSourceListSerializer,
    SyncLogSerializer, CSVImportJobSerializer,
)
from .connectors import test_connection, sync_data
from datasets.serializers import DatasetSerializer

logger = logging.getLogger(__name__)


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
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination
    filterset_class = DataSourceFilter
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name", "status", "last_synced"]
    ordering = ["-created_at"]
    model_permission_mapping = {
        "test": "datasources.view_datasource",
        "sync": "datasources.change_datasource",
        "create_dataset": "datasources.add_dataset",
        "import_csv": "datasources.add_datasource",
        "import_csv_detail": "datasources.add_datasource",
    }

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
            return Response(success_response(None, message))
        raise DmvnException(message, status_code=400, code="connection_failed")

    @action(detail=True, methods=["post"])
    def sync(self, request, pk=None):
        """Trigger immediate sync for this data source."""
        source = self.get_object()
        source.status = "syncing"
        source.save(update_fields=["status"])

        try:
            result = sync_data(source)
        except Exception as exc:
            logger.exception(f"Sync failed for datasource {source.id}")
            raise DmvnException(str(exc), status_code=500, code="sync_failed")

        return Response(success_response(result, "Sync completed"))

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
                raise DmvnException(str(exc), status_code=500, code="sync_failed")

        if not columns:
            raise DmvnException(
                "No data columns found. Sync the datasource first.",
                status_code=400,
                code="no_data",
            )

        try:
            _auto_create_dataset(source, columns)
        except Exception as exc:
            raise DmvnException(str(exc), status_code=500, code="create_failed")

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
            raise DmvnException("file is required", status_code=400, code="missing_file")

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
                raise DmvnException(
                    result.get("error_message", "Sync failed"),
                    status_code=500,
                    code="sync_failed",
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
            if isinstance(e, DmvnException):
                raise
            raise DmvnException(str(e), status_code=500, code="import_error")

        serializer = CSVImportJobSerializer(job)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser, FormParser],
            url_path="import-csv")
    def import_csv(self, request):
        """Non-detail endpoint: POST /datasources/import-csv/ with source_id in body."""
        source_id = request.data.get("source_id")
        if not source_id:
            raise DmvnException("source_id is required", status_code=400, code="missing_source_id")
        try:
            source = DataSource.objects.get(id=source_id)
        except DataSource.DoesNotExist:
            raise DmvnException("DataSource not found", status_code=404, code="not_found")
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
        return Response(success_response({
            "columns": data.get("columns", []),
            "rows": data.get("rows", []),
            "row_count": data.get("row_count", 0),
        }))
