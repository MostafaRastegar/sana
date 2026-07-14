"""Unit tests for core middleware."""
from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from django.utils import translation

from core.middleware import HTTPMethodRestrictionMiddleware, APILanguageDetectionMiddleware


def _ok_response(request):
    return HttpResponse("ok")


class HTTPMethodRestrictionMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = HTTPMethodRestrictionMiddleware(_ok_response)

    def test_allows_get(self):
        req = self.factory.get("/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 200)

    def test_allows_post(self):
        req = self.factory.post("/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 200)

    def test_allows_put(self):
        req = self.factory.put("/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 200)

    def test_allows_patch(self):
        req = self.factory.patch("/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 200)

    def test_allows_delete(self):
        req = self.factory.delete("/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 200)

    def test_allows_head(self):
        req = self.factory.head("/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 200)

    def test_allows_options(self):
        req = self.factory.options("/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 200)

    def test_blocks_unknown_method(self):
        req = self.factory.generic("PURGE", "/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not allowed", resp.content.decode().lower())

    def test_blocks_trace(self):
        req = self.factory.generic("TRACE", "/")
        resp = self.middleware(req)
        self.assertEqual(resp.status_code, 400)


@override_settings(LANGUAGES=[("en", "English"), ("fa", "Persian")], LANGUAGE_CODE="fa")
class APILanguageDetectionMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = APILanguageDetectionMiddleware(_ok_response)

    def test_ignores_non_api_path(self):
        req = self.factory.get("/admin/")
        translation.deactivate()
        self.middleware(req)
        self.assertEqual(translation.get_language(), "fa")

    def test_detects_language_from_url(self):
        req = self.factory.get("/api/en/users/")
        self.middleware(req)
        self.assertEqual(translation.get_language(), "en")

    def test_detects_language_from_url_fa(self):
        req = self.factory.get("/api/fa/dashboards/")
        self.middleware(req)
        self.assertEqual(translation.get_language(), "fa")

    def test_falls_back_to_default_for_invalid_lang(self):
        req = self.factory.get("/api/de/users/")
        translation.deactivate()
        translation.activate("fa")
        self.middleware(req)
        self.assertEqual(translation.get_language(), "fa")

    def test_detects_language_from_query_param(self):
        req = self.factory.get("/api/dashboards/?lang=en")
        self.middleware(req)
        self.assertEqual(translation.get_language(), "en")

    def test_url_lang_takes_priority_over_query_param(self):
        req = self.factory.get("/api/fa/dashboards/?lang=en")
        self.middleware(req)
        # Middleware checks URL first — URL path lang wins over query param
        self.assertEqual(translation.get_language(), "fa")

    def test_detects_from_accept_language_header(self):
        req = self.factory.get("/api/dashboards/", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9")
        self.middleware(req)
        self.assertEqual(translation.get_language(), "en")

    def test_sets_request_language_code(self):
        req = self.factory.get("/api/en/dashboards/")
        self.middleware(req)
        self.assertEqual(req.LANGUAGE_CODE, "en")

    def test_no_lang_uses_default(self):
        req = self.factory.get("/api/dashboards/")
        translation.deactivate()
        translation.activate("fa")
        self.middleware(req)
        self.assertEqual(translation.get_language(), "fa")