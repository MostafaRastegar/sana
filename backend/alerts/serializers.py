from rest_framework import serializers
from .models import DataAlert, AlertHistory


class AlertHistorySerializer(serializers.ModelSerializer):
    """Serializer for AlertHistory model."""

    alert_name = serializers.CharField(source="alert.name", read_only=True)

    class Meta:
        model = AlertHistory
        fields = [
            "id",
            "alert",
            "alert_name",
            "triggered_at",
            "actual_value",
            "threshold",
            "condition",
            "message",
            "notification_sent",
            "notification_response",
        ]
        read_only_fields = [
            "id", "triggered_at", "notification_sent", "notification_response",
        ]


class DataAlertSerializer(serializers.ModelSerializer):
    """Serializer for DataAlert model."""

    dataset_name = serializers.CharField(
        source="dataset.name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.username", read_only=True
    )
    condition_display = serializers.CharField(
        source="get_condition_display", read_only=True
    )
    recipient_ids = serializers.PrimaryKeyRelatedField(
        source="recipients",
        queryset=serializers.CurrentUserDefault(),  # placeholder, overridden in __init__
        many=True,
        required=False,
    )

    class Meta:
        model = DataAlert
        fields = [
            "id",
            "name",
            "description",
            "dataset",
            "dataset_name",
            "metric",
            "aggregation",
            "condition",
            "condition_display",
            "threshold",
            "check_interval",
            "notification_channels",
            "recipients",
            "recipient_ids",
            "webhook_url",
            "filters",
            "is_active",
            "created_by",
            "created_by_name",
            "last_checked",
            "last_triggered",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "created_by", "last_checked", "last_triggered",
            "created_at", "updated_at",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields["recipient_ids"] = serializers.PrimaryKeyRelatedField(
            source="recipients",
            queryset=User.objects.all(),
            many=True,
            required=False,
        )

    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError(
                "Alert name must be at least 2 characters long."
            )
        return value

    def validate_threshold(self, value):
        if self.initial_data.get("condition") == "change_percent" and value == 0:
            raise serializers.ValidationError(
                "Threshold cannot be 0 for percent change condition."
            )
        return value

    def create(self, validated_data):
        recipients = validated_data.pop("recipients", [])
        instance = super().create(validated_data)
        if recipients:
            instance.recipients.set(recipients)
        return instance

    def update(self, instance, validated_data):
        recipients = validated_data.pop("recipients", None)
        instance = super().update(instance, validated_data)
        if recipients is not None:
            instance.recipients.set(recipients)
        return instance