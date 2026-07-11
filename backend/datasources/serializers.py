import os
import re

from django.conf import settings
from rest_framework import serializers

from .models import CSVImportJob, DataSource, SyncLog


def _validate_filename(name):
    """Prevent path traversal: only safe filename chars."""
    if not re.match(r'^[a-zA-Z0-9_\.\-]+$', name):
        raise serializers.ValidationError(f"Invalid filename: '{name}'")


class DataSourceSerializer(serializers.ModelSerializer):
    decrypted_config = serializers.SerializerMethodField()

    class Meta:
        model = DataSource
        fields = [
            "id", "name", "source_type", "connection_config",
            "decrypted_config", "auto_sync_enabled", "csv_config",
            "sync_schedule", "is_active", "last_synced",
            "status", "error_message", "created_at", "updated_at",
        ]
        read_only_fields = [
            "last_synced", "status", "error_message",
            "created_at", "updated_at", "decrypted_config",
        ]
        extra_kwargs = {
            "connection_config": {"write_only": True},
        }

    def get_decrypted_config(self, obj):
        return obj.get_decrypted_config()

    def validate(self, attrs):
        ds_type = attrs.get("source_type", getattr(self.instance, "source_type", None))

        # CSV uploads: auto-populate connection_config from uploaded file
        if ds_type == "csv":
            config = attrs.get("connection_config")

            # If updating and no new connection_config provided, keep existing
            if config is None and self.instance and self.instance.pk:
                # Don't wipe existing config on update without config data
                attrs.pop("connection_config", None)
                return super().validate(attrs)

            # If config is a string (already encrypted from the model), skip
            if isinstance(config, str):
                return super().validate(attrs)

            # If already has a valid config (update without new file), keep it
            if config and isinstance(config, dict) and config.get("file_path"):
                file_path = config["file_path"]
                if os.path.exists(file_path):
                    return super().validate(attrs)

            # Try to get file from initial_data
            f = self.initial_data.get("file")
            if f:
                safe_name = os.path.basename(f.name)
                _validate_filename(safe_name)
                upload_dir = os.path.join(settings.MEDIA_ROOT, "datasource_files")
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, safe_name)
                with open(file_path, "wb+") as dest:
                    for chunk in f.chunks():
                        dest.write(chunk)
                attrs["connection_config"] = {
                    "file_path": file_path,
                    "file_name": safe_name,
                }

        return super().validate(attrs)

    def create(self, validated_data):
        validated_data.pop("decrypted_config", None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("decrypted_config", None)
        return super().update(instance, validated_data)


class DataSourceListSerializer(serializers.ModelSerializer):
    """Compact serializer for list views (no config)."""

    class Meta:
        model = DataSource
        fields = [
            "id", "name", "source_type", "sync_schedule", "is_active",
            "last_synced", "status", "error_message", "created_at", "updated_at",
        ]


class SyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncLog
        fields = [
            "id", "source", "started_at", "finished_at",
            "status", "rows_imported", "error_message", "created_at",
        ]
        read_only_fields = ["created_at"]


class CSVImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSVImportJob
        fields = [
            "id", "source", "file_name", "file_path",
            "rows_total", "rows_imported", "rows_failed",
            "error_log", "status", "started_at", "finished_at", "created_at",
        ]
        read_only_fields = ["created_at", "started_at", "finished_at"]


class TestConnectionSerializer(serializers.Serializer):
    id = serializers.IntegerField()