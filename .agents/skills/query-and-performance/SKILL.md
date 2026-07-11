---
name: performance_and_optimization
description: DRF query optimization — select_related/prefetch_related, pagination, caching (Redis), indexing, async tasks (Celery), response compression, memory management.
---

# Query & Performance

## When to Use
Use this skill when optimizing database queries, adding caching, or handling large datasets.

## Standards

### 1. Query Optimization
- `select_related('fk1', 'fk2')` for every ForeignKey/O2O accessed in serializers
- `prefetch_related('m2m', 'reverse_fk_set')` for every ManyToMany/reverse FK
- Apply at class level in `queryset`, extend in `get_queryset()`
- Never iterate a queryset without `select_related` for relationship access

### 2. Pagination
- `CustomPagination` — never return unpaginated lists
- For very large datasets: `CursorPagination` (no count query, stable ordering)
- Page size default: 20, max: 100

### 3. Caching (Redis)
```python
from django.core.cache import cache

stats = cache.get("category_stats")
if stats is None:
    stats = expensive_computation()
    cache.set("category_stats", stats, 60 * 30)  # TTL in seconds
```
- Cache: computed stats, aggregations, reference data (categories, configs)
- Never cache: user-specific data, active records, auth tokens
- View-level: `@method_decorator(cache_page(60*15))` for infrequently-changing list endpoints

### 4. Database Indexing
```python
class Product(models.Model):
    name = models.CharField(db_index=True)
    category = models.ForeignKey(Category, db_index=True)
    created_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "in_stock"]),        # composite
            models.Index(fields=["-created_at"]),                  # descending
        ]
```
- Index: FK fields, frequently-filtered fields, ORDER BY columns, composite for multi-field filters

### 5. Async / Background Tasks
- Celery for: email sending, data exports, report generation, bulk processing
- View returns task ID immediately; client polls for completion
- Always wrap task bodies in try/except with logging

### 6. Response Optimization
- Compact serializers for list views: `ProductListSerializer` with minimal fields
- `StreamingHttpResponse` for CSV/exports (iterator chunk_size=2000)
- GZip middleware for large payloads

### 7. Memory Management
- `iterator(chunk_size=2000)` for large queryset iteration (never `list(queryset)`)
- `TemporaryUploadedFile` for large file uploads
- Monitor memory: <50MB per request on data-heavy endpoints

## Checklist
- [ ] select_related + prefetch_related on every ViewSet
- [ ] Pagination configured (CustomPagination on all list endpoints)
- [ ] Expensive computations cached with TTL
- [ ] Database indexes on FK + frequently-filtered fields
- [ ] Celery tasks for background/async work
- [ ] Compact list serializers used for multi-row responses
- [ ] iterator() used for bulk processing (no list(queryset))