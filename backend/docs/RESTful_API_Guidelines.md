# RESTful API Guidelines

## Overview

This document provides comprehensive guidelines for building RESTful APIs using Django REST Framework (DRF) with the project's specific architecture patterns.

## Table of Contents

1. [HTTP Methods](#http-methods)
2. [URL Design](#url-design)
3. [Status Codes](#status-codes)
4. [Response Format](#response-format)
5. [Authentication & Authorization](#authentication--authorization)
6. [Filtering & Pagination](#filtering--pagination)
7. [Error Handling](#error-handling)
8. [Versioning](#versioning)
9. [Documentation](#documentation)
10. [Best Practices](#best-practices)

## HTTP Methods

### Standard CRUD Operations

| Method | Purpose | Example |
|--------|---------|---------|
| `GET` | Retrieve data | `GET /api/products/` |
| `POST` | Create new resource | `POST /api/products/` |
| `PUT` | Replace entire resource | `PUT /api/products/1/` |
| `PATCH` | Partial update | `PATCH /api/products/1/` |
| `DELETE` | Delete resource | `DELETE /api/products/1/` |

### Custom Actions

Use `@action` decorator for custom operations:

```python
@action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
def archive(self, request, pk=None):
    """Archive a product."""
    # Implementation
```

**RESTful Compliant Custom Actions:**
- ✅ `products/{id}/archive/` (PATCH)
- ✅ `orders/{id}/update-status/` (PATCH)
- ❌ `products/export/` (Not RESTful)
- ❌ `orders/summary/` (Not RESTful)

## URL Design

### Resource Naming

- Use **nouns** for resources, not verbs
- Use **plural** form for collections
- Use **kebab-case** for multi-word resources

```python
# ✅ Correct
api/categories/
api/products/
api/order-items/

# ❌ Incorrect
api/getCategories/
api/product/
api/orderItems/
```

### URL Structure

```python
# Collection endpoints
GET    /api/products/          # List all products
POST   /api/products/          # Create new product

# Single resource endpoints
GET    /api/products/{id}/     # Get specific product
PUT    /api/products/{id}/     # Replace product
PATCH  /api/products/{id}/     # Update product
DELETE /api/products/{id}/     # Delete product

# Related resources
GET    /api/products/{id}/orders/     # Orders for product
GET    /api/categories/{id}/products/ # Products in category
```

### Custom Actions URLs

```python
# ✅ RESTful custom actions
path("products/<int:pk>/archive/", ...)
path("orders/<int:pk>/update-status/", ...)
path("users/me/", ...)

# ❌ Non-RESTful endpoints
path("products/export/", ...)
path("orders/summary/", ...)
path("products/low-stock/", ...)
```

## Status Codes

### Success Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| `200` | OK | Successful GET, PUT, PATCH |
| `201` | Created | Successful POST |
| `204` | No Content | Successful DELETE |

### Client Error Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| `400` | Bad Request | Invalid request format |
| `401` | Unauthorized | Authentication required |
| `403` | Forbidden | Authenticated but no permission |
| `404` | Not Found | Resource doesn't exist |
| `405` | Method Not Allowed | HTTP method not supported |
| `409` | Conflict | Resource conflict |
| `422` | Unprocessable Entity | Validation errors |

### Server Error Codes

| Code | Meaning | When to Use |
|------|---------|-------------|
| `500` | Internal Server Error | Unexpected server error |

## Response Format

### Success Responses

```json
// List response
{
  "count": 10,
  "next": "http://api.example.com/api/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Product Name",
      "price": "99.99"
    }
  ]
}

// Single resource response
{
  "id": 1,
  "name": "Product Name",
  "price": "99.99",
  "created_at": "2023-01-01T00:00:00Z"
}

// Custom action response
{
  "message": "Product archived successfully",
  "product_id": 1,
  "status": "archived"
}
```

### Error Responses

```json
{
  "error": {
    "status_code": 400,
    "code": "validation_error",
    "message": "Validation failed",
    "details": [
      {
        "field": "email",
        "message": "Enter a valid email address."
      }
    ]
  }
}
```

## Authentication & Authorization

### JWT Authentication

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ViewSet level
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ModelActionPermission]
```

### Permission Classes

```python
# Global permission
permission_classes = [IsAuthenticated]

# Custom permission
permission_classes = [ModelActionPermission]

# Action-specific permission
@action(detail=True, methods=["patch"], permission_classes=[IsAdminUser])
def archive(self, request, pk=None):
    pass
```

## Filtering & Pagination

### Built-in Filtering

```python
class ProductViewSet(viewsets.ModelViewSet):
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "in_stock"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "created_at"]
    ordering = ["-created_at"]
```

### Custom Filtering

```python
def get_queryset(self):
    queryset = super().get_queryset()
    
    # Custom filter
    category_id = self.request.query_params.get("category_id", None)
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    return queryset
```

### Pagination

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "core.utils.pagination.CustomPagination",
}

# ViewSet level
pagination_class = CustomPagination
```

## Error Handling

### DmvnException - Custom Exception Class

All errors should be raised using `DmvnException` for consistent error responses:

```python
from core.base_exception import DmvnException

# Basic error (defaults to 400)
raise DmvnException("Error message")

# Validation error (400)
raise DmvnException("Field is required.", status_code=400, code="bad_request")

# Permission denied (403)
raise DmvnException(
    "You do not have permission to perform this action.",
    status_code=403,
    code="permission_denied"
)

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

### Exception Handler Configuration

```python
# core/base_exception.py
class DmvnException(Exception):
    """Custom exception for DMVN project."""

    def __init__(self, message, status_code=400, code="invalid", details=None):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or []
        super().__init__(message)


def custom_exception_handler(exc, context):
    """Handle all exceptions and return consistent error responses."""
    
    if isinstance(exc, DmvnException):
    raise DmvnException(
        "An error occurred",
        status_code=response.status_code,
        code="error",
        details=response.data,
    )
    
    # Handle other exceptions...
    response = exception_handler(exc, context)
    return response
```

### Error Response Format

```json
{
  "error": {
    "status_code": 400,
    "code": "bad_request",
    "message": "Field is required.",
    "details": []
  }
}
```

### Using DmvnException in Custom Actions

```python
from core.base_exception import DmvnException

@action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated])
def update_status(self, request, pk=None):
    """Update order status."""
    order = self.get_object()
    new_status = request.data.get("status")

    # Validation
    if not new_status:
        raise DmvnException("Status is required.", status_code=400, code="bad_request")

    if new_status not in dict(Order.STATUS_CHOICES):
        raise DmvnException("Invalid status.", status_code=400, code="bad_request")

    # Permission check
    if not request.user.has_perm("app.permission_codename"):
        raise DmvnException(
            "You do not have permission.",
            status_code=403,
            code="permission_denied"
        )

    order.status = new_status
    order.save()

    return Response({"message": "Status updated successfully."})
```

### Validation Errors in Serializers

```python
def validate(self, attrs):
    if attrs.get("name") and attrs.get("description"):
        if attrs["name"].lower() in attrs["description"].lower():
            raise serializers.ValidationError(
                "Product name should not be repeated in description."
            )
    return super().validate(attrs)
```

**Note:** Serializer validation errors are automatically handled by the custom exception handler. Use `DmvnException` for errors in views and custom actions.

## Versioning

### URL Path Versioning

```python
# config/urls.py
urlpatterns = [
    path("api/v1/", include("example.urls")),
]
```

### Accept Header Versioning

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "1.0",
}
```

## Documentation

### Schema Configuration

```python
# settings.py
SPECTACULAR_SETTINGS = {
    "TITLE": "Team Backend API",
    "DESCRIPTION": "API for team management system",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_DIST": "SIDECAR",
    "POSTPROCESSING_HOOKS": [
        "core.schema.add_global_lang_param",
    ],
}
```

### ViewSet Documentation

```python
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product model.
    Demonstrates advanced CRUD operations with custom permissions and actions.
    """
    
    @action(detail=True, methods=["patch"], permission_classes=[ModelActionPermission])
    def archive(self, request, pk=None):
        """Archive a product (custom action with custom permission)."""
        pass
```

## Best Practices

### 1. Use ViewSets

```python
# ✅ Use ViewSets for full CRUD
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

# ❌ Avoid function-based views for CRUD
@api_view(['GET', 'POST'])
def product_list(request):
    pass
```

### 2. Proper Serializer Design

```python
class ProductSerializer(serializers.ModelSerializer):
    # Read-only computed fields
    category_name = serializers.CharField(source="category.name", read_only=True)
    
    class Meta:
        model = Product
        fields = ["id", "name", "price", "category", "category_name"]
        read_only_fields = ["id", "created_at"]
```

### 3. Custom Actions

```python
# ✅ Use @action for custom operations
@action(detail=True, methods=["patch"])
def archive(self, request, pk=None):
    pass

# ❌ Avoid custom endpoints in urls.py
# path("products/archive/", views.archive_product)
```

### 4. Relationship Handling

```python
# ✅ Use select_related and prefetch_related
queryset = Product.objects.select_related("category").prefetch_related("orders")

# ✅ Nested serialization
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
```

### 5. Permission Mapping

```python
# Custom permission mapping for actions
model_permission_mapping = {
    "archive": "example.archive_product",
    "export": "example.export_product",
}
```

### 6. URL Patterns

```python
# ✅ Use router for standard CRUD
router = DefaultRouter()
router.register(r"products", views.ProductViewSet)

# ✅ Custom endpoints only for truly custom operations
urlpatterns = [
    path("", include(router.urls)),
    path("products/<int:pk>/archive/", views.ProductViewSet.as_view({"patch": "archive"})),
]
```

## Django-Specific Patterns

### 1. Model Design

```python
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("archive_product", "Can archive product"),
        ]
```

### 2. Admin Configuration

```python
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "category"]
    list_filter = ["category", "in_stock"]
    search_fields = ["name", "description"]
    readonly_fields = ["created_at", "updated_at"]
```

### 3. Custom Middleware

```python
class APILanguageDetectionMiddleware:
    """Detect language from request and set in context."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Language detection logic
        response = self.get_response(request)
        return response
```

## Security Considerations

### 1. CORS Configuration

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### 2. Security Headers

```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

### 3. Rate Limiting

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}
```

## Testing Guidelines

### 1. API Testing

```python
from rest_framework.test import APITestCase
from rest_framework import status

class ProductAPITestCase(APITestCase):
    def test_create_product(self):
        url = "/api/products/"
        data = {"name": "Test Product", "price": "99.99"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

### 2. Permission Testing

```python
def test_product_archive_permission(self):
    # Test without permission
    response = self.client.patch(f"/api/products/{self.product.id}/archive/")
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # Test with permission
    self.user.user_permissions.add(self.archive_permission)
    response = self.client.patch(f"/api/products/{self.product.id}/archive/")
    self.assertEqual(response.status_code, status.HTTP_200_OK)
```

## Performance Optimization

### 1. Database Queries

```python
# ✅ Use select_related for ForeignKey
queryset = Product.objects.select_related("category")

# ✅ Use prefetch_related for ManyToMany
queryset = Order.objects.prefetch_related("items__product")

# ❌ Avoid N+1 queries
# for product in products:
#     print(product.category.name)  # N+1 queries
```

### 2. Caching

```python
from django.core.cache import cache

class ProductViewSet(viewsets.ModelViewSet):
    def list(self, request):
        cache_key = "products_list"
        products = cache.get(cache_key)
        if not products:
            products = list(self.get_queryset())
            cache.set(cache_key, products, 300)  # 5 minutes
        return Response(self.get_serializer(products, many=True).data)
```

### 3. Pagination

```python
# ✅ Always use pagination for list views
pagination_class = CustomPagination

# ❌ Avoid returning all records
# def list(self, request):
#     return Response(Product.objects.all())  # Bad for large datasets
```

## Conclusion

Following these guidelines ensures that your Django REST Framework API is:

- ✅ **RESTful**: Proper use of HTTP methods and URL design
- ✅ **Consistent**: Uniform response formats and error handling
- ✅ **Secure**: Proper authentication, authorization, and security measures
- ✅ **Performant**: Optimized database queries and caching
- ✅ **Maintainable**: Clear code structure and documentation
- ✅ **Testable**: Comprehensive test coverage

These patterns align with the project's architecture using Django REST Framework, custom permissions, pagination, and the core utilities provided.