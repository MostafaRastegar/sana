"""Unit tests for core exception handler."""
from unittest.mock import Mock
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError as DjangoValidationError, PermissionDenied
from django.db.models import ProtectedError
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core.base_exception import (
    DmvnException,
    custom_exception_handler,
    create_error_response,
)


class DmvnExceptionTest(TestCase):
    def test_default_values(self):
        exc = DmvnException("test error")
        self.assertEqual(exc.message, "test error")
        self.assertEqual(exc.status_code, 400)
        self.assertEqual(exc.code, "invalid")
        self.assertEqual(exc.details, [])

    def test_custom_values(self):
        exc = DmvnException("permission denied", status_code=403, code="forbidden", details=["no access"])
        self.assertEqual(exc.message, "permission denied")
        self.assertEqual(exc.status_code, 403)
        self.assertEqual(exc.code, "forbidden")
        self.assertEqual(exc.details, ["no access"])

    def test_inherits_from_exception(self):
        exc = DmvnException("test")
        self.assertIsInstance(exc, Exception)


class CreateErrorResponseTest(TestCase):
    def test_creates_payload(self):
        payload = create_error_response(400, "bad request", ["detail1"], code="bad_request")
        self.assertEqual(payload, {
            "error": {
                "status_code": 400,
                "code": "bad_request",
                "message": "bad request",
                "details": ["detail1"],
            }
        })

    def test_empty_details(self):
        payload = create_error_response(500, "error", [])
        self.assertEqual(payload["error"]["details"], [])


class CustomExceptionHandlerTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.context = {"view": APIView()}

    def _get_response(self, exc):
        return custom_exception_handler(exc, self.context)

    def test_handles_dmvn_exception(self):
        resp = self._get_response(DmvnException("custom error", status_code=422, code="validation"))
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.data["error"]["code"], "validation")
        self.assertIn("custom error", resp.data["error"]["message"])

    def test_handles_django_validation_error(self):
        exc = DjangoValidationError({"name": ["This field is required."]})
        resp = self._get_response(exc)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"]["code"], "bad_request")
        self.assertIn("name", resp.data["error"]["details"])

    def test_handles_django_validation_error_non_dict(self):
        exc = DjangoValidationError("invalid value")
        resp = self._get_response(exc)
        self.assertEqual(resp.status_code, 400)

    def test_handles_drf_validation_error_list(self):
        exc = DRFValidationError(["error1", "error2"])
        resp = self._get_response(exc)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error1", resp.data["error"]["details"]["non_field_errors"])

    def test_handles_drf_validation_error_dict(self):
        exc = DRFValidationError({"name": ["required"]})
        resp = self._get_response(exc)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"]["details"]["name"], ["required"])

    def test_handles_protected_error(self):
        exc = ProtectedError("protected", Mock())
        resp = self._get_response(exc)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["error"]["code"], "protected")

    def test_handles_permission_denied(self):
        exc = PermissionDenied("no access")
        resp = self._get_response(exc)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.data["error"]["code"], "forbidden")

    def test_handles_drf_exception(self):
        from rest_framework.exceptions import NotFound
        resp = self._get_response(NotFound())
        self.assertEqual(resp.status_code, 404)
        self.assertIn("error", resp.data)

    def test_handles_unexpected_exception(self):
        resp = self._get_response(ValueError("something broke"))
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.data["error"]["code"], "internal")