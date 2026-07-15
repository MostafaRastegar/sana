---
name: django-crud-patterns
description: Standardized CRUD patterns for Django REST Framework — model viewsets, serializers, action mapping, and bulk operations.
---

# django-crud-patterns

Defines standardized CRUD patterns: ModelViewSet configuration, serializer mapping, custom actions, bulk operations, and URL routing for any Django model via REST Framework.

## Usage

Use this skill when building or extending CRUD endpoints for any Django model via REST Framework.

## Steps

1. **ModelViewSet Configuration** — Use `ModelViewSet` for full CRUD, override `get_queryset()` for filtering, set `permission_classes` per action, use `action` decorator for custom endpoints.

2. **Serializer Mapping** — Separate read/write serializers, use `get_serializer_class()` for conditional mapping, override `perform_create/update` for side effects.

3. **Custom Actions** — Use `@action(detail=True, methods=['post'])` for non-CRUD endpoints (e.g. archive, restore). Return explicit status codes. Set `throttle_classes` per action when rate differs from the view default.

4. **Bulk Operations** — Class-based views or decorators for bulk create/update/delete. Always validate all items before any mutation.

5. **URL Routing** — `DefaultRouter` for standard CRUD, nested routers for parent/child resources, explicit `path()` for custom actions.

**Checklist:**
- [ ] ViewSet uses appropriate queryset with select_related/prefetch_related
- [ ] Serializers validate at field and object level
- [ ] Custom actions have throttle_classes
- [ ] Permissions are set per action, not globally
- [ ] Bulk operations validate before execute