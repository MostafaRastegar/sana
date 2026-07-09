from rest_framework import serializers
from .models import Dashboard


class DashboardSerializer(serializers.ModelSerializer):
    """Serializer for Dashboard model."""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    chart_count = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            "id",
            "name",
            "description",
            "layout",
            "chart_count",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_chart_count(self, obj):
        """Get number of charts in this dashboard."""
        if obj.layout and isinstance(obj.layout, dict):
            charts = obj.layout.get("charts", [])
            return len(charts) if isinstance(charts, list) else 0
        return 0

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Dashboard name must be at least 2 characters long."
            )
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class DashboardRenderSerializer(serializers.Serializer):
    """Serializer for a fully rendered dashboard with chart data."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    layout = serializers.DictField(allow_null=True)
    charts_data = serializers.ListField(child=serializers.DictField())