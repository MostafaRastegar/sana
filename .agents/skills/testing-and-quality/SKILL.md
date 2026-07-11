---
name: testing_and_code_quality
description: DRF testing patterns — unit/integration/API tests, serializer testing, mocking, coverage, linting, CI integration.
---

# Testing & Code Quality

## When to Use
Use this skill when writing tests, configuring CI, or enforcing code quality.

## Standards

### 1. Test Structure
```
tests/
├── test_models.py
├── test_serializers.py
├── test_views.py
├── test_integration.py
├── fixtures/
└── conftest.py  (shared fixtures/factories)
```
- One file per concern (models, serializers, views)
- Class per model/endpoint, method per scenario
- `APITestCase` for endpoint tests, `TestCase` for model/serializer unit tests

### 2. Model Tests
```python
class ProductModelTest(TestCase):
    def test_validation_negative_price(self):
        product = Product(price=-1, ...)
        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_save_calls_full_clean(self):
        product = Product(price=-1, ...)
        with self.assertRaises(ValidationError):
            product.save()
```
- Test: creation, field constraints, custom clean(), relationships, permissions

### 3. Serializer Tests
```python
class ProductSerializerTest(APITestCase):
    def test_invalid_price(self):
        serializer = ProductSerializer(data={"price": -10, ...})
        self.assertFalse(serializer.is_valid())
        self.assertIn("price", serializer.errors)
```
- Test: valid data, per-field validation, cross-field validation, read-only fields, nested output

### 4. API Tests
```python
class ProductAPITest(APITestCase):
    def test_list_requires_auth(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, 401)

    def test_create_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/products/", data)
        self.assertEqual(response.status_code, 201)
```
- Test: all HTTP methods, auth required, permission checks, pagination, filtering, search, error formats

### 5. Integration Tests
- Complete workflows (create → read → update → delete)
- Error paths (invalid data, missing resources, permission denied)
- Use `TransactionTestCase` for transaction rollback tests

### 6. Mocking
```python
@patch("example.services.send_notification")
def test_notification(self, mock_send):
    mock_send.return_value = True
    result = send_order_notification(order_id=123)
    mock_send.assert_called_once_with(order_id=123)
```
- Mock: external APIs, Celery tasks, expensive operations
- Never mock: ORM queries, serializers, own business logic (test real)

### 7. Coverage Configuration
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
addopts =
    --cov=backend --cov-report=term-missing --cov-report=html
    --cov-fail-under=80
    -v --tb=short
```
- Target: ≥80% coverage
- Exclude: migrations, settings, manage.py, __pycache__, locale, venv

### 8. Linting
```makefile
lint:
    ruff check backend/
    mypy backend/
```
- Ruff for fast linting (flake8 + isort + pyupgrade ruleset)
- mypy for type checking
- Max line length: 88 (black default)

## Checklist
- [ ] Model tests: creation, validation, relationships, clean()
- [ ] Serializer tests: valid/invalid data, read-only fields
- [ ] API tests: every endpoint, auth scenarios, filtering, pagination
- [ ] Integration tests: end-to-end workflow + error paths
- [ ] Mocks used only for external dependencies
- [ ] Coverage ≥80%
- [ ] Ruff + mypy pass in CI