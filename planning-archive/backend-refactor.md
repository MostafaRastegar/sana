# Implementation Plan

Standardize all DRF viewsets and function-based views across the `datasources`, `charts`, `datasets`, `dashboards`, `alerts`, `reports`, and `query` apps to follow the consistent error handling and response pattern demonstrated in the example `ProductViewSet` — using `DmvnException` for all error cases, `create_error_response` for non-exception responses, proper `ModelActionPermission` with `model_permission_mapping`, `CustomPagination`, and standard filter backend setup.

The current codebase has a mature exception handling system (`core.base_exception.DmvnException`, `custom_exception_handler`, `create_error_response`) already registered in `REST_FRAMEWORK.EXCEPTION_HANDLER`. However, many views bypass this infrastructure by returning raw error dicts inline (e.g. `datasources/views.py` has ~10 places that manually build `{"error": {"code": ..., "message": ..., "details": []}}`). Others miss `ModelActionPermission`, `CustomPagination`, or `model_permission_mapping`. This plan refactors every view to use the canonical pattern consistently.

[Types]

No new types, enums, or data structures needed. The existing `DmvnException`, `create_error_response`, `ModelActionPermission`, and `CustomPagination` are sufficient.

[Files]

Seven existing view files will be modified. No new files, no deletions.

Modified files (all in `backend/`):
1. `backend/datasources/views.py` — 6 actions + 1 private method return raw error dicts instead of raising `DmvnException`. Missing `ModelActionPermission`, `CustomPagination`, `DjangoFilterBackend` in filter_backends, and `model_permission_mapping`. `perform_create` silent-fails instead of using `DmvnException`. Request validation (missing fields, not found) done via manual return instead of `DmvnException`.

2. `backend/charts/views.py` — `drill_down` action returns raw `{"error": ...}` dict for missing params and not-found chart. `perform_create` missing permission field.

3. `backend/datasets/views.py` — `from_datasource` action catches exceptions manually instead of letting `DmvnException` propagate. `ModelActionPermission` not used on the action.

4. `backend/dashboards/views.py` — `layout`, `filters`, `render`, `permissions`, `instantiate` actions already use `DmvnException` correctly. `perform_update`/`perform_destroy` override pattern is good. Minor: `UserSearchView.list` returns empty dict for short query instead of informing.

5. `backend/alerts/views.py` — Already follows pattern well. Minor: `check_now` exception handling wraps in `DmvnException` — good. `toggle` returns serializer data — good. `stats` returns dict — acceptable.

6. `backend/reports/views.py` — `preview`, `download`, `trigger_now`, `history` actions catch exceptions and return raw `{"status": "error", "message": str(e)}` instead of raising `DmvnException`.

7. `backend/query/views.py` — Already follows pattern well. No changes needed.

[Functions]

No new functions. No removals.

Modified functions/methods:
- `DataSourceViewSet.perform_create` — add proper error context
- `DataSourceViewSet.test` — replace manual error response with DmvnException
- `DataSourceViewSet.sync` — replace manual error response with DmvnException
- `DataSourceViewSet.logs` — no change needed (returns serializer data)
- `DataSourceViewSet.csv_jobs` — no change needed
- `DataSourceViewSet.create_dataset` — replace manual error dicts with DmvnException
- `DataSourceViewSet._handle_csv_import` — replace ~6 manual error dict returns with DmvnException raises
- `DataSourceViewSet.import_csv` — replace manual error dict returns with DmvnException
- `DataSourceViewSet.import_csv_detail` — no change needed (delegates to _handle_csv_import)
- `DataSourceViewSet.records` — wraps raw data in Response, acceptable
- `ChartViewSet.drill_down` — replace 2 raw error dict returns with DmvnException
- `ScheduledReportViewSet.preview` — replace raw error dict with DmvnException
- `ScheduledReportViewSet.download` — replace raw error dict with DmvnException
- `ScheduledReportViewSet.trigger_now` — replace raw error dict with DmvnException

[Classes]

No new classes. No removals.

Modified classes:
- `DataSourceViewSet` — add `permission_classes = [ModelActionPermission]`, `pagination_class = CustomPagination`, `filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]`, `model_permission_mapping`, refactor all error responses to use `DmvnException`
- `ChartViewSet` — refactor `drill_down` error responses, add `model_permission_mapping`
- `DatasetViewSet` — refactor `from_datasource` to let DmvnException propagate naturally
- `ScheduledReportViewSet` — refactor `preview`, `download`, `trigger_now` to use `DmvnException` instead of raw error dicts

[Dependencies]

No new packages, no version changes.

[Testing]

Run existing test suite after each file change to catch regressions. Since no new functionality is added — only error handling consistency — the existing tests should pass without modification, provided test assertions match the new error response shape. For `datasources` views this may require test updates where assertions check for specific error dict formats.

[Implementation Order]

1. `datasources/views.py` — most changes, biggest deviation from the pattern
2. `reports/views.py` — 3 actions returning raw error dicts
3. `charts/views.py` — 2 raw error dicts in `drill_down`
4. `datasets/views.py` — minor refactor in `from_datasource`
5. Run full test suite to verify no regressions