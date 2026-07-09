from django.test import TestCase
from django.contrib.auth.models import User
from django.db import connection
from rest_framework.test import APIClient


class QueryAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="test", password="test123")
        self.client.force_authenticate(user=self.user)
        with connection.cursor() as c:
            c.execute("CREATE TABLE IF NOT EXISTS test_query_data (id INTEGER, val INTEGER)")
            c.execute("INSERT INTO test_query_data VALUES (1, 100), (2, 200)")

    def tearDown(self):
        with connection.cursor() as c:
            c.execute("DROP TABLE IF EXISTS test_query_data")

    def test_execute_select(self):
        resp = self.client.post("/api/execute/", {"sql": "SELECT * FROM test_query_data"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("rows", resp.data)
        self.assertEqual(len(resp.data["rows"]), 2)

    def test_execute_rejects_non_select(self):
        resp = self.client.post("/api/execute/", {"sql": "DROP TABLE test_query_data"})
        self.assertEqual(resp.status_code, 400)

    def test_execute_requires_sql(self):
        resp = self.client.post("/api/execute/", {"sql": ""})
        self.assertEqual(resp.status_code, 400)
