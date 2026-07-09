---
name: crud_pattern_rule
description: Brief description of what this skill does
---

# crud_pattern_rule

Instructions for the AI agent...

## Usage

# CRUD Implementation Rules for Djankit Project

When implementing CRUD operations in this Django REST Framework project, follow these patterns strictly.

## Model Implementation

### Required Structure
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

User = get_user_model()


class ModelName(models.Model):
    """Model description"""
    
    # Fields with verbose_name
    name = models.CharField(max_length=100, verbose_name=_("Name"))
    
    # Timestamps (ALWAYS include)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Model Name")
        verbose_name_plural = _("Model Names")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def clean(self):
        """Custom validation"""
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

### Field Patterns
- **ForeignKey**: Always use `related_name` for reverse access
- **Choices**: Define as class constant `STATUS_CHOICES`
- **Always add `verbose_name` using `_()` for translation**

## Serializer Implementation

### Required Structure
```python
from rest_framework import serializers
from .models import ModelName


class ModelNameSerializer(serializers.ModelSerializer):
    """Serializer description"""
    
    # Computed fields
    related_display = serializers.CharField(source="related.name", read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = ModelName
        fields = ["id", "name", "related", "related_display", "item_count", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_item_count(self, obj):
        return obj.items.count()

    def validate_name(self, value):
        # Field validation
        return value

    def validate(self, attrs):
        # Cross-field validation
        return super().validate(attrs)
```

### Nested Write Pattern
```python
def create(self, validated_data):
    items_data = validated_data.pop("items", [])
    instance = Model.objects.create(**validated_data)
    for item_data in items_data:
        Item.objects.create(parent=instance, **item_data)
    return instance

def update(self, instance, validated_data):
    items_data = validated_data.pop("items", [])
    for attr, value in validated_data.items():
        setattr(instance, attr, value)
    instance.save()
    if items_data:
        instance.items.all().delete()
        for item_data in items_data:
            Item.objects.create(parent=instance, **item_data)
    return instance
```

## ViewSet Implementation

### Required Structure
```python
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from .models import ModelName
from .serializers import ModelNameSerializer


class ModelNameViewSet(viewsets.ModelViewSet):
    """ViewSet description"""
    
    # Query optimization (ALWAYS optimize)
    queryset = ModelName.objects.select_related("foreign_key").prefetch_related("many_to_many")
    
    serializer_class = ModelNameSerializer
    permission_classes = [ModelActionPermission]
    pagination_class = CustomPagination
    
    # Filters
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "category"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Dynamic filters
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
```

### Query Optimization Rules
- **select_related**: For ForeignKey and OneToOne fields
- **prefetch_related**: For ManyToMany and reverse ForeignKey
- **Always optimize to prevent N+1 queries**

## URL Implementation

### Required Structure
```python
# app_name/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"resources", views.ResourceViewSet, basename="resource")

urlpatterns = [
    path("", include(router.urls)),
]
```

## Permission Rules

### Standard Permissions
- `IsAuthenticated`: Only logged-in users
- `IsAdminUser`: Only admin users
- `ModelActionPermission`: Custom permission based on model permissions

### Custom Action Permissions
```python
# Map custom actions to model permissions
model_permission_mapping = {
    "archive": "app_name.archive_model",
    "export": "app_name.export_model",
}
```

## Custom Actions

### Detail Action (single object)
```python
@action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
def action_name(self, request, pk=None):
    obj = self.get_object()
    # Process
    return Response(data)
```

### List Action (entire list)
```python
@action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
def action_name(self, request):
    queryset = self.get_queryset()
    # Process
    return Response(data)
```

## Implementation Checklist

### Before Creating Model
- [ ] Define all fields with `verbose_name`
- [ ] Add `created_at` and `updated_at`
- [ ] Define `__str__` method
- [ ] Add custom permissions in Meta (if needed)
- [ ] Implement `clean()` for validation (if needed)

### Before Creating Serializer
- [ ] Define `fields` and `read_only_fields`
- [ ] Add computed fields with `SerializerMethodField`
- [ ] Implement field validation with `validate_<field>`
- [ ] Implement cross-field validation with `validate`
- [ ] Handle nested writes (if needed)

### Before Creating ViewSet
- [ ] Optimize queryset with `select_related`/`prefetch_related`
- [ ] Set `serializer_class`
- [ ] Set `permission_classes`
- [ ] Set `pagination_class`
- [ ] Configure filters
- [ ] Add `get_queryset` for dynamic filters (if needed)
- [ ] Add `perform_create` for auto fields (if needed)
- [ ] Register in `urls.py`

## Error Handling

### Use DmvnException for All Errors
```python
from core.base_exception import DmvnException

# Validation error (400)
raise DmvnException("Field is required.", status_code=400, code="bad_request")

# Permission denied (403)
raise DmvnException("You do not have permission.", status_code=403, code="permission_denied")

# Not found (404)
raise DmvnException("Resource not found.", status_code=404, code="not_found")

# With details
raise DmvnException(
    "Validation failed.",
    status_code=400,
    code="validation_error",
    details={"field": ["error message"]}
)
```

### Error Handling Pattern in Actions
```python
@action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
def update_status(self, request, pk=None):
    obj = self.get_object()
    new_value = request.data.get("field")

    # Validation
    if not new_value:
        raise DmvnException("Field is required.", status_code=400, code="bad_request")

    if new_value not in VALID_CHOICES:
        raise DmvnException("Invalid value.", status_code=400, code="bad_request")

    # Permission check
    if not request.user.has_perm("app.permission_codename"):
        raise DmvnException(
            "You do not have permission.",
            status_code=403,
            code="permission_denied"
        )

    obj.field = new_value
    obj.save()

    return Response({"message": "Updated successfully."})
```

## Critical Rules

1. **NEVER skip query optimization** - Always use `select_related` or `prefetch_related`
2. **ALWAYS set permissions** - No unprotected endpoints
3. **ALWAYS mark read-only fields** - `id`, `created_at`, `updated_at`
4. **ALWAYS use `get_queryset` for dynamic filters**
5. **ALWAYS validate inputs in custom actions**
6. **ALWAYS return proper Response with status codes**
7. **ALWAYS use DmvnException for errors** - Never use `create_error_response` directly
