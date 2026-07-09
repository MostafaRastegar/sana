---
name: restful_api_rule
description: Brief description of what this skill does
---

# Cline Rule: RESTful API Development

## Rule Overview

This rule enforces RESTful API development standards for Django REST Framework projects using the project's specific architecture patterns.

## Rule Configuration

```yaml
rule_name: "RESTful API Development"
description: "Enforces RESTful API standards for Django REST Framework"
category: "API Development"
severity: "error"
```

## Enforced Standards

### 1. HTTP Methods Usage

**Requirement**: Use appropriate HTTP methods for operations

**Checks**:
- ✅ `GET` for retrieving data
- ✅ `POST` for creating resources
- ✅ `PUT` for replacing entire resources
- ✅ `PATCH` for partial updates
- ✅ `DELETE` for deleting resources
- ❌ Using `POST` for non-creation operations
- ❌ Using `GET` for operations that modify data

**Example**:
```python
# ✅ Correct
@action(detail=True, methods=["patch"])
def archive(self, request, pk=None):
    pass

# ❌ Incorrect
@action(detail=True, methods=["post"])
def archive(self, request, pk=None):
    pass
```

### 2. URL Design

**Requirement**: Use RESTful URL patterns

**Checks**:
- ✅ Use nouns, not verbs in URLs
- ✅ Use plural form for collections
- ✅ Use kebab-case for multi-word resources
- ✅ Use proper URL structure: `/api/resources/{id}/action/`
- ❌ Using verbs in URLs: `/api/getProducts/`
- ❌ Using singular form: `/api/product/`
- ❌ Using camelCase: `/api/productItems/`

**Example**:
```python
# ✅ Correct
path("products/<int:pk>/archive/", ...)
path("categories/<int:pk>/products/", ...)

# ❌ Incorrect
path("products/archive/", ...)
path("product/<int:pk>/archive/", ...)
```

### 3. Custom Actions

**Requirement**: Only use custom actions for truly custom operations

**Checks**:
- ✅ Use `@action` decorator for custom operations
- ✅ Use appropriate HTTP methods (PATCH for updates)
- ✅ Use descriptive action names
- ❌ Creating custom endpoints for standard CRUD
- ❌ Using non-RESTful custom endpoints
- ❌ Using POST for update operations

**Allowed Custom Actions**:
```python
# ✅ RESTful custom actions
products/{id}/archive/
orders/{id}/update-status/
users/me/
users/{id}/products/
categories/{id}/products/

# ❌ Non-RESTful endpoints
products/export/
orders/summary/
products/low-stock/
orders/my-orders/
```

### 4. Response Format

**Requirement**: Use consistent response formats

**Checks**:
- ✅ Use structured error responses
- ✅ Include proper status codes
- ✅ Use consistent field naming
- ✅ Include pagination for list responses
- ❌ Returning raw Django errors
- ❌ Inconsistent error formats
- ❌ Missing status codes

**Example**:
```python
# ✅ Correct error response
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

# ❌ Incorrect error response
{"detail": "Validation failed"}
```

### 5. Authentication & Authorization

**Requirement**: Use proper authentication and authorization

**Checks**:
- ✅ Use JWT authentication
- ✅ Use appropriate permission classes
- ✅ Use ModelActionPermission for custom actions
- ✅ Use IsAuthenticated for protected endpoints
- ❌ Using no authentication for protected endpoints
- ❌ Using wrong permission classes
- ❌ Hardcoding permissions in views

**Example**:
```python
# ✅ Correct
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [ModelActionPermission]

# ❌ Incorrect
class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
```

### 6. Filtering & Pagination

**Requirement**: Always implement filtering and pagination

**Checks**:
- ✅ Use DjangoFilterBackend for filtering
- ✅ Use SearchFilter for search
- ✅ Use OrderingFilter for sorting
- ✅ Use CustomPagination for pagination
- ✅ Implement custom filtering when needed
- ❌ Returning all records without pagination
- ❌ Missing filtering options
- ❌ Inconsistent pagination

**Example**:
```python
# ✅ Correct
class ProductViewSet(viewsets.ModelViewSet):
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "in_stock"]
    search_fields = ["name", "description"]
    pagination_class = CustomPagination

# ❌ Incorrect
class ProductViewSet(viewsets.ModelViewSet):
    # No filtering or pagination
    pass
```

### 7. Serializer Design

**Requirement**: Use proper serializer patterns

**Checks**:
- ✅ Use ModelSerializer for model-based serializers
- ✅ Use read-only fields for computed values
- ✅ Use proper field validation
- ✅ Use nested serialization for relationships
- ✅ Use Meta class for configuration
- ❌ Using Serializer for model data
- ❌ Missing validation
- ❌ Inconsistent field naming

**Example**:
```python
# ✅ Correct
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    
    class Meta:
        model = Product
        fields = ["id", "name", "price", "category", "category_name"]
        read_only_fields = ["id", "created_at"]

# ❌ Incorrect
class ProductSerializer(serializers.Serializer):
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
```

### 8. ViewSet Design

**Requirement**: Use ViewSets for API endpoints

**Checks**:
- ✅ Use ModelViewSet for full CRUD
- ✅ Use ReadOnlyModelViewSet for read-only
- ✅ Use proper queryset optimization
- ✅ Use select_related and prefetch_related
- ❌ Using function-based views for CRUD
- ❌ Missing queryset optimization
- ❌ N+1 query problems

