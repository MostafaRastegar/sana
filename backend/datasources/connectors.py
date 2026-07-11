"""Connector implementations for external data sources."""

import csv
import io
import logging
from datetime import datetime
from typing import Any

import requests
from django.db import connection
from django.utils import timezone

from .models import DataSource, SyncLog, CSVImportJob

logger = logging.getLogger(__name__)


def test_connection(source: DataSource) -> tuple[bool, str]:
    """Validate data source connectivity. Returns (success, message)."""
    config = source.get_decrypted_config()
    try:
        if source.source_type == "postgresql":
            return _test_postgresql(config)
        elif source.source_type == "mysql":
            return _test_mysql(config)
        elif source.source_type == "sqlite":
            return _test_sqlite(config)
        elif source.source_type == "api":
            return _test_api(config)
        elif source.source_type == "csv":
            return _test_csv(config)
        else:
            return False, f"Unsupported source type: {source.source_type}"
    except Exception as e:
        logger.exception(f"Connection test failed for {source.name}")
        return False, str(e)


def sync_data(source: DataSource) -> dict[str, Any]:
    """Pull data from external source and import into a local table.

    Returns dict with status, rows_imported, error_message.
    """
    log = SyncLog.objects.create(
        source=source,
        started_at=timezone.now(),
        status="running",
    )
    try:
        if source.source_type in ("postgresql", "mysql", "sqlite"):
            result = _sync_sql(source)
        elif source.source_type == "api":
            result = _sync_api(source)
        elif source.source_type == "csv":
            result = _sync_csv(source)
        else:
            raise ValueError(f"Unsupported source type: {source.source_type}")

        log.status = "success"
        log.finished_at = timezone.now()
        log.rows_imported = result.get("rows_imported", 0)
        log.save(update_fields=["status", "finished_at", "rows_imported"])

        source.last_synced = timezone.now()
        source.status = "active"
        source.error_message = ""
        source.save(update_fields=["last_synced", "status", "error_message"])

        # Auto-create or update a Dataset for this datasource
        columns = result.get("columns", [])
        if columns:
            try:
                _auto_create_dataset(source, columns)
            except Exception as ds_err:
                logger.warning(f"Auto-create dataset failed for {source.name}: {ds_err}")

        return result
    except Exception as e:
        logger.exception(f"Sync failed for {source.name}")
        log.status = "failed"
        log.finished_at = timezone.now()
        log.error_message = str(e)
        log.save(update_fields=["status", "finished_at", "error_message"])

        source.status = "error"
        source.error_message = str(e)
        source.save(update_fields=["status", "error_message"])
        return {"status": "failed", "rows_imported": 0, "error_message": str(e)}


def _auto_create_dataset(source: DataSource, columns: list[str]) -> None:
    """Create or update a Dataset linked to this DataSource."""
    from datasets.models import Dataset

    col_defs = [{"name": c, "type": "string", "label": c.replace("_", " ").title()} for c in columns]

    table_name = f"datasource_{source.id}"

    # Count rows
    row_count = 0
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            row_count = cursor.fetchone()[0]
    except Exception:
        pass

    existing = Dataset.objects.filter(datasource=source).first()
    if existing:
        existing.columns = col_defs
        existing.row_count = row_count
        existing.save(update_fields=["columns", "row_count"])
    else:
        Dataset.objects.create(
            name=source.name,
            description=f"Auto-created from datasource: {source.name}",
            table_name=table_name,
            columns=col_defs,
            row_count=row_count,
            datasource=source,
        )


def _import_rows_to_local(table_name: str, columns: list[str], rows: list[list]) -> int:
    """Create/replace local table and bulk-insert rows."""
    cols = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join("%s" for _ in columns)

    with connection.cursor() as cursor:
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        col_defs = ", ".join(f'"{c}" TEXT' for c in columns)
        cursor.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

        if rows:
            values = [tuple(row) for row in rows]

            # Batch insert
            for i in range(0, len(values), 500):
                batch = values[i : i + 500]
                placeholders_list = ", ".join(
                    f"({placeholders})" for _ in batch
                )
                flat_params = [item for row in batch for item in row]
                sql = f'INSERT INTO "{table_name}" ({cols}) VALUES {placeholders_list}'
                cursor.execute(sql, flat_params)

    return len(rows)


# ── PostgreSQL ──────────────────────────────────────────────


def _test_postgresql(config: dict) -> tuple[bool, str]:
    import psycopg2
    conn = psycopg2.connect(
        host=config.get("host", "localhost"),
        port=config.get("port", 5432),
        dbname=config.get("database"),
        user=config.get("user"),
        password=config.get("password"),
        connect_timeout=5,
    )
    conn.close()
    return True, "Connection successful"


