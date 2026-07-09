---
name: performance_and_optimization
description: Brief description of what this skill does
---

# Performance and Optimization Best Practices

## Overview
This rule defines performance optimization practices for Django REST Framework applications, focusing on database queries, caching, serialization, and API response optimization.

## Rule Details

### 1. Database Query Optimization

**Description**: Optimize database queries to prevent N+1 problems and reduce database load.

**Pattern**:
- Use `select_related()` for ForeignKey and OneToOneField relationships
- Use `prefetch_related()` for ManyToManyField and reverse ForeignKey relationships
- Implement custom `get_queryset()` methods for filtering
- Use database indexes for frequently queried fields
- Avoid using `count()` on large querysets

**Example**:
```python
# GOOD - Optimized queryset
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related(
        'category', 'created_by'
    ).prefetch_related('orders__items__product')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

# BAD - N+1 query problem
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()  # No optimization
    
    def list(self, request):
        products = self.get_queryset()
        # This will cause N+1 queries for category and created_by
        data = []
        for product in products:
            data.append({
                'name': product.name,
                'category': product.category.name,  # Additional query
                'created_by': product.created_by.username,  # Additional query
            })
        return Response(data)
```

### 2. Pagination and Large Dataset Handling

**Description**: Implement proper pagination to handle large datasets efficiently.

**Pattern**:
- Use custom pagination classes with appropriate page sizes
- Implement cursor-based pagination for large datasets
- Use `count()` optimization for total counts
- Implement lazy loading for expensive computations

**Example**:
```python
# GOOD - Custom pagination with optimization
class LargeDatasetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        # Optimize count for large datasets
        total_count = self.page.paginator.count
        return Response({
            'count': total_count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            'total_pages': self.page.paginator.num_pages,
        })

# GOOD - Cursor pagination for large datasets
class CursorPagination(CursorPagination):
    page_size = 50
    ordering = '-created_at'
    page_size_query_param = 'page_size'
    max_page_size = 200

# BAD - No pagination
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()  # Will load all records
```

### 3. Serializer Optimization

**Description**: Optimize serializers to reduce serialization overhead and improve response times.

**Pattern**:
- Use `to_representation()` for computed fields instead of properties
- Implement selective field serialization with `fields` parameter
- Use `SerializerMethodField` for complex computed fields
- Cache expensive computations in serializers
- Use `PrimaryKeyRelatedField` for write-only relationships

**Example**:
```python
# GOOD - Optimized serializer
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'category_name', 'discounted_price']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_discounted_price(self, obj):
        # Cache expensive computation
        if not hasattr(self, '_discount_cache'):
            self._discount_cache = {}
        if obj.id not in self._discount_cache:
            self._discount_cache[obj.id] = round(obj.price * 0.9, 2)
        return self._discount_cache[obj.id]

# BAD - Expensive property access
class ProductSerializer(serializers.ModelSerializer):
    @property
    def discounted_price(self):
        # This will be called for every instance
        return round(self.instance.price * 0.9, 2)
    
    class Meta:
        model = Product
        fields = '__all__'
```

### 4. Caching Strategies

**Description**: Implement appropriate caching strategies to reduce database and computation overhead.

**Pattern**:
- Use Redis for session and cache storage
- Implement view-level caching for expensive operations
- Use cache invalidation strategies
- Cache serializer results for frequently accessed data
- Use cache headers for HTTP caching

**Example**:
```python
# GOOD - View-level caching
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class ProductViewSet(viewsets.ModelViewSet):
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def list(self, request):
        return super().list(request)
    
    @method_decorator(cache_page(60 * 60))  # Cache for 1 hour
    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk)

# GOOD - Custom caching for expensive operations
class CategoryViewSet(viewsets.ModelViewSet):
    def get_stats(self):
        cache_key = 'category_stats'
        stats = cache.get(cache_key)
        if stats is None:
            stats = {
                'total_categories': self.get_queryset().count(),
                'categories_with_products': self.get_queryset()
                .filter(products__isnull=False)
                .distinct()
                .count(),
            }
            cache.set(cache_key, stats, 60 * 30)  # Cache for 30 minutes
        return stats

# BAD - No caching for expensive operations
class CategoryViewSet(viewsets.ModelViewSet):
    def get_stats(self):
        # This will hit the database every time
        return {
            'total_categories': self.get_queryset().count(),
            'categories_with_products': self.get_queryset()
            .filter(products__isnull=False)
            .distinct()
            .count(),
        }
```

### 5. Database Indexing

**Description**: Implement proper database indexing for frequently queried fields.

**Pattern**:
- Add indexes for fields used in WHERE, ORDER BY, and JOIN clauses
- Use composite indexes for multi-field queries
- Add indexes for foreign key fields
- Use partial indexes for filtered queries
- Monitor query performance with Django Debug Toolbar

**Example**:
```python
# GOOD - Model with proper indexing
class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        db_index=True,  # Index foreign key
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    in_stock = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['category', 'in_stock']),  # Composite index
            models.Index(fields=['-created_at']),  # Descending index for ordering
            models.Index(fields=['name'], name='product_name_idx'),
        ]

# BAD - No indexing
class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    in_stock = models.BooleanField(default=True)
```

### 6. Asynchronous Operations

**Description**: Use asynchronous operations for I/O-bound tasks to improve performance.

**Pattern**:
- Use Celery for background tasks
- Implement async views for long-running operations
- Use async database operations when possible
- Implement proper error handling for async tasks

