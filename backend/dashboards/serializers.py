from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Dashboard, DashboardPermission, DashboardTemplate


class DashboardSerializer(serializers.ModelSerializer):
    """Serializer for Dashboard model."""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    chart_count = serializers.SerializerMethodField()
    user_permission = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Dashboard
        fields = [
            "id",
            "name",
            "description",
            "layout",
            "filters",
            "is_public",
            "is_owner",
            "user_permission",
            "created_by",
            "created_by_name",
            "chart_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_chart_count(self, obj):
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
        try:
            perm = DashboardPermission.objects.get(
                dashboard=obj, user=request.user
            )
            return perm.permission
        except DashboardPermission.DoesNotExist:
            return None

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class DashboardPermissionSerializer(serializers.ModelSerializer):
    """Serializer for DashboardPermission model."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = DashboardPermission
        fields = [
            "id",
            "dashboard",
            "user",
            "username",
            "permission",
            "shared_by",
            "created_at",
        ]
        read_only_fields = ["id", "shared_by", "created_at", "dashboard"]

    def create(self, validated_data):
        validated_data["shared_by"] = self.context["request"].user
        return super().create(validated_data)


class DashboardRenderSerializer(serializers.Serializer):
    """Serializer for rendered dashboard with chart data."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField()
    layout = serializers.JSONField()
    charts_data = serializers.ListField()
    filters = serializers.JSONField()


class UserSearchSerializer(serializers.ModelSerializer):
    """Serializer for user search results."""

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email"]


class DashboardTemplateSerializer(serializers.ModelSerializer):
    """Serializer for DashboardTemplate model."""

    class Meta:
        model = DashboardTemplate
        fields = [
            "id",
            "name",
            "description",
            "category",
            "layout",
            "chart_configs",
            "preview_image",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]