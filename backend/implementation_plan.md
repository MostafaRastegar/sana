# Implementation Plan

Comprehensive test suite for the Sana backend. Cover core app (permissions, middleware, exception handling, validators, pagination), datasources (connectors, import CSV, sync, CRUD + custom actions), charts (preview, drill-down, export, bulk-delete), and dashboards (permissions, public sharing, layout). pytest with `:memory:` SQLite, mock external calls. Build incrementally on existing test structure — no framework changes.

[Types]

No new type definitions. Use existing Django models, DRF serializers, and pytest fixtures. Add shared test utility types as needed (e.g., factory helpers).

[Files]

New test files to create, existing files to modify.

**New files:**
- `backend/alerts/tests.py` — Tests for alert services, models, serializers, views
- `backend/charts/tests.py` — Tests for chart CRUD, preview, drill_down, data, export, bulk_delete
- `backend/datasources/tests.py` — Tests for datasource CRUD, test/sync/logs/csv_jobs/create_dataset/import_csv/records actions, models, serializers, connectors
- `backend/core/tests/__init__.py` — Make core tests a proper package
- `backend/core/tests/test_permissions.py` — Tests for ModelActionPermission, IsAdminOrReadOnly
- `backend/core/tests/test_middleware.py` — Tests for custom middleware (e.g., error handling, request timing)
- `backend/core/tests/test_exceptions.py` — Tests for DmvnException, custom exception handler
- `backend/core/tests/test_validators.py` — Tests for core/utils/validators.py
- `backend/core/tests/test_pagination.py` — Tests for CustomPagination
- `backend/dashboards/tests.py` — **Replace** with expanded tests: permission checks, public sharing, filter CRUD, layout update edge cases

**Modified files:**
- None (all new tests in their own files; no production code changes needed)
- `backend/conftest.py` — New shared pytest conftest with common fixtures (authenticated client, admin user, test data)

**No files deleted or moved.**
**Configuration:** Update `pyproject.toml` `[tool.pytest.ini_options]` to use `DJANGO_SETTINGS_MODULE = "config.settings.test"` (currently points to development; test settings have `:memory:` DB and eager Celery).

[Functions]

**New test functions** — each per test file:

### `backend/conftest.py`
- `pytest_configure()` — Force test settings
- `api_client()` — Returns unauthenticated APIClient
- `auth_client()` — Returns authenticated APIClient (admin user)
- `admin_user()` — Creates/DJ admin user
- `regular_user()` — Creates non-admin user
- `test_db()` — Provide test database access

### `backend/core/tests/test_permissions.py`
- `test_admin_user_can_write()` — Admin passes POST/PUT/DELETE
- `test_readonly_user_can_read()` — Non-admin can GET
- `test_readonly_user_cannot_write()` — Non-admin gets 403 on POST
- `test_unauthenticated_user_blocked()` — No auth → 401

### `backend/core/tests/test_middleware.py`
- `test_unauthenticated_request()` — Verify middleware passes through
- `test_request_id_added()` — Check X-Request-Id if implemented
- `test_error_handler_catches_exception()` — Exception → proper error response

### `backend/core/tests/test_exceptions.py`
- `test_dmvnexception_status_code()` — DmvnException returns custom status
- `test_dmvnexception_default_code()` — Default error code present
- `test_custom_exception_handler()` — DRF exception → consistent format

### `backend/core/tests/test_validators.py`
- `test_valid_sql_valid()` — Valid SQL passes
- `test_invalid_sql_rejected()` — Malicious/DDL SQL rejected
- `test_empty_string_rejected()` — Empty → validation error

### `backend/core/tests/test_pagination.py`
- `test_default_page_size()` — Default page size applied
- `test_custom_page_size()` — Custom page param works
- `test_max_page_size_enforced()` — Can't exceed max

### `backend/datasources/tests.py`
- `test_create_datasource()` — POST with valid data → 201
- `test_create_datasource_invalid()` — Missing fields → 400
- `test_list_datasources()` — GET → paginated list
- `test_retrieve_datasource()` — GET detail by ID
- `test_update_datasource()` — PUT update
- `test_delete_datasource()` — DELETE → 204
- `test_filter_by_source_type()` — Filter param works
- `test_search_datasource_by_name()` — Search works
- `test_test_connection_success()` — Mock test_connection → success response
- `test_test_connection_failure()` — Mock test_connection → 400
- `test_sync_data()` — Mock sync_data → success
- `test_sync_data_failure()` — Mock sync_data → 500
- `test_sync_sets_status_syncing()` — Verify status change
- `test_get_logs()` — Logs endpoint returns sync logs
- `test_get_csv_jobs()` — CSV jobs endpoint
- `test_create_dataset()` — create_dataset action with mock
- `test_create_dataset_no_columns()` — No columns → sync then fail gracefully
- `test_import_csv_missing_file()` — 400 without file
- `test_import_csv_success()` — Mock sync → 201
- `test_import_csv_detail()` — Detail endpoint variant
- `test_import_csv_source_not_found()` — non-detail with bad source_id → 404
- `test_records_endpoint()` — GET records with mocked data
- `test_records_auto_sync_csv()` — Empty CSV triggers auto-sync

