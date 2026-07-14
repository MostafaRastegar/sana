import os

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """Return unauthenticated APIClient."""
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    user, _ = User.objects.get_or_create(
        username="admin",
        defaults={
            "email": "admin@test.com",
            "is_staff": True,
            "is_superuser": True,
        },
    )
    user.set_password("admin123")
    user.save()
    return user


@pytest.fixture
def auth_client(admin_user):
    """Return authenticated APIClient as admin user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def regular_user(db):
    """Create and return a non-admin user."""
    user, _ = User.objects.get_or_create(
        username="user",
        defaults={
            "email": "user@test.com",
            "is_staff": False,
            "is_superuser": False,
        },
    )
    user.set_password("user123")
    user.save()
    return user