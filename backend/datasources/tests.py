"""
Tests for the datasources app.
Covers models, encryption, connectors, serializers, and views.
"""
from unittest import mock
from django.test import TestCase, RequestFactory
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import DataSource, SyncLog, CSVImportJob
from .serializers import (
    DataSourceSerializer,
    DataSourceListSerializer,
    SyncLogSerializer,
    CSVImportJobSerializer,
)
from .connectors import (
    test_connection,
    sync_data,
    get_data,
    _sync_csv,
)
from .encryption import encrypt_config, decrypt_config


User = get_user_model()


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------
class DataSourceModelTest(TestCase):
    def setUp(self):
        self.ds = DataSource.objects.create(
            name="Test Source",
            source_type="csv",
            connection_config={"file_path": "/tmp/test.csv"},
        )

    def test_create(self):
        self.assertEqual(self.ds.name, "Test Source")
        self.assertEqual(self.ds.source_type, "csv")
        self.assertIn("file_path", self.ds.connection_config)
        self.assertEqual(self.ds.status, "ready")

    def test_str(self):
        self.assertEqual(str(self.ds), "Test Source")

    def test_defaults(self):
        self.assertTrue(self.ds.is_active)
        self.assertIsNone(self.ds.last_synced)
        self.assertEqual(self.ds.status, "ready")


class SyncLogModelTest(TestCase):
    def setUp(self):
        self.ds = DataSource.objects.create(
            name="S",
            source_type="csv",
            connection_config={},
        )
        self.log = SyncLog.objects.create(
            source=self.ds,
            status="success",
            rows_synced=100,
        )

    def test_str(self):
        self.assertIn("success", str(self.log))

    def test_related_name(self):
        self.assertIn(self.log, self.ds.sync_logs.all())


class CSVImportJobModelTest(TestCase):
    def setUp(self):
        self.ds = DataSource.objects.create(
            name="S",
            source_type="csv",
            connection_config={},
        )
        self.job = CSVImportJob.objects.create(
            source=self.ds,
            file_name="data.csv",
            file_path="/tmp/data.csv",
        )

    def test_str(self):
        self.assertIn("data.csv", str(self.job))

    def test_defaults(self):
        self.assertEqual(self.job.status, "pending")
        self.assertIsNone(self.job.started_at)
        self.assertIsNone(self.job.finished_at)

    def test_related_name(self):
        self.assertIn(self.job, self.ds.csv_import_jobs.all())


# ---------------------------------------------------------------------------
# Encryption tests
# ---------------------------------------------------------------------------
class EncryptionTest(TestCase):
    def test_encrypt_decrypt(self):
        config = {"host": "localhost", "port": 5432, "dbname": "test"}
        encrypted = encrypt_config(config)
        decrypted = decrypt_config(encrypted)
        self.assertEqual(config, decrypted)

    def test_different_calls_produce_different_ciphertext(self):
        a = encrypt_config({"x": 1})
        b = encrypt_config({"x": 1})
        self.assertNotEqual(a, b)  # different IV each time

    def test_empty_dict(self):
        self.assertEqual({}, decrypt_config(encrypt_config({})))


# ---------------------------------------------------------------------------
# Connector tests
# ---------------------------------------------------------------------------
class CSVConnectorTest(TestCase):
    def setUp(self):
        import tempfile, os
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.tmp.write("name,age\nAlice,30\nBob,25\n")
        self.tmp.close()
        self.ds = DataSource.objects.create(
            name="CSV",
            source_type="csv",
            connection_config={
                "file_path": self.tmp.name,
                "file_name": "test.csv",
            },
        )

    def tearDown(self):
        import os
        os.unlink(self.tmp.name)

    def test_sync_csv(self):
        result = _sync_csv(self.ds)
        self.assertEqual(result["rows_synced"], 2)
        self.assertEqual(result["columns"], ["name", "age"])
        self.ds.refresh_from_db()
        self.assertEqual(self.ds.status, "ready")
        self.assertEqual(self.ds.csv_import_jobs.count(), 1)
        self.assertEqual(self.ds.sync_logs.count(), 1)

    def test_get_data_csv(self):
        result = get_data(self.ds)
        self.assertEqual(result["row_count"], 2)
        self.assertEqual(result["columns"], ["name", "age"])
        self.assertEqual(len(result["rows"]), 2)

    def test_get_data_returns_empty_when_not_ready(self):
        self.ds.status = "syncing"
        self.ds.save(update_fields=["status"])
        result = get_data(self.ds)
        self.assertEqual(result, {"columns": [], "rows": [], "row_count": 0})

    def test_csv_import_job_created_on_sync(self):
        _sync_csv(self.ds)
        job = self.ds.csv_import_jobs.first()
        self.assertIsNotNone(job)
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.rows_imported, 2)


