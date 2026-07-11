---
name: restful-api-design
description: RESTful API design standards for DRF — HTTP methods, URL patterns, custom actions, response formats, auth, filtering, serializers, viewset design, error handling.
---

# restful-api-design

RESTful API design standards for DRF: HTTP method semantics, URL naming conventions, custom actions, structured response formats, auth, filtering, serializer rules, viewset design, and error handling.

## Usage

Use this skill when designing new API endpoints, reviewing existing ones, or enforcing REST conventions across the project.

## Steps

1. **HTTP Methods** — `GET` for retrieval (never mutate), `POST` for create, `PUT` for full replace, `PATCH` for partial update, `DELETE` for delete. Custom actions use `PATCH` for state mutations (e.g. archive), not `POST`.

2. **URL Design** — Nouns not verbs (`/api/products/` ✅, `/api/getProducts/` ❌). Plural collections (`/api/products/` ✅). Nested routes: `/api/categories/{id}/products/`. kebab-case for multi-word resources: `/api/order-items/`.

3. **Custom Actions** — Only for non-CRUD operations. Use `@action(detail=True, methods=['patch'], permission_classes=[ModelActionPermission])`.

4. **Response Format** — Success: standard DRF serializer output with pagination envelope. Error: `{"error": {"status_code": int, "code": str, "message": str, "details": [{"field": str, "message": str}]}}`. Always throw `DmvnException`, never raw `Exception` or bare `Response`.

5. **Filtering & Pagination** — `DjangoFilterBackend` + `SearchFilter` + `OrderingFilter` standard triad. `CustomPagination` class — never return unpaginated lists. Default `ordering = ['-created_at']`.

6. **Serializer Rules** — `ModelSerializer` for model data (never plain `Serializer`). Enumerate `fields` explicitly (never `'__all__'`). `read_only_fields` for system-set values. `validate_<field>` for per-field, `validate()` for cross-field.

7. **ViewSet Rules** — `ModelViewSet` for CRUD (never function-based views for CRUD). `ReadOnlyModelViewSet` for read-only resources. Always `select_related` + `prefetch_related`.

8. **Error Handling** — `DmvnException` with `status_code`, `code`, `message`, `details`. Never expose stack traces or internal error details to clients.

**Checklist:**
- [ ] URLs use nouns/plural, no verbs
- [ ] HTTP methods match semantics (PATCH for updates)
- [ ] Custom actions are truly non-CRUD
- [ ] Pagination + filters configured
- [ ] Error responses use structured format
- [ ] Serializers: ModelSerializer, explicit fields
- [ ] ViewSet: select_related + prefetch_related
- [ ] Auth: ModelActionPermission on all endpoints