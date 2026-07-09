#!/usr/bin/env python
"""
Script to create test users for the Django project.
Run this script to create test users with different permission levels.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


def create_user(
    username,
    email,
    password,
    is_staff=False,
    is_superuser=False,
    first_name="",
    last_name="",
):
    """Create a user with the given parameters."""
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )
        print(f"✅ Created user: {username} ({email})")
        return user
    except ValidationError as e:
        print(f"❌ Error creating user {username}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error creating user {username}: {e}")
        return None


def main():
    """Create test users."""
    print("🚀 Creating test users...")

    # Create admin user (already exists from createsuperuser command)
    try:
        admin_user = User.objects.get(username="admin")
        print(f"✅ Admin user already exists: {admin_user.username}")
    except User.DoesNotExist:
        admin_user = create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
            is_superuser=True,
            first_name="Admin",
            last_name="User",
        )

    # Create regular staff user
    staff_user = create_user(
        username="staff",
        email="staff@example.com",
        password="staff123",
        is_staff=True,
        is_superuser=False,
        first_name="Staff",
        last_name="User",
    )

    # Create regular user
    regular_user = create_user(
        username="user",
        email="user@example.com",
        password="user123",
        is_staff=False,
        is_superuser=False,
        first_name="Regular",
        last_name="User",
    )

    # Create another regular user
    test_user = create_user(
        username="testuser",
        email="test@example.com",
        password="test123",
        is_staff=False,
        is_superuser=False,
        first_name="Test",
        last_name="User",
    )

    print("\n📋 Test users created successfully!")
    print("\n🔐 Login credentials:")
    print("Admin user:")
    print("  Username: admin")
    print("  Password: admin123")
    print("  Email: admin@example.com")

    print("\nStaff user:")
    print("  Username: staff")
    print("  Password: staff123")
    print("  Email: staff@example.com")

    print("\nRegular user:")
    print("  Username: user")
    print("  Password: user123")
    print("  Email: user@example.com")

    print("\nTest user:")
    print("  Username: testuser")
    print("  Password: test123")
    print("  Email: test@example.com")

    print("\n💡 To get JWT tokens, use:")
    print("curl -X POST http://127.0.0.1:8000/api/token/ \\")
    print("  -H 'Content-Type: application/json' \\")
    print('  -d \'{"username":"admin","password":"admin123"}\'')

    print("\n🌐 Admin panel: http://127.0.0.1:8000/admin/")
    print("📚 API Documentation: http://127.0.0.1:8000/api/docs/")


if __name__ == "__main__":
    main()