class TestConnectionTest(TestCase):
    def test_csv_ready(self):
        ds = DataSource.objects.create(
            name="S", source_type="csv",
            connection_config={"file_path": "/tmp/f.csv"},
            status="ready",
        )
        ok, msg = test_connection(ds)
        self.assertTrue(ok)

    def test_csv_missing_path(self):
        ds = DataSource.objects.create(
            name="S", source_type="csv",
            connection_config={},
        )
        ok, msg = test_connection(ds)
        self.assertFalse(ok)
        self.assertIn("file_path", msg)

    def test_unsupported_type(self):
        ds = DataSource.objects.create(
            name="S", source_type="oracle",
            connection_config={},
        )
        ok, msg = test_connection(ds)
        self.assertFalse(ok)
        self.assertIn("not supported", msg)

    def test_sqlite_connector(self):
        ds = DataSource.objects.create(
            name="S", source_type="sqlite",
            connection_config={},
        )
        ok, msg = test_connection(ds)
        self.assertFalse(ok)
        self.assertIn("file_path", msg)


# ---------------------------------------------------------------------------
# Serializer tests
# ---------------------------------------------------------------------------
class DataSourceSerializerTest(TestCase):
    def test_read(self):
        ds = DataSource.objects.create(
            name="Test", source_type="csv",
            connection_config={"file_path": "/tmp/f.csv"},
        )
        serializer = DataSourceSerializer(ds)
        data = serializer.data
        self.assertEqual(data["name"], "Test")
        self.assertEqual(data["source_type"], "csv")
        self.assertEqual(data["connection_config"], {"file_path": "/tmp/f.csv"})
        self.assertEqual(data["status"], "ready")

    def test_create(self):
        data = {
            "name": "New",
            "source_type": "csv",
            "connection_config": {"file_path": "/tmp/new.csv"},
        }
        serializer = DataSourceSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        ds = serializer.save()
        self.assertEqual(ds.name, "New")

    def test_invalid_missing_fields(self):
        serializer = DataSourceSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)
        self.assertIn("source_type", serializer.errors)


class DataSourceListSerializerTest(TestCase):
    def test_excludes_connection_config(self):
        ds = DataSource.objects.create(
            name="Test", source_type="csv",
            connection_config={"file_path": "/tmp/f.csv"},
        )
        serializer = DataSourceListSerializer(ds)
        self.assertNotIn("connection_config", serializer.data)


class SyncLogSerializerTest(TestCase):
    def test_fields(self):
        ds = DataSource.objects.create(
            name="S", source_type="csv", connection_config={},
        )
        log = SyncLog.objects.create(source=ds, status="success", rows_synced=10)
        serializer = SyncLogSerializer(log)
        self.assertEqual(serializer.data["status"], "success")
        self.assertEqual(serializer.data["rows_synced"], 10)


class CSVImportJobSerializerTest(TestCase):
    def test_fields(self):
        ds = DataSource.objects.create(
            name="S", source_type="csv", connection_config={},
        )
        job = CSVImportJob.objects.create(
            source=ds, file_name="t.csv", file_path="/tmp/t.csv",
        )
        serializer = CSVImportJobSerializer(job)
        self.assertEqual(serializer.data["file_name"], "t.csv")
        self.assertEqual(serializer.data["status"], "pending")


