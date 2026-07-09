# CRUD Implementation Patterns Guide for Djankit Project

This document demonstrates standard CRUD implementation patterns in the project based on the `example` app.

## Table of Contents

1. [Models](#models)
2. [Serializers](#serializers)
3. [ViewSets](#viewsets)
4. [URLs](#urls)
5. [Permissions](#permissions)
6. [Custom Actions](#custom-actions)

---

## Models

### Basic Structure

```python
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

User = get_user_model()


class ExampleModel(models.Model):
    """
    Model description
    """
    
    # Fields
    name = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name=_("Name")
    )
    description = models.TextField(
        blank=True, 
        verbose_name=_("Description")
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name=_("Updated At")
    )

    class Meta:
        verbose_name = _("Example Model")
        verbose_name_plural = _("Example Models")
        ordering = ["-created_at"]
        permissions = [
            ("custom_action_model", "Can perform custom action"),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Custom validation"""
        if self.name and len(self.name) < 3:
            raise ValidationError(_("Name must be at least 3 characters."))
        return super().clean()

    def save(self, *args, **kwargs):
        """Call validation before saving"""
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def computed_field(self):
        """Computed field"""
        return f"{self.name} - computed"
```

### Common Field Patterns

```python
# ForeignKey
category = models.ForeignKey(
    Category,
    on_delete=models.CASCADE,
    related_name="products",  # Reverse access: category.products.all()
    verbose_name=_("Category"),
)

# ForeignKey with SET_NULL
created_by = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="created_items",
    verbose_name=_("Created By"),
)

# Choices
STATUS_CHOICES = [
    ("pending", _("Pending")),
    ("processing", _("Processing")),
    ("completed", _("Completed")),
]
status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default="pending",
    verbose_name=_("Status"),
)

# Boolean
is_active = models.BooleanField(default=True, verbose_name=_("Is Active"))

# Decimal
price = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    verbose_name=_("Price")
)
```

---

## Serializers

### Basic Serializer

```python
from rest_framework import serializers
from .models import ExampleModel


class ExampleSerializer(serializers.ModelSerializer):
    """
    Basic serializer with validation
    """
    
    # Computed field
    related_name = serializers.CharField(
        source="related.name", 
        read_only=True
    )
    
    # Count field
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = ExampleModel
        fields = [
            "id",
            "name",
            "description",
            "related",
            "related_name",
            "item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_item_count(self, obj):
        """Calculate item count"""
        return obj.items.count()

    def validate_name(self, value):
        """Validate name field"""
        if len(value) < 3:
            raise serializers.ValidationError(
                "Name must be at least 3 characters long."
            )
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        if attrs.get("name") and attrs.get("description"):
            if attrs["name"].lower() in attrs["description"].lower():
                raise serializers.ValidationError(
                    "Name should not be repeated in description."
                )
        return super().validate(attrs)
```

### Nested Write Serializer

```python
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price", "total_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer_name", "items", "item_count", "created_at"]
        read_only_fields = ["id", "item_count", "created_at"]

    def create(self, validated_data):
        """Create with nested items"""
        items_data = validated_data.pop("items", [])
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        return order

    def update(self, instance, validated_data):
        """Update with nested items"""
        items_data = validated_data.pop("items", [])
        
        # Update main fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update items
        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        
        return instance
```

### Inherited Serializer

```python
class ProductListSerializer(ProductSerializer):
    """List serializer with additional fields"""
    
    discounted_price = serializers.SerializerMethodField()

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ["discounted_price"]

    def get_discounted_price(self, obj):
        return round(obj.price * 0.9, 2)
```

---

## ViewSets

### Basic ModelViewSet

```python
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from core.permissions import ModelActionPermission
from core.utils.pagination import CustomPagination
from .models import ExampleModel
from .serializers import ExampleSerializer


class ExampleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for full CRUD operations
    """
    
    # Query optimization
    queryset = ExampleModel.objects.select_related(
        "related_field"
    ).prefetch_related("many_to_many_field")
    
    serializer_class = ExampleSerializer
    
    # Permissions
    permission_classes = [ModelActionPermission]
    
    # Pagination
    pagination_class = CustomPagination
    
    # Filters
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "category"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """Filter queryset based on request parameters"""
        queryset = super().get_queryset()
        
        # Custom filter
        custom_param = self.request.query_params.get("custom_param", None)
        if custom_param:
            queryset = queryset.filter(custom_field=custom_param)
        
        return queryset

    def perform_create(self, serializer):
        """Set created_by field on creation"""
        serializer.save(created_by=self.request.user)
```

### ReadOnlyModelViewSet

```python
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    pagination_class = CustomPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["username", "email"]
    ordering_fields = ["username", "date_joined"]
    ordering = ["username"]
```

### Query Optimization

```python
# select_related for ForeignKey and OneToOne
queryset = Product.objects.select_related(
    "category", "created_by"
)

# prefetch_related for ManyToMany and reverse ForeignKey
queryset = Order.objects.prefetch_related(
    "items__product"
)

# Combined
queryset = Product.objects.select_related(
    "category", "created_by"
).prefetch_related("orders")
```

---

## URLs

### Basic Structure

```python
# app_name/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router
router = DefaultRouter()

# Register ViewSets
router.register(r"resources", views.ResourceViewSet, basename="resource")
router.register(r"items", views.ItemViewSet, basename="item")

# URL patterns
urlpatterns = [
    path("", include(router.urls)),
]
```

### Adding to Main URLs

```python
# config/urls.py
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path("api/", include("app_name.urls")),
]
```

---

## Permissions

### Standard Permissions

```python
from rest_framework.permissions import IsAuthenticated, IsAdminUser

# Only logged-in users
permission_classes = [IsAuthenticated]

# Only admins
permission_classes = [IsAdminUser]
```

### Custom Permission (ModelActionPermission)

```python
from core.permissions import ModelActionPermission

# Use in ViewSet
permission_classes = [ModelActionPermission]

# Map custom actions to model permissions
model_permission_mapping = {
    "archive": "app_name.archive_model",
    "export": "app_name.export_model",
}
```

### Permissions in Actions

```python
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

class ExampleViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def custom_action(self, request, pk=None):
        """Action with IsAuthenticated permission"""
        pass

    @action(detail=True, methods=["patch"], permission_classes=[ModelActionPermission])
    def archive(self, request, pk=None):
        """Action with custom permission"""
        if not request.user.has_perm("app_name.archive_model"):
            raise DmvnException("app_name.archive_model")
        # ...
```

---

## Custom Actions

### Detail Action (on a single object)

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class ProductViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def orders(self, request, pk=None):
        """Get orders for a product"""
        product = self.get_object()
        orders = product.orders.all()
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], permission_classes=[ModelActionPermission])
    def archive(self, request, pk=None):
        """Archive a product"""
        product = self.get_object()
        
        if not request.user.has_perm("example.archive_product"):
            raise DmvnException("example.archive_product")
        
        product.in_stock = False
        product.save()
        
        return Response(
            {"message": f'Product "{product.name}" has been archived.'},
            status=status.HTTP_200_OK,
        )
```

### List Action (on entire list)

```python
class CategoryViewSet(viewsets.ModelViewSet):
    
    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def stats(self, request):
        """Category statistics"""
        stats = {
            "total_categories": self.get_queryset().count(),
            "categories_with_products": self.get_queryset()
            .filter(products__isnull=False)
            .distinct()
            .count(),
        }
        return Response(stats)
```

### Action with Parameter

```python
@action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
def update_status(self, request, pk=None):
    """Update order status"""
    order = self.get_object()
    new_status = request.data.get("status")

    # Validation
    if not new_status:
        raise DmvnException("Status is required.", status_code=400, code="bad_request")

    if new_status not in dict(Order.STATUS_CHOICES):
        raise DmvnException("Invalid status.", status_code=400, code="bad_request")

    order.status = new_status
    order.save()

    return Response({
        "message": f"Order status updated to {order.get_status_display()}",
        "order_id": order.id,
        "status": order.status,
    })
```

---

## Implementation Checklist

### For Each New Model:

- [ ] Create model with `verbose_name` and `ordering`
- [ ] Add `created_at` and `updated_at`
- [ ] Define `__str__`
- [ ] Add custom `permissions` (if needed)
- [ ] Validation in `clean()` (if needed)

### For Each Serializer:

- [ ] Define `fields` and `read_only_fields`
- [ ] Add computed fields with `SerializerMethodField`
- [ ] Field validation with `validate_<field>`
- [ ] Cross-field validation with `validate`
- [ ] Handle nested writes (if needed)

### For Each ViewSet:

- [ ] Set `queryset` with `select_related` and `prefetch_related`
- [ ] Set `serializer_class`
- [ ] Set `permission_classes`
- [ ] Set `pagination_class`
- [ ] Set `filter_backends` and filters
- [ ] Add `get_queryset` (if needed)
- [ ] Add `perform_create` (if needed)
- [ ] Register in `urls.py`

### For Custom Actions:

- [ ] Set `detail=True` or `detail=False`
- [ ] Set `methods`
- [ ] Set `permission_classes`
- [ ] Validate inputs
- [ ] Return appropriate `Response`

---

## Important Notes

1. **Always use `select_related` and `prefetch_related`** to avoid N+1 query problems
2. **Set permissions at ViewSet and action level**, not at method level
3. **Mark read-only fields** such as `id`, `created_at`, `updated_at`
4. **Use `get_queryset` for dynamic filters**
5. **Translate error messages** for users
6. **Always verify authentication token** for protected endpoints