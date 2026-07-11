from rest_framework import serializers
from .models import Dataset


class DatasetSerializer(serializers.ModelSerializer):
    """Serializer for Dataset model."""

    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    column_count = serializers.SerializerMethodField()
    datasource_name = serializers.CharField(
        source="datasource.name", read_only=True, allow_null=True
    )

    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "description",
            "table_name",
            "columns",
            "row_count",
            "column_count",
            "datasource",
            "datasource_name",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at", "datasource_name"]

    def get_column_count(self, obj):
        """Get number of columns in this dataset."""
        return len(obj.columns) if isinstance(obj.columns, list) else 0

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Dataset name must be at least 2 characters long."
            )
        return value

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)


class DatasetDataSerializer(serializers.Serializer):
    """Serializer for returning dataset row data."""

    columns = serializers.ListField(child=serializers.DictField())
    rows = serializers.ListField(child=serializers.DictField())
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()