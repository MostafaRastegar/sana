# Sana Security Rules

## Authentication
- JWT access/refresh tokens stored in cookies with `bi_` prefix via `utils/cookies.ts`.
- Cookie attributes: `path=/`, `SameSite=Strict` — never relax.
- Token refresh handled transparently by Axios interceptor in `api/client.ts`.
- Auth check: `isAuthenticated()` from `api/client.ts` checks cookie presence.
- NEVER store tokens in localStorage/sessionStorage.
- NEVER expose tokens in URL query params or body logs.

## Authorization
- ALL ViewSets use `ModelActionPermission` from `core.permissions`.
- Standard permission mapping (auto):
  - `list` → `app.view_model`
  - `create` → `app.add_model`
  - `update`/`partial_update` → `app.change_model`
  - `destroy` → `app.delete_model`
  - `retrieve` → `app.view_model`
- Custom actions: define `model_permission_mapping = {...}` on ViewSet.
- `IsAdminUserOrReadOnly` for admin-only write endpoints.
- Superusers bypass all checks; staff users require explicit model permissions.
- Non-staff authenticated users pass permission check; fine-grained access enforced in `get_queryset()` and `perform_create/update/destroy`.
- NEVER hardcode permission strings in view logic; use `get_required_permission()`.

## Input Validation
- ALWAYS use Django ModelForm/model field validation + DRF serializer validation.
- Override `validate_<field>()` on serializers for custom rules; raise `serializers.ValidationError`.
- Call `self.full_clean()` in model `save()` overrides.
- NEVER trust user input — validate type, length, format on every endpoint.
- SQL injection: ALWAYS use Django ORM; never raw SQL with string interpolation.

## Exception Handling
- Business exceptions → `DmvnException("message", status_code=N, code="slug")`.
- NEVER raise DRF exceptions directly (`ValidationError`, `ParseError`, `PermissionDenied`).
- Global handler in `base_exception.py` catches: `DmvnException`, `DjangoValidationError`, DRF `ValidationError`, `PermissionDenied`, `ProtectedError`, unknown → 500.
- Custom status codes: 470=invalid_input, 471=missing_field, 472=invalid_format, 473=invalid_value, 474=already_exists, 475=permission_denied, 476=dependency_exists, 478=sync_failed.

## CSRF & XSS
- Django CSRF middleware active — ensure CSRF cookie is sent for state-changing requests.
- Axios instance in `client.ts` includes `X-CSRFToken` header from cookie.
- NEVER use `@csrf_exempt` on views unless explicitly required and documented.
- All template output auto-escaped by Django/Jinja2 — never use `|safe` or `mark_safe` without review.
- Ant Design components auto-escape — still sanitize any `dangerouslySetInnerHTML` usage.

## CORS
- CORS configured via `django-cors-headers` in settings — restrict to known frontend origins.
- NEVER set `CORS_ALLOW_ALL_ORIGINS=True` in production.
- Only required HTTP methods/allowed headers in CORS config.

## Data Protection
- `ForeignKey` to User: use `get_user_model()`, not direct import.
- `created_by` field on every model tracks ownership.
- `get_queryset()` scopes to user's accessible objects (ownership/permission-based filtering).
- Datasource credentials: stored encrypted; decrypted only on demand in `encryption.py`.
- NEVER log credentials, tokens, or personal data.
- `.env` for secrets; NEVER commit secrets to settings files.

## API Layer (Frontend)
- ALWAYS use pre-configured `client` from `api/client.ts` — never create custom Axios instances.
- Axios interceptor globally handles 401 → redirect to login.
- Response interceptor unwraps `{success: true, data: ...}` envelope.
- Error interceptor shows `notification.error()` — no manual error handling in components.

## File Upload
- Validate file type and size on both client and server.
- Store uploaded files in `media/` directory; serve via configured media URL.
- Never allow direct execution of uploaded files.

## Environment Separation
- `development.py` — debug on, relaxed CORS, SQLite.
- `production.py` — debug off, strict CORS, PostgreSQL, HTTPS enforced.
- `test.py` — separate DB, eager Celery, fast hasher.
- Settings inheritance: base → environment-specific override.