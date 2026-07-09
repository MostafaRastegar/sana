from rest_framework import serializers


def map_drf_type_to_ts(field):
    """Maps DRF field types to TypeScript types."""
    if isinstance(
        field,
        (
            serializers.IntegerField,
            serializers.FloatField,
            serializers.DecimalField,
        ),
    ):
        return "number"

    elif isinstance(
        field,
        (
            serializers.CharField,
            serializers.EmailField,
            serializers.URLField,
            serializers.UUIDField,
            serializers.DateField,
            serializers.DateTimeField,
            serializers.TimeField,
        ),
    ):
        return "string"
    elif isinstance(field, serializers.BooleanField):
        return "boolean"
    elif isinstance(field, serializers.Serializer):
        return field.__class__.__name__.replace("Serializer", "") + "Model"
    return "any"
