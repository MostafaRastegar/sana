---
name: testing_and_code_quality
description: Brief description of what this skill does
---

# testing_and_code_quality

Instructions for the AI agent...

## Usage
# Testing and Code Quality Best Practices

## Overview
This rule defines comprehensive testing and code quality practices for Django REST Framework applications, focusing on unit tests, integration tests, code coverage, and quality metrics.

## Rule Details

### 1. Test Structure and Organization

**Description**: Organize tests in a clear, maintainable structure that follows Django testing conventions.

**Pattern**:
- Use separate test files for models, serializers, views, and utilities
- Follow naming convention: `test_<component>.py`
- Use test classes that inherit from appropriate base classes
- Group related tests with descriptive method names
- Use fixtures and factories for test data

**Example**:
```python
# GOOD - Well-organized test structure
# tests/test_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from example.models import Category, Product

User = get_user_model()

class CategoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_category_creation(self):
        """Test that a category can be created successfully."""
        category = Category.objects.create(
            name='Electronics',
            description='Electronic devices and accessories'
        )
        self.assertEqual(category.name, 'Electronics')
        self.assertTrue(category.id > 0)
    
    def test_category_unique_name(self):
        """Test that category names must be unique."""
        Category.objects.create(name='Electronics')
        with self.assertRaises(Exception):
            Category.objects.create(name='Electronics')

# tests/test_serializers.py
from rest_framework.test import APITestCase
from example.serializers import ProductSerializer

class ProductSerializerTest(APITestCase):
    def test_product_serializer_validation(self):
        """Test product serializer field validation."""
        data = {
            'name': 'Test Product',
            'price': -10,  # Invalid: negative price
            'category': 1
        }
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)

# tests/test_views.py
from rest_framework.test import APITestCase
from rest_framework import status

class ProductAPITest(APITestCase):
    def test_product_list_requires_authentication(self):
        """Test that product list endpoint requires authentication."""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# BAD - Poor test organization
# tests.py (all tests in one file)
class AllTests(TestCase):
    def test_something(self):
        pass
    
    def test_something_else(self):
        pass
```

### 2. Unit Testing Models

**Description**: Write comprehensive unit tests for model methods, validation, and business logic.

**Pattern**:
- Test model creation, validation, and field constraints
- Test custom model methods and properties
- Test model relationships and foreign key constraints
- Test model permissions and custom validation
- Use `TestCase` for database operations

**Example**:
```python
# GOOD - Comprehensive model testing
class ProductModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
    
    def test_product_creation(self):
        """Test basic product creation."""
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
    
    def test_product_clean_method(self):
        """Test custom clean method validation."""
        product = Product(
            name='Test Product',
            price=100.00,
            category=self.category
        )
        product.clean()  # Should not raise exception
        self.assertTrue(True)
    
    def test_product_save_with_validation(self):
        """Test that save() calls full_clean()."""
        product = Product(
            name='Test Product',
            price=-50.00,  # Invalid
            category=self.category
        )
        with self.assertRaises(ValidationError):
            product.save()
    
    def test_product_relationships(self):
        """Test product relationships."""
        product = Product.objects.create(
            name='Laptop',
            price=999.99,
            category=self.category
        )
        # Test reverse relationship
        self.assertIn(product, self.category.products.all())
```

### 3. Testing Serializers

**Description**: Test serializer validation, serialization, and deserialization thoroughly.

**Pattern**:
- Test field-level validation methods
- Test cross-field validation in `validate()` method
- Test serialization of complex objects
- Test deserialization with invalid data
- Test read-only and write-only fields

**Example**:
```python
# GOOD - Comprehensive serializer testing
class ProductSerializerTest(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
        self.valid_data = {
            'name': 'Smartphone',
            'price': 599.99,
            'category': self.category.id,
            'description': 'A great smartphone'
        }
    
    def test_serializer_valid_data(self):
        """Test serialization with valid data."""
        serializer = ProductSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['name'], 'Smartphone')
    
    def test_serializer_invalid_price(self):
        """Test price validation."""
        data = self.valid_data.copy()
        data['price'] = -100.00
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
        self.assertEqual(
            str(serializer.errors['price'][0]),
            'Price must be greater than zero.'
        )
    
    def test_serializer_cross_field_validation(self):
        """Test cross-field validation."""
        data = self.valid_data.copy()
        data['name'] = 'Test'
        data['description'] = 'This is a Test product description'
        serializer = ProductSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
    
    def test_serializer_read_only_fields(self):
        """Test that read-only fields are not writable."""
        data = self.valid_data.copy()
        data['id'] = 999  # Should be ignored
        data['created_at'] = '2023-01-01T00:00:00Z'  # Should be ignored
        serializer = ProductSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        product = serializer.save()
        self.assertNotEqual(product.id, 999)
    
    def test_serializer_nested_serialization(self):
        """Test nested object serialization."""
        product = Product.objects.create(**self.valid_data)
        serializer = ProductSerializer(product)
        data = serializer.data
        self.assertIn('category_name', data)
        self.assertEqual(data['category_name'], self.category.name)
```

