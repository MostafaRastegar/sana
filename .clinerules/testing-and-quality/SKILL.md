---
name: testing-and-quality
description: DRF testing patterns — unit/integration/API tests, serializer testing, mocking, coverage, linting, CI integration.
---

# testing-and-quality

DRF testing and code quality patterns: test structure, model/serializer/API/integration tests, mocking, coverage configuration, linting with Ruff and mypy, and CI integration.

## Usage

Use this skill when writing tests, configuring CI, or enforcing code quality.

## Steps

1. **Test Structure** — Organize tests in `tests/` directory with one file per concern (`test_models.py`, `test_serializers.py`, `test_views.py`, `test_integration.py`), plus `fixtures/` and `conftest.py` for shared fixtures. Use `APITestCase` for endpoint tests, `TestCase` for model/serializer unit tests.

2. **Model Tests** — Test creation, field constraints, custom `clean()`, relationships, and permissions. Use `self.assertRaises(ValidationError)` for invalid scenarios.

3. **Serializer Tests** — Test valid data, per-field validation, cross-field validation, read-only fields, and nested output. Use `self.assertFalse(serializer.is_valid())` for invalid cases.

4. **API Tests** — Test all HTTP methods, auth required, permission checks, pagination, filtering, search, and error formats. Use `self.client.force_authenticate()` for authenticated scenarios.

5. **Integration Tests** — Complete workflows (create → read → update → delete). Error paths (invalid data, missing resources, permission denied). Use `TransactionTestCase` for transaction rollback tests.

6. **Mocking** — Mock external APIs, Celery tasks, and expensive operations. Never mock ORM queries, serializers, or own business logic — test them real.

7. **Coverage** — Target ≥80% coverage. Use `--cov=backend --cov-report=term-missing --cov-report=html --cov-fail-under=80`. Exclude migrations, settings, manage.py, __pycache__, locale, venv.

8. **Linting** — Ruff for fast linting (flake8 + isort + pyupgrade ruleset). mypy for type checking. Max line length: 88 (black default).

**Checklist:**
- [ ] Model tests: creation, validation, relationships, clean()
- [ ] Serializer tests: valid/invalid data, read-only fields
- [ ] API tests: every endpoint, auth scenarios, filtering, pagination
- [ ] Integration tests: end-to-end workflow + error paths
- [ ] Mocks used only for external dependencies
- [ ] Coverage ≥80%
- [ ] Ruff + mypy pass in CI