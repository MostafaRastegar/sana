from rest_framework import serializers
from .models import Chart, SavedQuery


class ChartSerializer(serializers.ModelSerializer):
    """Serializer for Chart model."""

    dataset_name = serializers.CharField(
        source="dataset.name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    chart_type_display = serializers.CharField(
        source="get_chart_type_display", read_only=True
    )

    class Meta:
        model = Chart
        fields = [
            "id",
            "name",
            "description",
            "dataset",
            "dataset_name",
            "chart_type",
            "chart_type_display",
            "config",
            "drill_down_config",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Chart name must be at least 2 characters long."
            )
        return value

    def validate_config(self, value):
        """Validate chart config structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Config must be a JSON object.")
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class ChartDataSerializer(serializers.Serializer):
    """Serializer for computed chart data."""

    columns = serializers.ListField(child=serializers.DictField())
    rows = serializers.ListField(child=serializers.DictField())
    chart_type = serializers.CharField()
    config = serializers.DictField()


class SavedQuerySerializer(serializers.ModelSerializer):
    """Serializer for SavedQuery model."""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    dataset_name = serializers.CharField(
        source="dataset.name", read_only=True
    )

    class Meta:
        model = SavedQuery
        fields = [
            "id",
            "name",
            "sql",
            "dataset",
            "dataset_name",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)