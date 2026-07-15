---
name: query-and-performance
description: DRF query optimization — select_related/prefetch_related, pagination, caching (Redis), indexing, async tasks (Celery), response compression, memory management.
---

# query-and-performance

DRF query optimization patterns: select_related/prefetch_related, pagination, Redis caching, database indexing, Celery async tasks, response compression, and memory management for handling large datasets.

## Usage

Use this skill when optimizing database queries, adding caching, or handling large datasets.

## Steps

1. **Query Optimization** — Apply `select_related('fk1', 'fk2')` for every ForeignKey/O2O and `prefetch_related('m2m', 'reverse_fk_set')` for every ManyToMany/reverse FK accessed in serializers. Apply at class level in `queryset`, extend in `get_queryset()`. Never iterate a queryset without `select_related` for relationship access.

2. **Pagination** — Use `CustomPagination` on all list endpoints. For very large datasets use `CursorPagination` (no count query, stable ordering). Default page size: 10, max: 100. Append `?page_size=N` to adjust per-request.

3. **Caching (Redis)** — Cache computed stats, aggregations, and reference data with `cache.get/set` and TTL. Never cache user-specific data, active records, or auth tokens. Use `@method_decorator(cache_page(60*15))` for infrequently-changing list endpoints.

4. **Database Indexing** — Add `db_index=True` on FK fields and frequently-filtered fields. Use composite indexes and descending indexes via `Meta.indexes` for multi-field filters and ORDER BY columns.

5. **Async / Background Tasks** — Use Celery for email sending, data exports, report generation, and bulk processing. Return task ID immediately; client polls for completion. Always wrap task bodies in try/except with logging.

6. **Response Optimization** — Use compact serializers for list views (`ProductListSerializer` with minimal fields). `StreamingHttpResponse` for CSV/exports (iterator chunk_size=2000). GZip middleware for large payloads.

7. **Memory Management** — Use `iterator(chunk_size=2000)` for large queryset iteration (never `list(queryset)`). Use `TemporaryUploadedFile` for large file uploads. Monitor memory: <50MB per request on data-heavy endpoints.

**Checklist:**
- [ ] select_related + prefetch_related on every ViewSet
- [ ] Pagination configured (CustomPagination on all list endpoints)
- [ ] Expensive computations cached with TTL
- [ ] Database indexes on FK + frequently-filtered fields
- [ ] Celery tasks for background/async work
- [ ] Compact list serializers used for multi-row responses
- [ ] iterator() used for bulk processing (no list(queryset))