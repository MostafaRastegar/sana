from rest_framework import status, filters, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import connection, DatabaseError
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from core.utils.pagination import CustomPagination
from core.base_exception import DmvnException
from charts.models import SavedQuery
from charts.serializers import SavedQuerySerializer


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def execute_query(request):
    """
    Execute a raw SQL query against the database.
    Returns paginated results with column metadata.
    """
    sql = request.data.get("sql", "").strip()

    if not sql:
        raise DmvnException(
            "SQL query is required.", status_code=400, code="bad_request"
        )

    # Security: only allow SELECT statements
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT"):
        raise DmvnException(
            "Only SELECT queries are allowed.", status_code=400, code="bad_request"
        )

    # Pagination params
    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 50))
    offset = (page - 1) * page_size

    try:
        # Count query
        count_sql = f"SELECT COUNT(*) FROM ({sql}) AS _count_query"
        with connection.cursor() as cursor:
            cursor.execute(count_sql)
            total = cursor.fetchone()[0]

        # Data query with pagination (wrap in subquery to avoid conflicting LIMIT)
        paginated_sql = f'SELECT * FROM ({sql}) AS _paginated LIMIT %s OFFSET %s'
        with connection.cursor() as cursor:
            cursor.execute(paginated_sql, [page_size, offset])
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    except DatabaseError as e:
        raise DmvnException(
            f"Query execution failed: {str(e)}",
            status_code=400,
            code="query_error",
        )

    col_meta = [{"name": col, "type": "string", "label": col} for col in columns]

    return Response(
        {
            "columns": col_meta,
            "rows": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@method_decorator(cache_page(60 * 15), name="list")
class SavedQueryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SavedQuery model.
    Standard CRUD — consistent with datasets/charts/dashboards APIs.
    """

    serializer_class = SavedQuerySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "sql"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return SavedQuery.objects.filter(
            created_by=self.request.user
        ).select_related("dataset", "created_by")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