### 4. Testing Views and APIs

**Description**: Test API endpoints thoroughly including authentication, permissions, and response formats.

**Pattern**:
- Use `APITestCase` for API endpoint testing
- Test all HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Test authentication and permission requirements
- Test pagination, filtering, and search functionality
- Test error responses and status codes

**Example**:
```python
# GOOD - Comprehensive API testing
class ProductAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Electronics',
            description='Electronic devices'
        )
        self.product = Product.objects.create(
            name='Smartphone',
            price=599.99,
            category=self.category,
            created_by=self.user
        )
    
    def test_product_list_unauthenticated(self):
        """Test that unauthenticated users cannot access product list."""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_product_list_authenticated(self):
        """Test that authenticated users can access product list."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_product_create(self):
        """Test product creation."""
        self.client.force_authenticate(user=self.user)
        data = {
            'name': 'Laptop',
            'price': 1299.99,
            'category': self.category.id,
            'description': 'A powerful laptop'
        }
        response = self.client.post('/api/products/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
    
    def test_product_update_permissions(self):
        """Test that only authorized users can update products."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        self.client.force_authenticate(user=other_user)
        
        data = {'name': 'Updated Name'}
        response = self.client.patch(f'/api/products/{self.product.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_product_filtering(self):
        """Test product filtering by category."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/products/?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_product_search(self):
        """Test product search functionality."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/products/?search=smartphone')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
```

### 5. Integration Testing

**Description**: Test the integration between different components and end-to-end workflows.

**Pattern**:
- Test complete user workflows
- Test database transactions and rollbacks
- Test middleware and authentication flow
- Test error handling across components
- Use `TransactionTestCase` for database transaction testing

**Example**:
```python
# GOOD - Integration testing
class OrderWorkflowTest(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='customer123'
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Smartphone',
            price=599.99,
            category=self.category,
            in_stock=True
        )
    
    def test_complete_order_workflow(self):
        """Test complete order creation and processing workflow."""
        # Create order
        order_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'items': [
                {
                    'product': self.product.id,
                    'quantity': 2,
                    'price': 599.99
                }
            ]
        }
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/orders/', order_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order was created
        order_id = response.data['id']
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.total_amount, 1199.98)
        self.assertEqual(order.items.count(), 1)
        
        # Test order status update
        status_data = {'status': 'processing'}
        response = self.client.patch(f'/api/orders/{order_id}/update_status/', status_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        order.refresh_from_db()
        self.assertEqual(order.status, 'processing')
    
    def test_order_validation_workflow(self):
        """Test order validation and error handling."""
        # Test with invalid product
        order_data = {
            'customer_name': 'John Doe',
            'customer_email': 'john@example.com',
            'items': [
                {
                    'product': 99999,  # Non-existent product
                    'quantity': 1,
                    'price': 100.00
                }
            ]
        }
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/orders/', order_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('items', response.data)
```

### 6. Code Coverage and Quality Metrics

**Description**: Implement comprehensive code coverage tracking and quality metrics.

**Pattern**:
- Use coverage.py for code coverage measurement
- Set minimum coverage thresholds
- Use pylint, flake8, or ruff for code quality
- Integrate with CI/CD pipeline
- Generate coverage reports

**Example**:
```python
# GOOD - Coverage configuration (.coveragerc)
[run]
source = .
omit = 
    */migrations/*
    */venv/*
    */virtualenv/*
    */tests/*
    */test_*
    manage.py
    */settings/*
    */__pycache__/*
    */locale/*
    */node_modules/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov

# GOOD - pytest configuration (pytest.ini)
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = tests.py test_*.py *_tests.py
addopts = 
    --cov=example
    --cov=core
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --tb=short
    -v

# GOOD - Makefile for testing
.PHONY: test test-cov lint coverage clean

test:
	python manage.py test

test-cov:
	python -m pytest --cov=example --cov=core --cov-report=html --cov-report=term-missing

lint:
	flake8 example/ core/ --max-line-length=88 --extend-ignore=E203,W503
	pylint example/ core/ --load-plugins=pylint_django

coverage:
	python -m coverage run --source='.' manage.py test
	python -m coverage html
	python -m coverage report --show-missing

clean:
	rm -rf htmlcov/
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
```

### 7. Mocking and Test Doubles

**Description**: Use appropriate mocking strategies for external dependencies and complex operations.

**Pattern**:
- Use `unittest.mock` for external service mocking
- Mock expensive operations and external APIs
- Use fixtures for test data instead of real database calls when appropriate
- Mock Celery tasks for testing
- Use `patch` decorator for method mocking

