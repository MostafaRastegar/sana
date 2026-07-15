# Sana Architecture Rules

## Response Format
- ALWAYS use helpers from `backend.core.response`:
  - `success_response(data, message, status=200)` → `{"success": True, "message": ..., "data": ...}`
  - `created_response(data)` → status 201
  - `deleted_response(message)` → status 200
- NEVER use DRF's `Response(...)` directly (except in `base_exception.py`).
- Custom status codes: 470=invalid_input, 471=missing_field, 472=invalid_format, 473=invalid_value, 474=already_exists, 475=permission_denied, 476=dependency_exists, 478=sync_failed.

## Exception Handling
- Business exceptions → ALWAYS use `DmvnException`:
  ```python
  raise DmvnException("message", status_code=400, code="slug")
  ```
- NEVER use DRF's `ValidationError`, `ParseError`, `PermissionDenied` directly.
- The global handler in `base_exception.py` catches: `DmvnException`, `DjangoValidationError`, DRF `ValidationError`, `PermissionDenied`, `ProtectedError`, and unknown → 500.
- Available exception types (via `details`): authentication, authorization, validation, not_found, conflict, business, rate_limit, external, server.

## Permissions
- Primary permission class on all ViewSets: `ModelActionPermission` from `backend.core.permissions`.
- Define `model_permission_mapping = {...}` on ViewSet for custom actions.
- Standard mapping (automatic):
  - `list` → `app.view_model`
  - `create` → `app.add_model`
  - `update`/`partial_update` → `app.change_model`
  - `destroy` → `app.delete_model`
  - `retrieve` → `app.view_model`
- `IsAdminUserOrReadOnly` available for admin-only write.
- NEVER hardcode permission strings in view logic; use `get_required_permission()`.

## Serializer Structure
- Use `TimestampedModelSerializer` from `backend.core.serializers` for models with created_at/updated_at.
- Include `read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']` in Meta.
- Use `verbose_name` for human-readable field labels in responses.
- For M2M relationships: expose via `PrimaryKeyRelatedField` in input, `SerializerMethodField` or nested source in output.

## i18n (Internationalization)
- Translation keys follow: `appname.context.key` (e.g. `alerts.model.name`).
- Shared keys: `app_common.xxx`.
- NEVER hardcode bilingual strings in code; extract to `.po` files under `backend/locale/{lang}/LC_MESSAGES/`.
- Use `gettext_lazy as _` for model fields, `gettext as _` for views/helpers.
- Language detection: `APILanguageDetectionMiddleware` checks URL path → query param → Accept-Language header → default 'fa'.

## Jinja2 / Templates
- Template directory: `backend/templates/`.
- Currently only used for `reports/`; keep template logic minimal.

## Database
- Always use `select_related()` and `prefetch_related()` on ViewSet querysets.
- `db_index=True` on frequently-filtered fields.
- `ordering = ['-created_at']` as default Meta ordering.

## URL Routing
- App-level `urls.py` with `app_name = 'app_name'`.
- Use `SimpleRouter` + `NestedSimpleRouter` for REST endpoints.
- All API endpoints under `/api/{lang}/app_name/`.
- Trailing slash required on all URLs.