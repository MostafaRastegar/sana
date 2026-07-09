from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Dashboard, DashboardPermission

User = get_user_model()


class DashboardSerializer(serializers.ModelSerializer):
    """Serializer for Dashboard model."""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    chart_count = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    user_permission = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            "id",
            "name",
            "description",
            "layout",
            "filters",
            "is_public",
            "chart_count",
            "is_owner",
            "user_permission",
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

    def get_is_owner(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.created_by == request.user
        return False

    def get_user_permission(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if obj.created_by == request.user:
            return "admin"
        perm = DashboardPermission.objects.filter(
            dashboard=obj, user=request.user
        ).first()
        return perm.permission if perm else None

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


class DashboardPermissionSerializer(serializers.ModelSerializer):
    """Serializer for DashboardPermission model."""

    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = DashboardPermission
        fields = [
            "id",
            "dashboard",
            "user",
            "user_name",
            "permission",
            "shared_by",
            "created_at",
        ]
        read_only_fields = ["id", "dashboard", "shared_by", "created_at"]

    def create(self, validated_data):
        validated_data["shared_by"] = self.context["request"].user
        return super().create(validated_data)


class UserSearchSerializer(serializers.ModelSerializer):
    """Minimal user serializer for sharing search."""

    class Meta:
        model = User
        fields = ["id", "username", "email"]
