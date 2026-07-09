from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from core.base_exception import DmvnException
from .models import Dashboard
from .serializers import DashboardSerializer, DashboardRenderSerializer


class DashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dashboard model.
    Provides CRUD operations plus `layout` and `render` actions.
    """

    queryset = Dashboard.objects.select_related("created_by").all()
    serializer_class = DashboardSerializer
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["put"])
    def layout(self, request, pk=None):
        """
        Update just the layout JSON for a dashboard.
        """
        dashboard = self.get_object()
        new_layout = request.data.get("layout")

        if new_layout is None:
            raise DmvnException(
                "Layout is required.", status_code=400, code="bad_request"
            )

        if not isinstance(new_layout, dict):
            raise DmvnException(
                "Layout must be a JSON object.", status_code=400, code="bad_request"
            )

        dashboard.layout = new_layout
        dashboard.save()

        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def render(self, request, pk=None):
        """
        Return dashboard with resolved chart data for each chart in layout.
        """
        dashboard = self.get_object()
        layout = dashboard.layout or {"charts": []}
        charts_data = []

        chart_entries = layout.get("charts", [])
        if not isinstance(chart_entries, list):
            chart_entries = []

        from charts.models import Chart
        from charts.serializers import ChartSerializer

        for entry in chart_entries:
            chart_id = entry.get("chartId") or entry.get("chart_id")
            if chart_id is None:
                continue
            try:
                chart = Chart.objects.select_related("dataset").get(id=chart_id)
                chart_serializer = ChartSerializer(chart, context={"request": request})
                charts_data.append(
                    {
                        "chart": chart_serializer.data,
                        "position": {
                            "x": entry.get("x", 0),
                            "y": entry.get("y", 0),
                            "w": entry.get("w", 4),
                            "h": entry.get("h", 3),
                        },
                    }
                )
            except Chart.DoesNotExist:
                continue

        serializer = DashboardRenderSerializer(
            instance={
                "id": dashboard.id,
                "name": dashboard.name,
                "description": dashboard.description,
                "layout": layout,
                "charts_data": charts_data,
            }
        )
        return Response(serializer.data)