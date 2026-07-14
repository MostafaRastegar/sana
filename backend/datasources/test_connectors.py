from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from datasources import connectors
from datasources.models import DataSource


class ConnectorTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("conn", "c@c.com", "p")
        self.ds = DataSource.objects.create(
            name="TestPG", source_type="postgresql",
            connection_config={
                "host": "localhost", "port": 5432,
                "dbname": "test", "user": "u", "password": "p",
            },
        )


class TestConnectionTest(ConnectorTestBase):
    @patch("psycopg2.connect")
    def test_connection_success(self, mock_connect):
        mock_connect.return_value = MagicMock()
        result = connectors.test_connection(self.ds)
        self.assertTrue(result[0])

    @patch("psycopg2.connect")
    def test_connection_failure(self, mock_connect):
        mock_connect.side_effect = Exception("conn refused")
        result = connectors.test_connection(self.ds)
        self.assertFalse(result[0])
        self.assertIn("conn refused", result[1])


class GetDataTest(ConnectorTestBase):
    def test_get_data_empty(self):
        # Table doesn't exist yet -> returns empty
        result = connectors.get_data(self.ds, "test_table")
        self.assertEqual(len(result["rows"]), 0)


class SyncDataTest(ConnectorTestBase):
    @patch("psycopg2.connect")
    def test_sync_data_creates_dataset(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "a"), (2, "b")]
        mock_connect.return_value.cursor.return_value = mock_cursor
        result = connectors.sync_data(self.ds)
        self.assertEqual(result["status"], "success")

    @patch("psycopg2.connect")
    def test_sync_data_failure(self, mock_connect):
        mock_connect.side_effect = Exception("Connection refused")
        result = connectors.sync_data(self.ds)
        self.assertEqual(result["status"], "failed")
        self.assertIn("Connection refused", result["error_message"])