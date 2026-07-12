from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import connection, DatabaseError
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from core.base_exception import DmvnException
from core.response import success_response
from .models import Dataset
from .serializers import DatasetSerializer, DatasetDataSerializer
from datasources.models import DataSource


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_tables(request):
    """
    List all user-accessible tables in the database.
    Excludes Django internal tables (auth_, django_, sqlite_).
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = []
            for row in cursor.fetchall():
                name = row[0]
                if not name.startswith(("auth_", "django_", "sqlite_")):
                    tables.append(name)
        return Response(success_response({"tables": tables}))
    except DatabaseError as e:
        raise DmvnException(str(e), status_code=400, code="db_error")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def detect_columns(request, table_name):
    """
    Detect columns for a given table in the database.
    Returns column name, type, and a human-readable label.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
                [table_name],
            )
            if not cursor.fetchone():
                raise DmvnException(
                    f"Table '{table_name}' does not exist.",
                    status_code=404,
                    code="table_not_found",
                )

            cursor.execute(f'SELECT * FROM "{table_name}" LIMIT 0')
            columns = [
                {
                    "name": col[0],
                    "type": col[1] if len(col) > 1 else "string",
                    "label": col[0].replace("_", " ").title(),
                }
                for col in cursor.description
            ]
        return Response(success_response({"columns": columns}))
    except DatabaseError as e:
        raise DmvnException(str(e), status_code=400, code="db_error")


@method_decorator(cache_page(60 * 15), name="list")
class DatasetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dataset model.
    Provides CRUD operations plus a `data` action to fetch rows
    from the dataset's backing database table.
    """

    queryset = Dataset.objects.select_related("created_by", "datasource").all()
    serializer_class = DatasetSerializer
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description", "table_name"]
    ordering_fields = ["name", "row_count", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    @action(detail=True, methods=["post"])
    def from_datasource(self, request, pk=None):
        """
        Create a Dataset from a DataSource's synced table.
        POST /api/datasets/{datasource_id}/from_datasource/
        """
        try:
            source = DataSource.objects.get(pk=pk)
        except DataSource.DoesNotExist:
            raise DmvnException(
                "DataSource not found.",
                status_code=404,
                code="not_found",
            )

        from datasources.connectors import _auto_create_dataset, get_data

        data = get_data(source)
        columns = data.get("columns", [])

        if not columns:
            from datasources.connectors import sync_data
            try:
                result = sync_data(source)
                columns = result.get("columns", [])
            except Exception as exc:
                raise DmvnException(
                    f"Sync failed: {exc}",
                    status_code=400,
                    code="sync_failed",
                )

        if not columns:
            raise DmvnException(
                "No data columns found. Sync the datasource first.",
                status_code=400,
                code="no_data",
            )

        try:
            _auto_create_dataset(source, columns)
        except Exception as exc:
            raise DmvnException(
                f"Failed to create dataset: {exc}",
                status_code=400,
                code="create_failed",
            )

        ds = Dataset.objects.filter(datasource=source).first()
        serializer = self.get_serializer(ds)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"])
    def data(self, request, pk=None):
        """
        Return paginated data rows from the dataset's backing table.
        """
        dataset = self.get_object()
        table_name = dataset.table_name

        # Validate table exists
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=%s",
                [table_name],
            )
            if not cursor.fetchone():
                raise DmvnException(
                    f"Table '{table_name}' does not exist.",
                    status_code=404,
                    code="table_not_found",
                )

        # Pagination params
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        offset = (page - 1) * page_size

        # Count total rows
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            total = cursor.fetchone()[0]

        # Fetch rows
        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT * FROM "{table_name}" LIMIT %s OFFSET %s',
                [page_size, offset],
            )
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Build column metadata
        col_meta = [{"name": col, "type": "string", "label": col} for col in columns]

        serializer = DatasetDataSerializer(
            instance={
                "columns": col_meta,
                "rows": rows,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )
        return Response(serializer.data)