### `backend/charts/tests.py`
- `test_create_chart_basic()` — POST chart → 201
- `test_create_chart_all_types()` — Each chart type accepted
- `test_list_charts()` — GET → paginated list
- `test_retrieve_chart()` — GET detail
- `test_update_chart()` — PUT update
- `test_delete_chart()` — DELETE → 204
- `test_bulk_delete()` — POST bulk_delete → multiple removed
- `test_preview_with_query()` — POST preview with SQL → mocked result
- `test_preview_invalid_query()` — Bad SQL → 400
- `test_drill_down()` — GET drill_down with dimension/value
- `test_data_endpoint()` — GET data returns chart data
- `test_export_png()` — GET export/png
- `test_delete_non_existent()` — 404 on bad ID
- `test_filter_by_type()` — Filter by chart_type
- `test_search_by_name()` — Search by name

### `backend/dashboards/tests.py`
- **Keep existing tests (create, list, update_layout, delete)**
- `test_permission_denied_for_public_read()` — Unauthenticated cannot read private dashboard
- `test_public_dashboard_readable_by_anyone()` — is_public=True → anyone can GET
- `test_public_dashboard_still_protected_for_write()` — is_public still blocks write
- `test_create_dashboard_permission()` — Specific permission check
- `test_create_dashboard_filter()` — Filter CRUD
- `test_update_layout_invalid_json()` — Bad layout → 400
- `test_filter_dashboard_by_name()` — Search/filter by name

### `backend/alerts/tests.py`
- `test_create_alert()` — POST → 201
- `test_list_alerts()` — GET list
- `test_evaluate_threshold_breach()` — Condition met → status OK
- `test_evaluate_threshold_no_breach()` — Condition not met
- `test_evaluate_comparison_operators()` — gt/lt/gte/lte/eq/ne
- `test_disable_alert()` — Toggle active=False
- `test_check_alert_mock_notification()` — Mock _send_notifications
- `test_alert_str()` — Model string representation

### No modified functions in production code.

[Classes]

**No new production classes.** Only test classes:

- `backend/core/tests/test_permissions.py`:
  - `TestModelActionPermission`
  - `TestIsAdminOrReadOnly`
- `backend/core/tests/test_middleware.py`:
  - `TestErrorMiddleware`
  - `TestRequestTimingMiddleware`
- `backend/core/tests/test_exceptions.py`:
  - `TestDmvnException`
  - `TestCustomExceptionHandler`
- `backend/core/tests/test_validators.py`:
  - `TestSQLValidator`
  - `TestGeneralValidators`
- `backend/core/tests/test_pagination.py`:
  - `TestCustomPagination`
- `backend/datasources/tests.py`:
  - `TestDataSourceModel`
  - `TestDataSourceSerializer`
  - `TestDataSourceViewSet` (CRUD + custom actions)
  - `TestConnectorFunctions` (mocked)
  - `TestCSVImport` (mocked file + sync)
- `backend/charts/tests.py`:
  - `TestChartModel`
  - `TestChartSerializer`
  - `TestChartViewSet` (CRUD + preview/drill-down/data/export/bulk_delete)
- `backend/dashboards/tests.py`:
  - Expand `DashboardAPITest` class
  - Add `TestDashboardPermissions` (public/private)
  - Add `TestDashboardFilter`
- `backend/alerts/tests.py`:
  - `TestAlertModel`
  - `TestAlertSerializer`
  - `TestAlertService` (evaluate_condition, check_alert with mocks)
  - `TestAlertViewSet`

**No classes removed.**

[Dependencies]

**No new dependencies.** pytest, pytest-django, pytest-cov already in `pyproject.toml [project.optional-dependencies] test`. Install before running:

```
pip install -e ".[test]"
```

[Testing]

pytest-based tests with Django TestCase transaction semantics, in-memory SQLite database (`config.settings.test`). Use `unittest.mock` for external calls (connectors, notifications). Target coverage floor: 40% (existing setting in pyproject.toml). Focus on critical paths: auth/permissions, CRUD operations, datasource sync/import, chart preview/export, dashboard sharing.

[Implementation Order]

1. Update `pyproject.toml` to use test settings (DJANGO_SETTINGS_MODULE = config.settings.test)
2. Create `backend/conftest.py` with shared fixtures (api_client, auth_client, admin_user, regular_user)
3. Write `backend/core/tests/__init__.py` and core unit tests (permissions, middleware, exceptions, validators, pagination)
4. Write `backend/datasources/tests.py` — models, serializers, viewset CRUD + custom actions (test, sync, import_csv, records) with mocked connectors
5. Write `backend/charts/tests.py` — models, serializers, viewset CRUD + preview/drill-down/data/export/bulk_delete
6. Expand `backend/dashboards/tests.py` — add permission, public sharing, filter tests
7. Write `backend/alerts/tests.py` — models, serializers, services (evaluate_condition, check_alert mocked), viewset CRUD
8. Run full test suite, verify coverage floor, fix any regressions