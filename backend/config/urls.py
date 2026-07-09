"""
URL configuration for team_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.http import HttpResponseRedirect
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from django.templatetags.static import static


# Get admin URL path from environment variable (default: 'admin/')
admin_url_path = settings.ADMIN_URL_PATH or "admin/"


def favicon_view(request):
    """Serve favicon.ico from static files"""
    return HttpResponseRedirect(static("/favicon/favicon.ico"))


# API URL patterns (shared between prefixed and non-prefixed)
api_patterns = [
    # JWT Authentication endpoints
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    # API Documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Non-translatable URLs (API endpoints, media, etc.)
urlpatterns = [
    path("api/", include(api_patterns)),
    # Include example app URLs in API patterns
    # Include BI Dashboard app URLs
    path("api/", include("datasets.urls")),
    path("api/", include("charts.urls")),
    path("api/", include("dashboards.urls")),
    path("api/", include("query.urls")),
    path("api/", include("alerts.urls")),
    # Favicon serving for browsers that look for /favicon.ico
    path("favicon.ico", favicon_view, name="favicon"),
]

# Translatable URLs (admin interface, etc.)
urlpatterns += i18n_patterns(
    path("i18n/", include("django.conf.urls.i18n")),  # Language switching URLs
    path(admin_url_path, admin.site.urls),
    prefix_default_language=False,  # Don't add language prefix for default language (Persian)
)
