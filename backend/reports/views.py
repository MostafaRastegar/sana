import logging

from django.http import HttpResponse
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from core.base_exception import DmvnException
from core.response import success_response
from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from .models import ScheduledReport, ReportHistory
from .serializers import ScheduledReportSerializer, ReportHistorySerializer
from .services import generate_and_send, generate_report

logger = logging.getLogger(__name__)


@method_decorator(cache_page(60 * 15), name="list")
class ScheduledReportViewSet(viewsets.ModelViewSet):
    queryset = ScheduledReport.objects.select_related(
        "dashboard", "created_by"
    ).prefetch_related("recipients").all()
    serializer_class = ScheduledReportSerializer
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination
    model_permission_mapping = {
        "trigger_now": "reports.view_scheduledreport",
        "toggle": "reports.change_scheduledreport",
    }
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "last_sent", "next_run"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        dashboard_id = self.request.query_params.get("dashboard_id")
        if dashboard_id:
            queryset = queryset.filter(dashboard_id=dashboard_id)
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["get"])
    def preview(self, request, pk=None):
        """View report HTML in browser."""
        report = self.get_object()
        try:
            result = generate_report(report)
            html_content = result.get("html", "")
            return HttpResponse(html_content, content_type="text/html; charset=utf-8")
        except Exception as e:
            logger.exception(f"Error previewing report {report.id}")
            raise DmvnException(str(e), status_code=500, code="report_preview_failed")

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Download report as PDF."""
        report = self.get_object()
        try:
            result = generate_report(report)
            html_content = result.get("html", "")
            from weasyprint import HTML
            pdf = HTML(string=html_content).write_pdf()
            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{report.name}.pdf"'
            return response
        except Exception as e:
            logger.exception(f"Error downloading report {report.id}")
            raise DmvnException(str(e), status_code=500, code="report_download_failed")

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """Get report generation history."""
        report = self.get_object()
        history_qs = report.history.all()[:50]
        serializer = ReportHistorySerializer(history_qs, many=True)
        return Response(success_response(serializer.data))

    @action(detail=True, methods=["post"])
    def trigger_now(self, request, pk=None):
        """Immediately generate and send a report."""
        report = self.get_object()
        try:
            result = generate_and_send(report)
            return Response(success_response(result, "Report triggered"))
        except Exception as e:
            logger.exception(f"Error triggering report {report.id}")
            raise DmvnException(str(e), status_code=500, code="report_trigger_failed")

    @action(detail=True, methods=["post"])
    def toggle(self, request, pk=None):
        """Toggle report active/inactive."""
        report = self.get_object()
        report.is_active = not report.is_active
        report.save(update_fields=["is_active"])
        serializer = self.get_serializer(report)
        return Response(serializer.data)
