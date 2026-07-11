import json
from rest_framework import viewsets, status, filters as drf_filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connection
from django.db.models import Count, Sum, Avg, Min, Max
from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from core.base_exception import DmvnException
from .models import Chart, SavedQuery
from .serializers import ChartSerializer, ChartDataSerializer, SavedQuerySerializer


class ChartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Chart model.
    Provides CRUD operations plus a `data` action that computes
    chart data by applying the chart config to the dataset's table.
    """

    queryset = Chart.objects.select_related("dataset", "created_by").all()
    serializer_class = ChartSerializer
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        dataset_id = self.request.query_params.get("dataset_id", None)
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        chart_type = self.request.query_params.get("chart_type", None)
        if chart_type:
            queryset = queryset.filter(chart_type=chart_type)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _build_chart_sql(self, config, table_name):
        """Build a SQL query from chart config for a given table."""
        x_axis = config.get("xAxis") or config.get("x_axis")
        y_axis = config.get("yAxis") or config.get("y_axis")
        group_by = config.get("groupBy") or config.get("group_by")
        aggregate = config.get("aggregate", "none")
        limit = config.get("limit")
        sort_config = config.get("sort")
        filters_config = config.get("filters", [])

        chart_type = config.get("chart_type") or getattr(self, 'chart_type', None)
        is_kpi = chart_type == "kpi"

        if not is_kpi and (not x_axis or not y_axis):
            raise DmvnException(
                "x_axis and y_axis are required in chart config.",
                status_code=400,
                code="bad_request",
            )

        group_cols = []
        if aggregate and aggregate != "none":
            agg_func = {
                "sum": "SUM",
                "avg": "AVG",
                "count": "COUNT",
                "min": "MIN",
                "max": "MAX",
            }.get(aggregate, "SUM")

            if is_kpi:
                # KPI mode: single aggregate value, no grouping
                metric_col = config.get("metric") or y_axis
                select_cols = [f'{agg_func}("{metric_col}") as "{metric_col}"']
                sql = f'SELECT {", ".join(select_cols)} FROM "{table_name}"'
            else:
                select_cols = [f'"{x_axis}"']
                group_cols = [f'"{x_axis}"']

                if group_by:
                    select_cols.append(f'"{group_by}"')
                    group_cols.append(f'"{group_by}"')

                select_cols.append(f'{agg_func}("{y_axis}") as "{y_axis}"')
                sql = f'SELECT {", ".join(select_cols)} FROM "{table_name}"'
        else:
            sql = f'SELECT * FROM "{table_name}"'

        where_clauses = []
        params = []
        for f in filters_config:
            col = f.get("column")
            op = f.get("operator", "eq")
            val = f.get("value")
            if not col:
                continue
            if op == "eq":
                where_clauses.append(f'"{col}" = %s')
                params.append(val)
            elif op == "neq":
                where_clauses.append(f'"{col}" != %s')
                params.append(val)
            elif op == "gt":
                where_clauses.append(f'"{col}" > %s')
                params.append(val)
            elif op == "gte":
                where_clauses.append(f'"{col}" >= %s')
                params.append(val)
            elif op == "lt":
                where_clauses.append(f'"{col}" < %s')
                params.append(val)
            elif op == "lte":
                where_clauses.append(f'"{col}" <= %s')
                params.append(val)
            elif op == "contains":
                where_clauses.append(f'"{col}" LIKE %s')
                params.append(f"%{val}%")
            elif op == "in" and isinstance(val, list):
                placeholders = ", ".join(["%s"] * len(val))
                where_clauses.append(f'"{col}" IN ({placeholders})')
                params.extend(val)

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        if aggregate and aggregate != "none":
            sql += f' GROUP BY {", ".join(group_cols)}'

        if sort_config:
            col = sort_config.get("column", x_axis)
            direction = sort_config.get("direction", "asc")
            sql += f' ORDER BY "{col}" {direction.upper()}'
        elif aggregate and aggregate != "none":
            sql += f' ORDER BY "{y_axis}" DESC'

        if limit:
            sql += f" LIMIT {int(limit)}"

        return sql, params

    def _execute_chart_sql(self, sql, params, chart_type, config):
        """Execute SQL and return serialized chart data."""
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        col_meta = [{"name": col, "type": "string", "label": col} for col in columns]

        serializer = ChartDataSerializer(
            instance={
                "columns": col_meta,
                "rows": rows,
                "chart_type": chart_type,
                "config": config,
            }
        )
        return serializer.data

    @action(detail=True, methods=["get"])
    def data(self, request, pk=None):
        """Compute chart data for a saved chart.
        Accepts optional `global_filters` query param (JSON-encoded array)
        to merge into the chart's config filters.
        """
        chart = self.get_object()
        dataset = chart.dataset
        table_name = dataset.table_name

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

        # Merge global filters into chart config
        config = dict(chart.config)
        global_filters_raw = request.query_params.get("global_filters")
        if global_filters_raw:
            import json
            try:
                global_filters = json.loads(global_filters_raw)
                if isinstance(global_filters, list):
                    existing_filters = config.get("filters", [])
                    if not isinstance(existing_filters, list):
                        existing_filters = []
                    # Merge: global filters override chart filters with same column
                    merged = {f.get("column"): f for f in existing_filters}
                    for gf in global_filters:
                        col = gf.get("column")
                        if col:
                            merged[col] = gf
                    config["filters"] = list(merged.values())
            except (json.JSONDecodeError, TypeError):
                pass

        sql, params = self._build_chart_sql(config, table_name)
        return Response(self._execute_chart_sql(sql, params, chart.chart_type, config))

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        """Export chart data as CSV."""
        chart = self.get_object()
        dataset = chart.dataset
        table_name = dataset.table_name

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

        config = dict(chart.config)
        sql, params = self._build_chart_sql(config, table_name)

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        fmt = request.query_params.get("format", "csv")
        if fmt == "csv":
            import csv
            from django.http import HttpResponse

            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="{chart.name}.csv"'

            writer = csv.writer(response)
            writer.writerow(columns)
            for row in rows:
                writer.writerow(row)
            return response

        return Response({"error": "Unsupported format"}, status=400)

    @action(detail=False, methods=["post"])
    def preview(self, request):
        """Compute chart data without saving a chart (preview mode)."""
        dataset_id = request.data.get("dataset")
        config = request.data.get("config")
        chart_type = request.data.get("chart_type", "bar")

        if not dataset_id or not config:
            raise DmvnException(
                "dataset and config are required.", status_code=400, code="bad_request"
            )

        from datasets.models import Dataset
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            raise DmvnException("Dataset not found.", status_code=404, code="not_found")

        table_name = dataset.table_name
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

        self.chart_type = chart_type
        sql, params = self._build_chart_sql(config, table_name)
        return Response(self._execute_chart_sql(sql, params, chart_type, config))

    @action(detail=True, methods=["get"])
    def drill_down(self, request, pk=None):
        """Drill down into chart data by filtering on a specific column value.
        Query params: column, value, target_chart_id (optional).
        If target_chart_id provided, returns data for that chart filtered by column=value.
        Otherwise returns raw rows from the dataset filtered by column=value.
        """
        chart = self.get_object()
        column = request.query_params.get("column")
        value = request.query_params.get("value")
        if not column or value is None:
            return Response(
                {"error": "column and value query params required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        dataset = chart.dataset
        table_name = dataset.table_name

        target_chart_id = request.query_params.get("target_chart_id")
        if target_chart_id:
            try:
                target = Chart.objects.get(id=target_chart_id)
            except Chart.DoesNotExist:
                return Response(
                    {"error": "Target chart not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            # Inherit axes from source chart if target has none
            source_config = chart.config
            config = dict(target.config)
            config.setdefault("xAxis", source_config.get("xAxis") or source_config.get("x_axis"))
            config.setdefault("yAxis", source_config.get("yAxis") or source_config.get("y_axis"))
            config["chart_type"] = target.chart_type
            # Add drill-down filter
            filters = config.get("filters", [])
            if not isinstance(filters, list):
                filters = []
            filters.append({"column": column, "operator": "eq", "value": value})
            config["filters"] = filters
            sql, params = self._build_chart_sql(config, target.dataset.table_name)
            return Response(
                self._execute_chart_sql(sql, params, target.chart_type, config)
            )

        # No target: return raw rows filtered by column=value
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

        sql = f'SELECT * FROM "{table_name}" WHERE "{column}" = %s'
        params = [value]
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        col_meta = [{"name": col, "type": "string", "label": col} for col in columns]
        return Response({"columns": col_meta, "rows": rows})
