# Django REST Framework Development Guidelines

## Overview

This document provides actionable development guidelines for building high-quality Django REST Framework applications based on SonarQube best practices. These guidelines are designed to ensure code quality, security, performance, and maintainability.

## Quick Start Checklist

Before starting any new feature or endpoint:

- [ ] Review the relevant Cline rules for the component you're building
- [ ] Plan your implementation following the established patterns
- [ ] Write tests first (TDD approach recommended)
- [ ] Implement security measures and validation
- [ ] Optimize for performance from the start
- [ ] Document your code and API endpoints
- [ ] Run quality checks before committing

## Development Workflow

### 1. Planning Phase

**Before coding:**
1. Review existing models and serializers for similar patterns
2. Check if new models are needed or if existing ones can be extended
3. Plan API endpoints and their permissions
4. Identify potential performance bottlenecks
5. Consider security implications and validation requirements

**Questions to ask:**
- Does this endpoint follow REST conventions?
- What permissions should this endpoint require?
- What data validation is needed?
- How will this endpoint perform with large datasets?
- What error responses should be returned?

### 2. Implementation Phase

**Follow this order:**
1. **Models**: Create or update models with proper validation and relationships
2. **Serializers**: Implement serializers with comprehensive validation
3. **Views**: Create ViewSets with proper permissions and optimization
4. **Tests**: Write comprehensive tests for all components
5. **Documentation**: Add API documentation and inline comments

**Code Review Checklist:**
- [ ] Models follow Django best practices
- [ ] Serializers have proper validation
- [ ] Views use appropriate permissions
- [ ] Database queries are optimized
- [ ] Error handling is comprehensive
- [ ] Tests cover all scenarios
- [ ] Code follows style guidelines

### 3. Quality Assurance Phase

**Run these checks before committing:**
```bash
# Code quality checks
flake8 example/ core/
pylint example/ core/

# Tests and coverage
python manage.py test
coverage run --source='.' manage.py test
coverage report --show-missing

# Security checks
python manage.py check --deploy
```

## Component-Specific Guidelines

### Models

**When creating models:**
1. Use descriptive field names and proper data types
2. Add appropriate database indexes for frequently queried fields
3. Implement custom validation in `clean()` method
4. Define custom permissions in Meta class
5. Use `related_name` for reverse relationships
6. Add proper docstrings

**Example:**
```python
class Product(models.Model):
    """Product model representing items available for sale."""
    
    name = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Product name"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Product price in USD"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        db_index=True,
        help_text="Product category"
    )
    
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('archive_product', 'Can archive product'),
            ('export_product', 'Can export product data'),
        ]
    
    def clean(self):
        """Validate model data."""
        if self.price < 0:
            raise ValidationError(_("Price cannot be negative."))
        return super().clean()
```

### Serializers

**When creating serializers:**
1. Use field-level validation for individual fields
2. Implement cross-field validation in `validate()` method
3. Use `read_only_fields` for computed or sensitive data
4. Exclude sensitive fields from responses
5. Add proper error messages

**Example:**
```python
class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with comprehensive validation."""
    
    category_name = serializers.CharField(
        source='category.name',
        read_only=True,
        help_text="Category name"
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'category', 
            'category_name', 'description', 'in_stock'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate product name."""
        if len(value) < 3:
            raise serializers.ValidationError(
                "Product name must be at least 3 characters long."
            )
        return value
    
    def validate_price(self, value):
        """Validate product price."""
        if value <= 0:
            raise serializers.ValidationError(
                "Price must be greater than zero."
            )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        if attrs.get('name') and attrs.get('description'):
            if attrs['name'].lower() in attrs['description'].lower():
                raise serializers.ValidationError(
                    "Product name should not be repeated in description."
                )
        return super().validate(attrs)
```

### Views

**When creating ViewSets:**
1. Use `ModelActionPermission` for consistent permission mapping
2. Optimize queryset with `select_related()` and `prefetch_related()`
3. Implement proper filtering and search
4. Use custom actions for non-CRUD operations
5. Add appropriate pagination

**Example:**
```python
class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product model with optimized queries and permissions."""
    
    queryset = Product.objects.select_related(
        'category', 'created_by'
    ).prefetch_related('orders')
    
    serializer_class = ProductSerializer
    permission_classes = [ModelActionPermission]
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
    
    # Custom permission mapping for actions
    model_permission_mapping = {
        'archive': 'example.archive_product',
        'export': 'example.export_product',
    }
    
    def perform_create(self, serializer):
        """Set created_by field on creation."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['patch'], permission_classes=[ModelActionPermission])
    def archive(self, request, pk=None):
        """Archive a product (requires archive_product permission)."""
        product = self.get_object()
        
        if not request.user.has_perm('example.archive_product'):
            raise DmvnException(
                "You do not have permission to archive products.",
                status_code=403,
                code="permission_denied",
            )
        
        product.in_stock = False
        product.save()
        
        return Response({
            "message": f'Product "{product.name}" has been archived.'
        })
```

### Tests

**Test structure:**
1. Create separate test files for each component
2. Use descriptive test method names
3. Test both positive and negative scenarios
4. Mock external dependencies
5. Test performance for critical paths

