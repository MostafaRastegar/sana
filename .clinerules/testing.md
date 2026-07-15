# Sana Testing Rules

## Test Framework
- Backend: pytest (not unittest). Config in `pytest.ini` — DJANGO_SETTINGS_MODULE=config.settings.test.
- Frontend: Vitest (configured in `frontend/vite.config.ts`).
- Factories: `factory_boy` for model factories (define in `conftest.py` or `factories.py`).

## Backend Test Structure
- Tests per app in `{app}/tests.py`. Large test files split into `tests/` package.
- Core tests in `core/tests/` directory.
- Conftest at `conftest.py` (project root) for shared fixtures.
- DB tests: always decorate with `@pytest.mark.django_db`.
- API tests: use `rest_framework.test.APIClient`.
- Celery tasks: set `CELERY_TASK_ALWAYS_EAGER=True` in test settings.

## Fixtures (conftest.py)
- `api_client` — unauthenticated APIClient.
- `admin_user` — superuser/staff user for admin tests.
- `auth_client` — APIClient force-authenticated as admin_user.
- `regular_user` — non-staff, non-superuser for permission tests.
- App-specific fixtures: create in app's `conftest.py` or `tests.py`.

## What to Test
- **Models**: `__str__`, `full_clean()` on save, field constraints, unique_together.
- **Views/ViewSets**: CRUD operations, filtering, pagination, custom actions, permission enforcement.
- **Serializers**: validation methods, field serialization/deserialization, edge cases.
- **Services**: business logic, error paths, complex calculations.
- **Celery tasks**: task execution, retry behavior, error handling.
- **Permissions**: test each permission level (anonymous, regular, staff, superuser) for every action.
- **Exception handling**: DmvnException, DRF ValidationError, DjangoValidationError, PermissionDenied, ProtectedError, unexpected errors.

## Test Quality Standards
- Coverage target: >= 40% (configured in pytest.ini).
- Every bug fix: add a test that reproduces the bug before fixing.
- Every new feature: test at least the primary success path and top 2 error paths.
- No hardcoded IDs in tests — use model fixtures with dynamic references.

## Naming Conventions
- Test files: `tests.py` or `test_*.py`.
- Test classes: `Test{Domain}` or `Test{Domain}{Action}` (PascalCase).
- Test functions: `test_{action}_{scenario}` or `test_{feature}_{condition}_expects_{result}`.

## Mocking
- Use `unittest.mock` (Mock, patch) for external services.
- Mock HTTP calls, file I/O, Celery task execution.
- Never mock Django ORM in model/service tests — use real DB with `django_db` marker.
- Mock `requests` calls for external API datasources.

## Frontend Testing
- Component tests: use `@testing-library/react`.
- Store tests: test Zustand stores directly by calling actions and asserting state changes.
- API layer tests: mock Axios `client` responses.
- Type tests: run `tsc --noEmit` to validate TypeScript.

## Running Tests
```bash
# Backend
cd backend && pytest

# Backend with coverage
cd backend && pytest --cov

# Frontend
cd frontend && npx vitest run

# TypeScript check
cd frontend && npx tsc --noEmit

# Full suite
cd backend && pytest && cd ../frontend && npx vitest run