# Implementation Plan

[Overview]
Standardize error handling and success response patterns across all BI dashboard viewsets.

The project uses `core/base_exception.py` for error handling with `DmvnException` and `custom_exception_handler`, but success responses are inconsistent — some views return inline dicts, raw DRF errors, or unformatted serializer data. Custom actions like `check_now`, `stats`, `records`, `execute_query` construct ad-hoc response dicts. The goal is to create a lightweight `core/response.py` helper and apply it uniformly, while fixing places like `dashboards/views.py:244` where `Response(serializer.errors, ...)` bypasses the centralized exception handler. Responses should either use the standard DRF pattern (`Response(serializer.data)`) or a simple `{"success": True, "message": …, "data": …}` wrapper for custom actions.

[Types]  
No new types, enums, or interfaces defined.

All changes are to existing Python files — no type system modifications required. The response helper returns plain dicts compatible with DRF `Response()`.

[Files]
Create one file, modify eight.

**New files:**
- `backend/core/response.py` — lightweight success response helpers: `success_response(data, message=None, status=200)`, `created_response(data)`, `deleted_response(message="Deleted successfully")`. Each returns a plain dict ready for `Response(...)`.

**Modified files — error-handling fix:**
- `backend/dashboards/views.py` line 244 — replace `Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)` with raising `DmvnException` so the centralized `custom_exception_handler` formats the error response consistently.

**Modified files — standardize success responses:**
- `backend/alerts/views.py` — `check_now` (69-73), `history` (90), `stats` (109-113) → use `success_response(data, message)` and `created_response()`.
- `backend/charts/views.py` — `data` (228), `drill_down` (352, 377) → wrap in `success_response`.
- `backend/datasets/views.py` — `list_tables` (33), `detect_columns` (67) → wrap in `success_response`.
- `backend/datasources/views.py` — `test` (70), `sync` (86), `records` (238-242) → use `success_response`.
- `backend/dashboards/views.py` — `UserSearchView.list` (311) → use `success_response`.
- `backend/query/views.py` — `execute_query` (63-70) → wrap inline dict in `success_response`.
- `backend/reports/views.py` — `history` (85), `trigger_now` (93) → use `success_response`.

[Functions]
No new functions. One helper module added.

**New module — `core/response.py`:**
- `success_response(data, message=None, status=200, extra=None)` → `{"success": True, "message": message, "data": data, **(extra or {})}` with `status` filtered out.
- `created_response(data, message="Created successfully.")` → calls `success_response(data, message, status=201)`.
- `deleted_response(message="Deleted successfully.")` → `success_response(None, message, status=200)`.

**Modified — `core/base_exception.py`:**
- No changes needed. `create_error_response` and `custom_exception_handler` already provide a consistent error format.

**Modified — `dashboards/views.py`:**
- `permissions` action (line 244): `Response(serializer.errors, status=400)` → raise `DmvnException(serializer.errors, status_code=400, code="bad_request")`.
- `UserSearchView.list`: `Response({"results": []})` → `Response(success_response(users_data))`.

**Modified — `alerts/views.py`:**
- `check_now`: inline dicts → `success_response({"triggered": True, "history": data})` / `success_response({"triggered": False}, message="Condition not met")`.
- `history`: `Response(serializer.data)` → `Response(success_response(serializer.data))`.
- `stats`: inline dict → `Response(success_response(stats_dict))`.

**Modified — `charts/views.py`:**
- `data`: `Response(self._execute_chart_sql(...))` → `Response(success_response(chart_data))`.
- `drill_down`: `Response(self._execute_chart_sql(...))` → `Response(success_response(data))`. Inline dict `{"columns": ..., "rows": ...}` → `Response(success_response({"columns": ..., "rows": ...}))`.

**Modified — `datasets/views.py`:**
- `list_tables`: `Response({"tables": tables})` → `Response(success_response({"tables": tables}))`.
- `detect_columns`: `Response({"columns": columns})` → `Response(success_response({"columns": columns}))`.

**Modified — `datasources/views.py`:**
- `test`: `Response({"success": True, "message": message})` → `Response(success_response(None, message))`.
- `sync`: `Response(result)` → `Response(success_response(result, "Sync completed"))`.
- `records`: inline dict → `Response(success_response(data_dict))`.

**Modified — `query/views.py`:**
- `execute_query`: inline dict → wrapped in `success_response`.

**Modified — `reports/views.py`:**
- `history`: `Response(serializer.data)` → `Response(success_response(serializer.data))`.
- `trigger_now`: `Response(result)` → `Response(success_response(result, "Report triggered"))`.

[Classes]
No new classes, removals, or class modifications.

All changes are to existing viewset method bodies — no class signatures or hierarchies change.

[Dependencies]
No new packages or version changes.

Only standard-library `from core.response import success_response, created_response, deleted_response` added to each affected views file.

[Testing]
No new test files.

Existing tests should continue passing since response structures are additive (wrapped responses include all original keys inside `"data"`). Any test that asserts exact response JSON shape must be updated to reflect the `{"success": true, "data": …}` envelope. Run the existing test suite after changes to confirm.

Affected tests to verify/update:
- Tests for `datasets` views: assert on `response["tables"]` → assert on `response["data"]["tables"]`.
- Tests for `alerts` views: `check_now`, `history`, `stats` response assertions.
- Tests for `query` views: `execute_query` response shape.
- Tests for `datasources` views: `test` action response.
- Tests for `dashboards` views: `permissions` POST validation error → now raises `DmvnException` instead of returning `400` with raw errors.

[Implementation Order]
Eight steps, each a single file change, ordered by dependency (response module first, then views files from least to most complex).

1. Create `backend/core/response.py` with `success_response`, `created_response`, `deleted_response`.
2. Fix `backend/dashboards/views.py` — `Response(serializer.errors, ...)` → `DmvnException` raise + `Response(success_response(...))` for `UserSearchView.list`.
3. Update `backend/datasets/views.py` — wrap `list_tables` and `detect_columns` responses.
4. Update `backend/query/views.py` — wrap `execute_query` response.
5. Update `backend/alerts/views.py` — wrap `check_now`, `history`, `stats` responses.
6. Update `backend/charts/views.py` — wrap `data`, `drill_down` responses.
7. Update `backend/datasources/views.py` — wrap `test`, `sync`, `records` responses.
8. Update `backend/reports/views.py` — wrap `history`, `trigger_now` responses.
9. Run tests and verify.