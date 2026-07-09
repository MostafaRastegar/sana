---
name: django_rest_framework_best_practices
description: Brief description of what this skill does
---

# Django REST Framework Best Practices

## Overview
This rule defines best practices for Django REST Framework (DRF) development, focusing on API design, security, performance, and maintainability.

## Rule Details

### 1. ViewSet Design and Permissions

**Description**: ViewSets should follow consistent patterns for permissions, filtering, and actions.

**Pattern**: 
- Use `ModelActionPermission` for consistent permission mapping
- Implement proper queryset optimization with `select_related` and `prefetch_related`
- Use custom permission mapping for custom actions
- Always specify `basename` in router registration

**Example**:
```python
# GOOD
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'created_by').prefetch_related('orders')
    permission_classes = [ModelActionPermission]
    model_permission_mapping = {
        'archive': 'example.archive_product',
        'export': 'example.export_product',
    }
    
    @action(detail=True, methods=['patch'], permission_classes=[ModelActionPermission])
    def archive(self, request, pk=None):
        # Implementation

# BAD
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()  # No optimization
    permission_classes = [IsAuthenticated]  # Generic permission
```

### 2. Serializer Validation and Security

**Description**: Serializers should implement proper validation, avoid exposing sensitive data, and handle nested objects correctly.

**Pattern**:
- Use `validate_<field_name>` methods for field validation
- Implement `validate()` method for cross-field validation
- Use `read_only_fields` for computed fields
- Avoid exposing sensitive user data in serializers
- Handle nested object creation/updates properly

**Example**:
```python
# GOOD
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'category_name']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
    
    def validate(self, attrs):
        if attrs.get('name') and attrs.get('description'):
            if attrs['name'].lower() in attrs['description'].lower():
                raise serializers.ValidationError("Product name should not be repeated in description.")
        return super().validate(attrs)

# BAD
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'  # Exposes all fields including sensitive ones
```

### 3. Exception Handling and Error Responses

**Description**: Use consistent exception handling with proper HTTP status codes and structured error responses.

**Pattern**:
- Use `DmvnException` for custom business logic errors
- Implement custom exception handler in `core.base_exception`
- Return structured error responses with status code, message, and details
- Avoid exposing internal error details to clients

**Example**:
```python
# GOOD
from core.base_exception import DmvnException

def some_view_method(self, request):
    if not request.user.has_perm('example.archive_product'):
        raise DmvnException(
            "You do not have permission to archive products.",
            status_code=403,
            code="permission_denied",
        )

# BAD
def some_view_method(self, request):
    if not request.user.has_perm('example.archive_product'):
        raise PermissionDenied("Access denied")  # Generic exception
```

### 4. Queryset Optimization

**Description**: Always optimize database queries to prevent N+1 problems and improve performance.

**Pattern**:
- Use `select_related()` for ForeignKey and OneToOneField relationships
- Use `prefetch_related()` for ManyToManyField and reverse ForeignKey relationships
- Implement custom `get_queryset()` methods for filtering
- Use database indexes for frequently queried fields

**Example**:
```python
# GOOD
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'created_by').prefetch_related('orders')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

# BAD
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()  # No optimization
```

### 5. API Documentation and Schema

**Description**: Use DRF Spectacular for comprehensive API documentation with proper schema definitions.

**Pattern**:
- Configure `SPECTACULAR_SETTINGS` in settings
- Use `@extend_schema` decorator for custom endpoints
- Implement proper response schemas for all endpoints
- Use `AutoSchema` for automatic schema generation

**Example**:
```python
# GOOD - Settings configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "Team Backend API",
    "DESCRIPTION": "API for team management system",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

# GOOD - ViewSet with proper schema
class ProductViewSet(viewsets.ModelViewSet):
    schema = AutoSchema()
    # Implementation

# BAD - No schema configuration
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema',
}
```

### 6. Authentication and Authorization

**Description**: Implement proper authentication and authorization patterns using JWT and custom permissions.

**Pattern**:
- Use JWT authentication with proper token lifetime settings
- Implement custom permission classes for fine-grained access control
- Use `@action` decorator for custom endpoints with proper permission classes
- Always validate user permissions before sensitive operations

**Example**:
```python
# GOOD
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ModelActionPermission]
    
    @action(detail=True, methods=['patch'], permission_classes=[ModelActionPermission])
    def archive(self, request, pk=None):
        product = self.get_object()
        if not request.user.has_perm('example.archive_product'):
            raise DmvnException("Permission denied", status_code=403)
        # Implementation

# BAD
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # Too generic
    
    @action(detail=True, methods=['patch'])
    def archive(self, request, pk=None):
        # No permission check
        pass
```

### 7. Pagination and Filtering

**Description**: Implement consistent pagination and filtering across all list endpoints.

**Pattern**:
- Use custom pagination class for consistent page sizes
- Implement proper filter backends for search and filtering
- Use `ordering_fields` and `search_fields` for discoverability
- Handle filter validation properly

**Example**:
```python
# GOOD
class ProductViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['category', 'in_stock', 'created_by']
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']

# BAD
class ProductViewSet(viewsets.ModelViewSet):
    # No pagination or filtering
    pass
```

### 8. Model Design and Relationships

**Description**: Design models with proper relationships, validation, and business logic.

**Pattern**:
- Use `clean()` method for model validation
- Implement proper `save()` method with validation
- Use `related_name` for reverse relationships
- Define custom permissions in model Meta class
- Use `select_related` and `prefetch_related` in related queries

**Example**:
```python
# GOOD
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
    )
    
    class Meta:
        permissions = [
            ("archive_product", "Can archive product"),
            ("export_product", "Can export product data"),
        ]
    
    def clean(self):
        if self.price < 0:
            raise ValidationError(_("Price cannot be negative."))
        return super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# BAD
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # No related_name
    # No validation or permissions
```

## Implementation Guidelines

1. **Consistency**: Apply these patterns consistently across all ViewSets and serializers
2. **Security**: Always validate permissions and sanitize input data
3. **Performance**: Optimize queries and implement proper caching where needed
4. **Documentation**: Use proper docstrings and schema definitions for API documentation
5. **Testing**: Write comprehensive tests for all endpoints and validation logic
6. **Error Handling**: Implement structured error responses with appropriate HTTP status codes

## Tools and Configuration

- Use `ModelActionPermission` for consistent permission mapping
- Configure `CustomPagination` for consistent pagination
- Use `DmvnException` for custom business logic errors
- Implement proper logging for debugging and monitoring
- Use APM tools for performance monitoring in production