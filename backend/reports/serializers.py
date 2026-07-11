from rest_framework import serializers
from .models import ScheduledReport, ReportHistory


class ReportHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportHistory
        fields = [
            "id",
            "report",
            "sent_at",
            "recipients_count",
            "format",
            "status",
            "error_message",
        ]
        read_only_fields = fields


class ScheduledReportSerializer(serializers.ModelSerializer):
    dashboard_name = serializers.CharField(source="dashboard.name", read_only=True)
    created_by_name = serializers.SerializerMethodField()
    recipients_count = serializers.SerializerMethodField()
    history = ReportHistorySerializer(many=True, read_only=True)

    class Meta:
        model = ScheduledReport
        fields = [
            "id",
            "name",
            "description",
            "dashboard",
            "dashboard_name",
            "format",
            "frequency",
            "day_of_week",
            "day_of_month",
            "time",
            "timezone",
            "recipients",
            "recipients_count",
            "is_active",
            "last_sent",
            "next_run",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
            "history",
        ]
        read_only_fields = ["last_sent", "next_run", "created_by", "created_at", "updated_at"]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def get_recipients_count(self, obj):
        return obj.recipients.count()

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