**Example**:
```python
# GOOD - Using mocks for external dependencies
from unittest.mock import patch, MagicMock
from django.test import TestCase

class ExternalAPITest(TestCase):
    @patch('example.services.send_notification')
    def test_notification_service(self, mock_send):
        """Test notification service with mocking."""
        mock_send.return_value = True
        
        # Call the method that uses the external service
        result = send_order_notification(order_id=123)
        
        # Verify the mock was called correctly
        mock_send.assert_called_once_with(order_id=123)
        self.assertTrue(result)
    
    @patch('example.tasks.process_large_dataset.delay')
    def test_celery_task_mocking(self, mock_task):
        """Test Celery task with mocking."""
        mock_task.return_value = MagicMock(id='task-123')
        
        result = trigger_data_processing(dataset_id=456)
        
        mock_task.assert_called_once_with(456)
        self.assertEqual(result, 'task-123')
    
    @patch('requests.get')
    def test_external_api_call(self, mock_get):
        """Test external API integration."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': 'success', 'data': []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = fetch_external_data('https://api.example.com/data')
        
        mock_get.assert_called_once_with('https://api.example.com/data')
        self.assertEqual(result['status'], 'success')

# GOOD - Using fixtures for test data
# tests/fixtures/products.json
[
    {
        "model": "example.category",
        "pk": 1,
        "fields": {
            "name": "Electronics",
            "description": "Electronic devices and accessories",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
    },
    {
        "model": "example.product", 
        "pk": 1,
        "fields": {
            "name": "Smartphone",
            "description": "Latest smartphone model",
            "price": "599.99",
            "category": 1,
            "in_stock": true,
            "created_by": null,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
    }
]

# In test class
class ProductFixtureTest(TestCase):
    fixtures = ['products.json']
    
    def test_fixture_data_loaded(self):
        """Test that fixture data is properly loaded."""
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Product.objects.count(), 1)
        
        category = Category.objects.get(name='Electronics')
        product = Product.objects.get(name='Smartphone')
        
        self.assertEqual(product.category, category)
```

### 8. Performance Testing

**Description**: Test application performance under various load conditions.

**Pattern**:
- Use Django's performance testing tools
- Test database query performance
- Test API response times
- Test memory usage with large datasets
- Use load testing tools for stress testing

**Example**:
```python
# GOOD - Performance testing
from django.test import TestCase
from django.test.utils import override_settings
from django.db import connection
from django.core.cache import cache

class PerformanceTest(TestCase):
    def setUp(self):
        # Create test data
        self.categories = []
        for i in range(10):
            category = Category.objects.create(
                name=f'Category {i}',
                description=f'Description for category {i}'
            )
            self.categories.append(category)
        
        # Create products
        for i in range(100):
            Product.objects.create(
                name=f'Product {i}',
                price=100.00 + i,
                category=self.categories[i % 10]
            )
    
    def test_queryset_performance(self):
        """Test queryset performance with optimization."""
        # Clear query log
        connection.queries_log.clear()
        
        # Test optimized queryset
        products = Product.objects.select_related('category').all()
        list(products)  # Force evaluation
        
        # Should have minimal queries
        self.assertLessEqual(len(connection.queries), 2)
    
    def test_api_response_time(self):
        """Test API response time."""
        from django.test import Client
        import time
        
        client = Client()
        start_time = time.time()
        
        response = client.get('/api/products/')
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0)  # Should respond within 1 second
    
    def test_memory_usage(self):
        """Test memory usage with large datasets."""
        import tracemalloc
        
        tracemalloc.start()
        
        # Create large dataset
        products = []
        for i in range(1000):
            products.append(Product(
                name=f'Product {i}',
                price=100.00 + i,
                category=self.categories[i % 10]
            ))
        Product.objects.bulk_create(products)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be reasonable
        self.assertLess(current, 50 * 1024 * 1024)  # Less than 50MB
```

## Implementation Guidelines

1. **Test Pyramid**: Follow the test pyramid (more unit tests, fewer integration tests)
2. **Fast Feedback**: Keep tests fast for quick feedback during development
3. **Isolation**: Ensure tests are isolated and don't depend on each other
4. **Coverage Goals**: Aim for 80%+ code coverage with meaningful tests
5. **Continuous Testing**: Integrate testing into CI/CD pipeline
6. **Test Documentation**: Document test scenarios and expected behavior

## Testing Checklist

- [ ] Unit tests for all models with validation
- [ ] Serializer tests for validation and serialization
- [ ] API endpoint tests for all HTTP methods
- [ ] Authentication and permission tests
- [ ] Integration tests for complete workflows
- [ ] Mock external dependencies appropriately
- [ ] Performance tests for critical paths
- [ ] Code coverage above 80%
- [ ] Linting and code quality checks
- [ ] Tests run in CI/CD pipeline
- [ ] Test documentation is up to date