# ---------------------------------------------------------------------------
# View tests (use mock for connectors)
# ---------------------------------------------------------------------------
class DataSourceViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ds = DataSource.objects.create(
            name="Test",
            source_type="csv",
            connection_config={"file_path": "/tmp/test.csv"},
        )

    def test_list(self):
        response = self.client.get("/api/datasources/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Default DRF pagination wraps results
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_create(self):
        data = {
            "name": "New",
            "source_type": "csv",
            "connection_config": {"file_path": "/tmp/new.csv"},
        }
        response = self.client.post("/api/datasources/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DataSource.objects.count(), 2)

    def test_retrieve(self):
        response = self.client.get(f"/api/datasources/{self.ds.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test")

    def test_update(self):
        data = {"name": "Updated"}
        response = self.client.patch(
            f"/api/datasources/{self.ds.pk}/", data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ds.refresh_from_db()
        self.assertEqual(self.ds.name, "Updated")

    def test_delete(self):
        response = self.client.delete(f"/api/datasources/{self.ds.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DataSource.objects.count(), 0)

    @mock.patch("datasources.views.test_connection")
    def test_test_action_success(self, mock_test):
        mock_test.return_value = (True, "Connection successful")
        response = self.client.post(f"/api/datasources/{self.ds.pk}/test/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    @mock.patch("datasources.views.test_connection")
    def test_test_action_failure(self, mock_test):
        mock_test.return_value = (False, "Connection refused")
        response = self.client.post(f"/api/datasources/{self.ds.pk}/test/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    @mock.patch("datasources.views.sync_data")
    def test_sync_action(self, mock_sync):
        mock_sync.return_value = {"rows_synced": 42}
        response = self.client.post(f"/api/datasources/{self.ds.pk}/sync/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rows_synced"], 42)

    def test_logs_action(self):
        SyncLog.objects.create(source=self.ds, status="success", rows_synced=5)
        response = self.client.get(f"/api/datasources/{self.ds.pk}/logs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class DataSourceFilterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        DataSource.objects.create(
            name="Active", source_type="csv",
            connection_config={}, is_active=True, status="ready",
        )
        DataSource.objects.create(
            name="Inactive", source_type="csv",
            connection_config={}, is_active=False, status="error",
        )

    def test_filter_by_status(self):
        response = self.client.get("/api/datasources/", {"status": "error"})
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "error")

    def test_filter_by_is_active(self):
        response = self.client.get("/api/datasources/", {"is_active": "true"})
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)

    def test_search_by_name(self):
        response = self.client.get("/api/datasources/", {"search": "Active"})
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Active")


class CSVImportViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ds = DataSource.objects.create(
            name="CSV", source_type="csv",
            connection_config={},
        )

    def test_import_missing_source_id(self):
        from io import BytesIO
        csv_bytes = b"name\nAlice\n"
        response = self.client.post(
            "/api/datasources/import-csv/",
            {"file": BytesIO(csv_bytes)},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_import_invalid_source(self):
        from io import BytesIO
        csv_bytes = b"name\nAlice\n"
        response = self.client.post(
            "/api/datasources/import-csv/",
            {"source_id": 9999, "file": BytesIO(csv_bytes)},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RecordsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        import tempfile, os
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False
        )
        self.tmp.write("a,b\n1,2\n")
        self.tmp.close()
        self.ds = DataSource.objects.create(
            name="CSV", source_type="csv",
            connection_config={
                "file_path": self.tmp.name,
                "file_name": "test.csv",
            },
        )

    def tearDown(self):
        import os
        os.unlink(self.tmp.name)

    def test_records_action(self):
        # First sync to populate the file
        _sync_csv(self.ds)
        response = self.client.get(f"/api/datasources/{self.ds.pk}/records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["row_count"], 1)
        self.assertEqual(response.data["data"]["columns"], ["a", "b"])
