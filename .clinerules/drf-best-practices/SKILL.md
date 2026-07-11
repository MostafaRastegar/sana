---
name: drf-best-practices
description: ViewSet design, serializer validation, exception handling, queryset optimization, schema docs, auth, pagination, and model design for DRF projects.
---

# drf-best-practices

DRF development lifecycle patterns: ViewSet design, serializer validation, exception handling, queryset optimization, schema documentation, auth, pagination, and model design.

## Usage

Use this skill when building or maintaining any DRF viewset, serializer, or endpoint.

## Steps

1. **ViewSet & Permissions** — Use `ModelActionPermission` for consistent action-to-permission mapping. Override `get_queryset()` for scoped/dynamic filters. Custom actions via `@action(detail=True, methods=['patch'])` with explicit `permission_classes`. Always specify `basename` in `router.register()`.

2. **Serializers** — Field validation: `validate_<field>(self, value)` method per field. Cross-field validation: `validate(self, attrs)` with `super().validate(attrs)`. `read_only_fields` for system-set fields (id, created_at, updated_at). NEVER use `fields = '__all__'`. Use `source='related.field'` for nested display values instead of `SerializerMethodField` where possible.

3. **Exception Handling** — Raise `DmvnException` with structured error response `{"error": {"status_code", "code", "message", "details"}}`. Never raise raw `Exception` or Django built-in exceptions from view logic.

4. **Query Optimization** — `select_related('fk1', 'fk2')` for every ForeignKey/O2O. `prefetch_related('m2m', 'reverse_fk_set')` for every ManyToMany/reverse FK. Apply at class level in `queryset`, extend in `get_queryset()`.

5. **API Documentation (DRF Spectacular)** — `@extend_schema` on custom actions for request/response shape. `SPECTACULAR_SETTINGS` with `COMPONENT_SPLIT_REQUEST: True`.

6. **Pagination & Filtering** — `CustomPagination` class for consistent page sizes. `DjangoFilterBackend` + `filters.SearchFilter` + `filters.OrderingFilter` standard triad. Default `ordering = ['-created_at']`.

7. **Model Design** — `related_name` on every ForeignKey. `clean()` for model-level validation, called from `save()` via `self.full_clean()`. Custom permissions in `Meta.permissions`.

**Checklist:**
- [ ] ViewSet has select_related + prefetch_related
- [ ] Serializers enumerate fields explicitly
- [ ] All custom actions use @action with proper methods/permissions
- [ ] Exceptions use DmvnException, not raw Python exceptions
- [ ] Pagination + filter backends configured
- [ ] Model has clean() + full_clean() save override where validation needed
- [ ] Schema annotated with @extend_schema where auto-detection insufficient