**Example**:
```python
# GOOD - Celery task for background processing
from celery import shared_task

@shared_task
def process_large_dataset(dataset_id):
    """Process large dataset in background."""
    try:
        dataset = Dataset.objects.get(id=dataset_id)
        # Expensive processing
        result = expensive_operation(dataset)
        dataset.status = 'processed'
        dataset.save()
        return result
    except Exception as e:
        # Proper error handling
        logger.error(f"Error processing dataset {dataset_id}: {e}")
        raise

# GOOD - Async view for long-running operations
import asyncio
from django.http import JsonResponse

async def async_operation_view(request):
    """Handle long-running operations asynchronously."""
    if request.method == 'POST':
        # Start background task
        task = asyncio.create_task(process_data(request.POST))
        task_id = await task
        return JsonResponse({'task_id': task_id})
    
async def process_data(data):
    """Async data processing."""
    await asyncio.sleep(1)  # Simulate async operation
    return {'status': 'completed'}

# BAD - Synchronous long-running operation
def sync_operation_view(request):
    if request.method == 'POST':
        # This will block the request
        result = expensive_operation(request.POST)
        return JsonResponse(result)
```

### 7. API Response Optimization

**Description**: Optimize API responses to reduce payload size and improve transfer speed.

**Pattern**:
- Use field selection to return only necessary data
- Implement compression for large responses
- Use streaming responses for large datasets
- Optimize JSON serialization
- Implement proper HTTP caching headers

**Example**:
```python
# GOOD - Field selection in serializer
class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category_name']  # Only necessary fields
    
    category_name = serializers.CharField(source='category.name', read_only=True)

# GOOD - Streaming response for large datasets
from django.http import StreamingHttpResponse
import csv

def export_products_csv(request):
    """Stream large CSV export."""
    def generate():
        yield ','.join(['ID', 'Name', 'Price', 'Category']) + '\n'
        for product in Product.objects.all().iterator(chunk_size=2000):
            yield f"{product.id},{product.name},{product.price},{product.category.name}\n"
    
    response = StreamingHttpResponse(generate(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    return response

# BAD - Large response without optimization
class ProductViewSet(viewsets.ModelViewSet):
    def list(self, request):
        # Returns all fields for all products
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
```

### 8. Connection Pooling

**Description**: Implement database connection pooling to handle concurrent requests efficiently.

**Pattern**:
- Use connection pooling for database connections
- Configure appropriate pool sizes
- Implement connection reuse
- Monitor connection usage

**Example**:
```python
# GOOD - Database configuration with pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydatabase',
        'USER': 'mydatabaseuser',
        'PASSWORD': 'mypassword',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'MAX_CONNS': 20,  # Maximum connections
        }
    }
}

# GOOD - Redis configuration with pooling
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        }
    }
}

# BAD - No connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'CONN_MAX_AGE': 0,  # No pooling
    }
}
```

### 9. Query Optimization Tools

**Description**: Use Django's built-in tools to identify and fix performance issues.

**Pattern**:
- Use Django Debug Toolbar for query analysis
- Implement query logging in development
- Use `select_related()` and `prefetch_related()` appropriately
- Monitor slow queries and optimize them
- Use `explain()` for complex queries

**Example**:
```python
# GOOD - Development settings with query logging
if DEBUG:
    LOGGING = {
        'version': 1,
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'filters': ['require_debug_true'],
                'class': 'logging.StreamHandler',
            }
        },
        'loggers': {
            'django.db.backends': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            }
        }
    }

# GOOD - Using explain for complex queries
def analyze_query():
    queryset = Product.objects.filter(
        category__name='Electronics',
        price__gt=100
    ).select_related('category')
    
    # Analyze query execution plan
    print(queryset.explain())

# BAD - No query analysis
def bad_query():
    products = Product.objects.filter(
        category__name='Electronics',
        price__gt=100
    )  # No optimization
    return list(products)
```

### 10. Memory Management

**Description**: Implement proper memory management to prevent memory leaks and optimize resource usage.

**Pattern**:
- Use `iterator()` for large querysets
- Implement proper garbage collection
- Use streaming for large file operations
- Monitor memory usage in production
- Use appropriate data structures

**Example**:
```python
# GOOD - Memory-efficient queryset iteration
def process_large_queryset():
    for product in Product.objects.all().iterator(chunk_size=2000):
        # Process each product without loading all into memory
        process_product(product)

# GOOD - Streaming file upload
from django.core.files.uploadedfile import TemporaryUploadedFile

def handle_large_file_upload(file):
    """Handle large file uploads efficiently."""
    if isinstance(file, TemporaryUploadedFile):
        # File is already stored temporarily
        process_file(file.temporary_file_path())
    else:
        # Stream processing for memory efficiency
        with open('/tmp/uploaded_file', 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        process_file('/tmp/uploaded_file')

# BAD - Loading large queryset into memory
def bad_memory_usage():
    products = list(Product.objects.all())  # Loads all into memory
    for product in products:
        process_product(product)
```

## Implementation Guidelines

1. **Profile First**: Always measure performance before optimizing
2. **Database First**: Optimize database queries before application code
3. **Cache Strategically**: Use caching for expensive, frequently accessed data
4. **Monitor Continuously**: Use monitoring tools to track performance
5. **Scale Horizontally**: Consider horizontal scaling for high traffic
6. **Use CDNs**: Implement CDNs for static content delivery

## Performance Checklist

- [ ] Database queries use `select_related()` and `prefetch_related()`
- [ ] Proper pagination is implemented for large datasets
- [ ] Serializers are optimized for performance
- [ ] Caching is implemented for expensive operations
- [ ] Database indexes are properly configured
- [ ] Asynchronous operations are used for I/O-bound tasks
- [ ] API responses are optimized for size
- [ ] Connection pooling is configured
- [ ] Query performance is monitored and analyzed
- [ ] Memory usage is optimized for large datasets
- [ ] Production monitoring is in place