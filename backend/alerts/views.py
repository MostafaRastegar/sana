import logging

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from core.base_exception import DmvnException
from .models import DataAlert, AlertHistory
from .serializers import DataAlertSerializer, AlertHistorySerializer
from .services import check_alert

logger = logging.getLogger(__name__)


class DataAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DataAlert model.
    Provides CRUD plus `check_now` and `history` actions.
    """

    queryset = DataAlert.objects.select_related(
        "dataset", "created_by"
    ).prefetch_related("recipients").all()
    serializer_class = DataAlertSerializer
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination
    model_permission_mapping = {
        "toggle": "alerts.change_dataalert",
        "check_now": "alerts.view_dataalert",
        "history": "alerts.view_dataalert",
        "stats": "alerts.view_dataalert",
    }
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "last_checked", "last_triggered"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        dataset_id = self.request.query_params.get("dataset_id")
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        condition = self.request.query_params.get("condition")
        if condition:
            queryset = queryset.filter(condition=condition)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def check_now(self, request, pk=None):
        """Immediately evaluate an alert."""
        alert = self.get_object()
        try:
            history = check_alert(alert.id)
            if history:
                serializer = AlertHistorySerializer(history)
                return Response(
                    {"triggered": True, "history": serializer.data}
                )
            return Response(
                {"triggered": False, "message": "Condition not met"}
            )
        except Exception as e:
            logger.exception(f"Error checking alert {alert.id}")
            raise DmvnException(
                str(e), status_code=500, code="check_error"
            )

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """Get alert trigger history."""
        alert = self.get_object()
        histories = AlertHistory.objects.filter(alert=alert).order_by("-triggered_at")
        page = self.paginate_queryset(histories)
        if page is not None:
            serializer = AlertHistorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = AlertHistorySerializer(histories, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Toggle alert active/inactive."""
        alert = self.get_object()
        alert.is_active = not alert.is_active
        alert.save(update_fields=["is_active"])
        serializer = self.get_serializer(alert)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Return alert statistics."""
        total = DataAlert.objects.count()
        active = DataAlert.objects.filter(is_active=True).count()
        triggered_last_24h = AlertHistory.objects.filter(
            triggered_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        return Response({
            "total_alerts": total,
            "active_alerts": active,
            "triggered_last_24h": triggered_last_24h,
        })