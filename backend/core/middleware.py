import re
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.utils import translation


class HTTPMethodRestrictionMiddleware:
    """
    Middleware to restrict HTTP methods to only allowed ones.
    Blocks PUT and unknown HTTP methods.
    """

    ALLOWED_METHODS = {"GET", "POST", "PUT", "HEAD", "OPTIONS", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in self.ALLOWED_METHODS:
            return HttpResponseBadRequest(
                f"Method '{request.method}' not allowed. Allowed methods: {', '.join(sorted(self.ALLOWED_METHODS))}"
            )
        return self.get_response(request)


class APILanguageDetectionMiddleware:
    """
    Middleware to detect language from URL path, headers, or query parameters
    for API responses.

    Detection priority:
    1. URL path (e.g., /api/fa/users/)
    2. Query parameter (lang=fa)
    3. Accept-Language header
    4. Default language (fa)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Compile regex for language detection in URL paths
        self.lang_pattern = re.compile(r"^/api/(?P<lang>[a-z]{2})/")

    def __call__(self, request):
        # Only process API requests
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        language = self._detect_language(request)
        if language:
            translation.activate(language)
            # Store in request for later use
            request.LANGUAGE_CODE = language

        response = self.get_response(request)
        return response

    def _detect_language(self, request):
        """
        Detect language from multiple sources in order of priority.
        """

        # 1. Check URL path (/api/fa/users/)
        match = self.lang_pattern.match(request.path)
        if match:
            lang_code = match.group("lang")
            if lang_code in [lang[0] for lang in settings.LANGUAGES]:
                return lang_code

        # 2. Check query parameter (?lang=fa)
        lang_param = request.GET.get("lang")
        if lang_param and lang_param in [lang[0] for lang in settings.LANGUAGES]:
            return lang_param

        # 3. Check Accept-Language header
        accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        if accept_lang:
            # Parse Accept-Language header (e.g., "fa,en-US;q=0.9,en;q=0.8")
            languages = [lang.split(";")[0].strip() for lang in accept_lang.split(",")]
            for lang in languages:
                lang_code = lang.split("-")[0]  # Extract 'fa' from 'fa-IR'
                if lang_code in [lang[0] for lang in settings.LANGUAGES]:
                    return lang_code

        # 4. Return default language
        return settings.LANGUAGE_CODE