def _test_mysql(config: dict) -> tuple[bool, str]:
    import pymysql
    conn = pymysql.connect(
        host=config.get("host", "localhost"),
        port=config.get("port", 3306),
        database=config.get("database"),
        user=config.get("user"),
        password=config.get("password"),
        connect_timeout=5,
    )
    conn.close()
    return True, "Connection successful"


# ── SQLite ──────────────────────────────────────────────


def _test_sqlite(config: dict) -> tuple[bool, str]:
    path = config.get("path", "")
    if not path:
        return False, "No SQLite file path configured"
    import sqlite3
    conn = sqlite3.connect(path, timeout=5)
    conn.close()
    return True, "SQLite connection successful"


# ── SQL Sync (shared) ───────────────────────────────────────


def _sync_sql(source: DataSource) -> dict[str, Any]:
    config = source.get_decrypted_config()
    query = config.get("query", "SELECT * FROM information_schema.tables LIMIT 100")

    if source.source_type == "postgresql":
        import psycopg2
        conn = psycopg2.connect(
            host=config.get("host", "localhost"),
            port=config.get("port", 5432),
            dbname=config.get("database"),
            user=config.get("user"),
            password=config.get("password"),
            connect_timeout=10,
        )
    elif source.source_type == "mysql":
        import pymysql
        conn = pymysql.connect(
            host=config.get("host", "localhost"),
            port=config.get("port", 3306),
            database=config.get("database"),
            user=config.get("user"),
            password=config.get("password"),
            connect_timeout=10,
        )
    elif source.source_type == "sqlite":
        import sqlite3
        path = config.get("path", "")
        if not path:
            raise ValueError("No SQLite file path configured")
        conn = sqlite3.connect(path, timeout=10)
    else:
        raise ValueError(f"Unsupported SQL type: {source.source_type}")

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        raw = cursor.fetchall() or []
        rows = [list(row) for row in raw]
        cursor.close()
    finally:
        conn.close()

    table_name = f"datasource_{source.id}"
    imported = _import_rows_to_local(table_name, columns, rows)

    return {"status": "success", "rows_imported": imported, "table_name": table_name, "columns": columns}


# ── REST API ──────────────────────────────────────────


def _test_api(config: dict) -> tuple[bool, str]:
    url = config.get("url")
    if not url:
        return False, "No URL configured"
    resp = requests.head(url, timeout=5)
    resp.raise_for_status()
    return True, f"API responded with {resp.status_code}"


def _sync_api(source: DataSource) -> dict[str, Any]:
    config = source.get_decrypted_config()
    url = config.get("url")
    headers = config.get("headers", {})
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict):
        data = data.get(config.get("results_key", "results"), data)

    if not isinstance(data, list) or not data:
        raise ValueError("API response is empty or not a list")

    columns = list(data[0].keys())
    rows = [[row.get(c, "") for c in columns] for row in data]

    table_name = f"datasource_{source.id}"
    imported = _import_rows_to_local(table_name, columns, rows)

    return {"status": "success", "rows_imported": imported, "table_name": table_name, "columns": columns}


# ── CSV ────────────────────────────────────────────────


def _test_csv(config: dict) -> tuple[bool, str]:
    file_path = config.get("file_path", "")
    if not file_path:
        return False, "No CSV file path configured"
    import os
    if not os.path.exists(file_path):
        return False, f"CSV file not found at path: {file_path}"
    return True, "CSV file exists and is accessible"


def get_data(source: DataSource, limit: int = 1000) -> dict[str, Any]:
    """Read rows from the local mirrored table for a data source."""
    table_name = f"datasource_{source.id}"
    try:
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT * FROM "{table_name}" LIMIT %s', [limit])
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return {"columns": columns, "rows": rows, "row_count": len(rows)}
    except Exception:
        # Table doesn't exist yet — no sync performed or sync failed
        return {"columns": [], "rows": [], "row_count": 0}


def _sync_csv(source: DataSource) -> dict[str, Any]:
    config = source.get_decrypted_config()
    file_path = config.get("file_path", "")

    if not file_path:
        raise ValueError("No CSV file path configured")

    with open(file_path) as f:
        content = f.read()

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows:
        raise ValueError("CSV is empty")

    columns = rows[0]
    data_rows = rows[1:]

    table_name = f"datasource_{source.id}"
    imported = _import_rows_to_local(table_name, columns, data_rows)

    config["csv_content"] = content
    source.connection_config = config
    source.save(update_fields=["connection_config"])

    return {"status": "success", "rows_imported": imported, "table_name": table_name, "columns": columns}