**Example:**
```python
class ProductModelTest(TestCase):
    """Test Product model validation and relationships."""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
    
    def test_product_creation(self):
        """Test that a product can be created with valid data."""
        product = Product.objects.create(
            name='Smartphone',
            price=599.99,
            category=self.category
        )
        self.assertEqual(product.name, 'Smartphone')
        self.assertEqual(product.price, 599.99)
        self.assertEqual(product.category, self.category)
    
    def test_product_validation_negative_price(self):
        """Test that negative prices are rejected."""
        product = Product(
            name='Test Product',
            price=-100.00,  # Invalid
            category=self.category
        )
        with self.assertRaises(ValidationError):
            product.full_clean()
    
    def test_product_relationships(self):
        """Test product-category relationships."""
        product = Product.objects.create(
            name='Laptop',
            price=999.99,
            category=self.category
        )
        self.assertIn(product, self.category.products.all())
```

## Security Guidelines

### Authentication and Authorization

1. **Always use JWT authentication** for stateless APIs
2. **Implement proper permission classes** for each endpoint
3. **Use ModelActionPermission** for consistent permission mapping
4. **Validate user permissions** before sensitive operations
5. **Never expose sensitive data** in API responses

### Input Validation

1. **Validate all input data** at the serializer level
2. **Use Django's built-in validators** for common patterns
3. **Implement custom validation** for business logic
4. **Sanitize user input** before processing
5. **Use parameterized queries** to prevent SQL injection

### Error Handling

1. **Use structured error responses** with appropriate status codes
2. **Never expose internal errors** to clients
3. **Log errors securely** without sensitive data
4. **Use DmvnException** for custom business logic errors
5. **Implement custom exception handler** for consistency

## Performance Guidelines

### Database Optimization

1. **Use select_related()** for ForeignKey relationships
2. **Use prefetch_related()** for ManyToMany relationships
3. **Implement proper database indexes**
4. **Avoid N+1 query problems**
5. **Use pagination** for large datasets

### API Optimization

1. **Implement field selection** for large responses
2. **Use caching** for expensive operations
3. **Optimize serializer performance**
4. **Use streaming responses** for large files
5. **Implement rate limiting** for sensitive endpoints

### Memory Management

1. **Use iterator()** for large querysets
2. **Implement proper garbage collection**
3. **Monitor memory usage** in production
4. **Use appropriate data structures**

## Code Quality Standards

### Style Guidelines

1. **Follow PEP 8** for Python code style
2. **Use meaningful variable names**
3. **Add proper docstrings** to all functions and classes
4. **Keep functions and methods small and focused**
5. **Use type hints** where appropriate

### Testing Standards

1. **Aim for 80%+ code coverage**
2. **Write tests for all new functionality**
3. **Test both positive and negative scenarios**
4. **Use mocking for external dependencies**
5. **Run tests in CI/CD pipeline**

### Documentation Standards

1. **Document all API endpoints** with DRF Spectacular
2. **Add inline comments** for complex logic
3. **Maintain up-to-date README files**
4. **Document breaking changes** in changelog
5. **Use proper commit messages**

## Common Patterns

### Custom Actions

```python
@action(detail=True, methods=['patch'], permission_classes=[ModelActionPermission])
def archive(self, request, pk=None):
    """Archive a resource."""
    instance = self.get_object()
    # Implementation
    return Response({'message': 'Resource archived successfully'})
```

### Custom Filters

```python
class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    
    class Meta:
        model = Product
        fields = ['category', 'in_stock']
```

### Custom Permissions

```python
class CustomPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == 'archive':
            return request.user.has_perm('app.archive_model')
        return super().has_permission(request, view)
```

## Troubleshooting

### Common Issues

1. **N+1 Query Problems**: Use `select_related()` and `prefetch_related()`
2. **Permission Errors**: Check permission classes and user permissions
3. **Validation Errors**: Review serializer validation methods
4. **Performance Issues**: Analyze database queries and implement caching
5. **Authentication Errors**: Verify JWT token configuration

### Debugging Tools

1. **Django Debug Toolbar**: For query analysis
2. **DRF Spectacular**: For API documentation
3. **Coverage.py**: For test coverage analysis
4. **Logging**: For runtime debugging

## Continuous Improvement

### Regular Tasks

1. **Code Reviews**: Review all pull requests for quality
2. **Security Audits**: Regularly review security measures
3. **Performance Monitoring**: Monitor API response times
4. **Test Maintenance**: Keep tests up to date with code changes
5. **Documentation Updates**: Update documentation as code evolves

### Metrics to Track

1. **Code Coverage**: Maintain 80%+ coverage
2. **API Response Times**: Monitor 95th percentile response times
3. **Error Rates**: Track and reduce error rates
4. **Security Vulnerabilities**: Address security issues promptly
5. **Code Quality**: Monitor code quality metrics

## Resources

- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [Django Documentation](https://docs.djangoproject.com/)
- [SonarQube Documentation](https://docs.sonarqube.org/)
- [DRF Spectacular Documentation](https://drf-spectacular.readthedocs.io/)

## Support

For questions or issues related to these guidelines:

1. Check the existing documentation
2. Review similar implementations in the codebase
3. Ask in the development team chat
4. Create an issue for guideline improvements

Remember: These guidelines are living documents. Contribute improvements and updates as you discover better practices!