**Example**:
```python
# ✅ Correct
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").prefetch_related("orders")
    serializer_class = ProductSerializer

# ❌ Incorrect
@api_view(['GET', 'POST'])
def product_list(request):
    # Function-based view
    pass
```

### 9. URL Configuration

**Requirement**: Use proper URL patterns

**Checks**:
- ✅ Use routers for standard CRUD
- ✅ Use path() for custom endpoints
- ✅ Include custom endpoints in router URLs
- ✅ Use proper URL naming
- ❌ Using url() (deprecated)
- ❌ Hardcoding URL patterns
- ❌ Missing URL names

**Example**:
```python
# ✅ Correct
router = DefaultRouter()
router.register(r"products", views.ProductViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("products/<int:pk>/archive/", views.ProductViewSet.as_view({"patch": "archive"})),
]

# ❌ Incorrect
urlpatterns = [
    url(r'^products/$', views.product_list),  # Deprecated
    path("archive-product/", views.archive_product),  # Not RESTful
]
```

### 10. Error Handling

**Requirement**: Use proper error handling

**Checks**:
- ✅ Use custom exception handler
- ✅ Use proper HTTP status codes
- ✅ Use structured error responses
- ✅ Use serializers.ValidationError for validation
- ❌ Using raw exceptions
- ❌ Missing error handling
- ❌ Inconsistent error formats

**Example**:
```python
# ✅ Correct
def validate(self, attrs):
    if attrs.get("name") and attrs.get("description"):
        if attrs["name"].lower() in attrs["description"].lower():
            raise serializers.ValidationError(
                "Product name should not be repeated in description."
            )
    return super().validate(attrs)

# ❌ Incorrect
def validate(self, attrs):
    if attrs.get("name") and attrs.get("description"):
        if attrs["name"].lower() in attrs["description"].lower():
            raise Exception("Validation failed")  # Raw exception
    return super().validate(attrs)
```

## Implementation Guidelines

### 1. Before Creating New API

1. **Check if resource follows REST principles**
2. **Design URL structure using nouns**
3. **Choose appropriate HTTP methods**
4. **Plan authentication and permissions**
5. **Design response format**

### 2. During Development

1. **Use ViewSets for CRUD operations**
2. **Implement proper filtering and pagination**
3. **Use custom actions for special operations**
4. **Follow serializer best practices**
5. **Test with proper authentication**

### 3. Before Deployment

1. **Verify all endpoints follow REST principles**
2. **Test error handling and status codes**
3. **Check performance with large datasets**
4. **Validate API documentation**
5. **Test security measures**

## Violation Examples

### Example 1: Non-RESTful URL
```python
# ❌ Violation
path("products/export/", views.export_products)

# ✅ Fix
# Remove or move to separate service
```

### Example 2: Wrong HTTP Method
```python
# ❌ Violation
@action(detail=True, methods=["post"])
def archive(self, request, pk=None):
    pass

# ✅ Fix
@action(detail=True, methods=["patch"])
def archive(self, request, pk=None):
    pass
```

### Example 3: Missing Pagination
```python
# ❌ Violation
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()  # No pagination

# ✅ Fix
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    pagination_class = CustomPagination
```

### Example 4: Inconsistent Error Format
```python
# ❌ Violation
return Response({"error": "Something went wrong"}, status=400)

# ✅ Fix
    raise DmvnException("Something went wrong.", status_code=400, code="error")
```

## Tools and Validation

### 1. Linting Rules
```yaml
# Add to .pylintrc or similar
restful_api_rules:
  - no_function_based_views_for_crud
  - use_viewsets_for_crud
  - proper_http_methods
  - restful_url_patterns
  - consistent_error_responses
```

### 2. Testing Requirements
```python
# Required test cases
- test_http_method_usage
- test_url_patterns
- test_authentication_required
- test_pagination_applied
- test_error_response_format
- test_custom_actions
```

### 3. Documentation Requirements
```python
# Every ViewSet must have
- Class docstring
- Action docstrings
- Parameter documentation
- Response format documentation
```

## Review Checklist

- [ ] All endpoints use appropriate HTTP methods
- [ ] URL patterns follow REST principles
- [ ] Custom actions are truly necessary
- [ ] Authentication and permissions are properly configured
- [ ] Filtering and pagination are implemented
- [ ] Error responses are consistent
- [ ] Serializers follow best practices
- [ ] ViewSets are used for CRUD operations
- [ ] URL configuration is proper
- [ ] Error handling is comprehensive
- [ ] Tests cover all endpoints
- [ ] Documentation is complete

## Exceptions

This rule may be bypassed in the following cases:

1. **Legacy API compatibility**: When maintaining backward compatibility
2. **Third-party integration**: When integrating with external systems
3. **Performance requirements**: When RESTful approach impacts performance significantly
4. **Special business logic**: When business requirements dictate non-RESTful approach

**Exception Process**:
1. Document the reason for exception
2. Get approval from senior developer
3. Add `# RESTful-API-EXCEPTION: reason` comment
4. Plan migration to RESTful approach

## Maintenance

This rule should be reviewed and updated:

- [ ] Quarterly for new Django/DRF features
- [ ] When project architecture changes
- [ ] Based on team feedback
- [ ] When new security requirements emerge

## References

- [RESTful_API_Guidelines.md](../RESTful_API_Guidelines.md)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [REST API Design Best Practices](https://restfulapi.net/)