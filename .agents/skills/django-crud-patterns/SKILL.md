---
name: crud_pattern_rule
description: Standardized CRUD patterns for Django REST Framework — model viewsets, serializers, action mapping, and bulk operations.
---

# Django CRUD Patterns

## When to Use
Use this skill when building or extending CRUD endpoints for any Django model via REST Framework.

## Overview
Defines standardized CRUD patterns: ModelViewSet configuration, serializer mapping, custom actions, bulk operations, and URL routing.

## Key Patterns

### 1. ModelViewSet Configuration
- Use `ModelViewSet` for full CRUD
- Override `get_queryset()` for filtering
- Set `permission_classes` per action
- Use `action` decorator for custom endpoints

### 2. Serializer Mapping
- Separate read/write serializers
- Use `get_serializer_class()` for conditional mapping
- Override `perform_create/update` for side effects

### 3. Custom Actions
```python
@action(detail=True, methods=['post'])
def archive(self, request, pk=None):
    obj = self.get_object()
    obj.is_archived = True
    obj.save()
    return Response(status=204)
```

### 4. Bulk Operations
Class-based views or decorators for bulk create/update/delete. Always validate all items before any mutation.

### 5. URL Routing
- DefaultRouter for standard CRUD
- Nested routers for parent/child resources
- Explicit path() for custom actions

## Checklist
- [ ] ViewSet uses appropriate queryset with select_related/prefetch_related
- [ ] Serializers validate at field and object level
- [ ] Custom actions have throttle_classes
- [ ] Permissions are set per action, not globally
- [ ] Bulk operations validate before execute