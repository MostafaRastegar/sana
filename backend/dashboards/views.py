from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Q
from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from core.base_exception import DmvnException
from core.response import success_response
from .models import Dashboard, DashboardPermission, DashboardTemplate
from .serializers import (
    DashboardSerializer,
    DashboardRenderSerializer,
    DashboardPermissionSerializer,
    DashboardTemplateSerializer,
    UserSearchSerializer,
)

User = get_user_model()


class DashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dashboard model.
    Provides CRUD operations plus `layout`, `filters`, `render`, and sharing actions.
    """

    queryset = Dashboard.objects.select_related("created_by").all()
    serializer_class = DashboardSerializer
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == "permissions":
            return [IsAuthenticated()]
        return super().get_permissions()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Owner sees all their dashboards. Others see: public dashboards + shared with them.
        if not user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        elif not user.is_staff:
            shared_ids = DashboardPermission.objects.filter(
                user=user
            ).values_list("dashboard_id", flat=True)
            queryset = queryset.filter(
                Q(created_by=user) | Q(is_public=True) | Q(id__in=shared_ids)
            )

        name = self.request.query_params.get("name", None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Only owner or admin can update."""
        dashboard = self.get_object()
        user = self.request.user
        if dashboard.created_by != user and not self._has_permission(dashboard, user, "edit"):
            raise DmvnException(
                "You do not have permission to edit this dashboard.",
                status_code=403, code="permission_denied",
            )
        serializer.save()

    def perform_destroy(self, serializer):
        """Only owner or admin can delete."""
        dashboard = self.get_object()
        user = self.request.user
        if dashboard.created_by != user and not self._has_permission(dashboard, user, "admin"):
            raise DmvnException(
                "You do not have permission to delete this dashboard.",
                status_code=403, code="permission_denied",
            )
        serializer.delete()

    def _has_permission(self, dashboard, user, minimum):
        perm = DashboardPermission.objects.filter(
            dashboard=dashboard, user=user
        ).first()
        if not perm:
            return False
        hierarchy = {"view": 0, "edit": 1, "admin": 2}
        return hierarchy.get(perm.permission, -1) >= hierarchy.get(minimum, 0)

    @action(detail=True, methods=["put"])
    def layout(self, request, pk=None):
        """Update just the layout JSON for a dashboard."""
        dashboard = self.get_object()
        user = request.user
        if dashboard.created_by != user and not self._has_permission(dashboard, user, "edit"):
            raise DmvnException(
                "You do not have permission to edit this dashboard.",
                status_code=403, code="permission_denied",
            )
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

    @action(detail=True, methods=["put"])
    def filters(self, request, pk=None):
        """Update just the global filters JSON for a dashboard."""
        dashboard = self.get_object()
        user = request.user
        if dashboard.created_by != user and not self._has_permission(dashboard, user, "edit"):
            raise DmvnException(
                "You do not have permission to edit this dashboard.",
                status_code=403, code="permission_denied",
            )
        new_filters = request.data.get("filters")

        if new_filters is None:
            raise DmvnException(
                "Filters are required.", status_code=400, code="bad_request"
            )

        if not isinstance(new_filters, list):
            raise DmvnException(
                "Filters must be a JSON array.", status_code=400, code="bad_request"
            )

        dashboard.filters = new_filters
        dashboard.save()

        serializer = self.get_serializer(dashboard)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def render(self, request, pk=None):
        """
        Return dashboard with resolved chart data for each chart in layout.
        Accepts optional `global_filters` query param (JSON-encoded array)
        to apply to all charts.
        """
        dashboard = self.get_object()
        user = request.user
        if dashboard.created_by != user and not dashboard.is_public and not self._has_permission(dashboard, user, "view"):
            raise DmvnException(
                "You do not have permission to view this dashboard.",
                status_code=403, code="permission_denied",
            )
        layout = dashboard.layout or {"charts": []}
        charts_data = []

        chart_entries = layout.get("charts", [])
        if not isinstance(chart_entries, list):
            chart_entries = []

        # Parse global filters from query param (passed by frontend)
        global_filters_raw = request.query_params.get("global_filters")
        global_filters = []
        if global_filters_raw:
            import json
            try:
                global_filters = json.loads(global_filters_raw)
            except (json.JSONDecodeError, TypeError):
                pass

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
                "filters": dashboard.filters,
            }
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post", "delete"], url_path="permissions")
    def permissions(self, request, pk=None):
        """Manage dashboard permissions."""
        dashboard = self.get_object()
        user = request.user

        if dashboard.created_by != user and not self._has_permission(dashboard, user, "admin"):
            raise DmvnException(
                "Only the owner or an admin can manage permissions.",
                status_code=403, code="permission_denied",
            )

        if request.method == "GET":
            perms = DashboardPermission.objects.filter(dashboard=dashboard)
            serializer = DashboardPermissionSerializer(perms, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            serializer = DashboardPermissionSerializer(
                data=request.data, context={"request": request}
            )
            if not serializer.is_valid():
                raise DmvnException(
                    "Validation error.", status_code=400, code="bad_request", details=serializer.errors
                )
            serializer.save(dashboard=dashboard)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            perm_id = request.data.get("id") or request.query_params.get("id")
            if not perm_id:
                raise DmvnException(
                    "Permission id is required.", status_code=400, code="bad_request"
                )
            try:
                perm = DashboardPermission.objects.get(id=perm_id, dashboard=dashboard)
                perm.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except DashboardPermission.DoesNotExist:
                raise DmvnException(
                    "Permission not found.", status_code=404, code="not_found"
                )


class DashboardTemplateViewSet(viewsets.ModelViewSet):
    """CRUD for dashboard templates."""

    queryset = DashboardTemplate.objects.select_related("created_by").all()
    serializer_class = DashboardTemplateSerializer
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "category", "created_at"]
    ordering = ["category", "name"]

    def get_queryset(self):
        qs = super().get_queryset()
        cat = self.request.query_params.get("category")
        if cat:
            qs = qs.filter(category=cat)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def instantiate(self, request, pk=None):
        """Create a new dashboard from this template."""
        template = self.get_object()
        db = Dashboard.objects.create(
            name=request.data.get("name", template.name),
            description=template.description,
            layout=template.layout,
            created_by=request.user,
        )
        serializer = DashboardSerializer(db, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserSearchView(viewsets.GenericViewSet):
    """Search users for sharing dialogs."""

    queryset = User.objects.all()
    serializer_class = UserSearchSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def list(self, request):
        query = request.query_params.get("q", "")
        if len(query) < 2:
            return Response(success_response([]))
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id)[:20]
        serializer = self.get_serializer(users, many=True)
        return Response(success_response(serializer.data))
