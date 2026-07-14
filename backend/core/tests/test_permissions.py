"""Unit tests for core app permissions."""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from core.permissions import IsAdminUserOrReadOnly, ModelActionPermission

User = get_user_model()


class StubView(APIView):
    """Minimal view for permission testing."""
    action = None
    queryset = None
    model = None
    model_permission_mapping = None


class StubModelView:
    """Simulates a ModelViewSet for permission tests."""
    action = None
    queryset = None
    model = None
    model_permission_mapping = None


class IsAdminUserOrReadOnlyTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = IsAdminUserOrReadOnly()
        self.view = StubView.as_view()

    def _build_request(self, method="GET", user=None):
        req = self.factory.generic(method, "/")
        req.user = user
        return req

    def test_read_allows_authenticated(self):
        user = User.objects.create_user(username="reader", password="pass")
        req = self._build_request("GET", user)
        self.assertTrue(self.permission.has_permission(req, APIView()))

    def test_read_denies_unauthenticated(self):
        req = self._build_request("GET", None)
        self.assertFalse(self.permission.has_permission(req, APIView()))

    def test_write_denies_regular_user(self):
        user = User.objects.create_user(username="writer", password="pass")
        req = self._build_request("POST", user)
        self.assertFalse(self.permission.has_permission(req, APIView()))

    def test_write_allows_staff(self):
        user = User.objects.create_user(username="staff", password="pass", is_staff=True)
        req = self._build_request("POST", user)
        self.assertTrue(self.permission.has_permission(req, APIView()))

    def test_write_allows_superuser(self):
        user = User.objects.create_superuser(username="super", password="pass")
        req = self._build_request("POST", user)
        self.assertTrue(self.permission.has_permission(req, APIView()))

    def test_options_allows_authenticated(self):
        user = User.objects.create_user(username="opts", password="pass")
        req = self._build_request("OPTIONS", user)
        self.assertTrue(self.permission.has_permission(req, APIView()))

    def test_head_allows_authenticated(self):
        user = User.objects.create_user(username="header", password="pass")
        req = self._build_request("HEAD", user)
        self.assertTrue(self.permission.has_permission(req, APIView()))


class ModelActionPermissionTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission = ModelActionPermission()

    def _make_view(self, action=None, model=None, queryset=None, mapping=None):
        view = StubModelView()
        view.action = action
        view.model = model
        view.queryset = queryset
        view.model_permission_mapping = mapping
        return view

    def _make_request(self, user=None):
        req = self.factory.get("/")
        req.user = user
        return req

    def test_denies_unauthenticated(self):
        view = self._make_view(action="list")
        self.assertFalse(self.permission.has_permission(self._make_request(None), view))

    def test_superuser_bypasses(self):
        user = User.objects.create_superuser(username="super", password="pass")
        view = self._make_view(action="create")
        self.assertTrue(self.permission.has_permission(self._make_request(user), view))

    def test_regular_user_authenticated_passes(self):
        user = User.objects.create_user(username="regular", password="pass")
        view = self._make_view(action="list")
        self.assertTrue(self.permission.has_permission(self._make_request(user), view))

    def test_no_action_returns_false(self):
        user = User.objects.create_user(username="noact", password="pass")
        view = self._make_view(action=None)
        self.assertFalse(self.permission.has_permission(self._make_request(user), view))

    def test_staff_user_with_permission_passes(self):
        ct = ContentType.objects.get_for_model(User)
        perm = Permission.objects.get(content_type=ct, codename="change_user")
        user = User.objects.create_user(username="staff", password="pass", is_staff=True)
        user.user_permissions.add(perm)

        view = self._make_view(action="update", model=User)
        self.assertTrue(self.permission.has_permission(self._make_request(user), view))

    def test_staff_user_without_permission_denied(self):
        user = User.objects.create_user(username="staff", password="pass", is_staff=True)
        view = self._make_view(action="create", model=User)
        self.assertFalse(self.permission.has_permission(self._make_request(user), view))

    def test_staff_user_read_only_bypasses_permission(self):
        user = User.objects.create_user(username="staff", password="pass", is_staff=True)
        view = self._make_view(action="list", model=User)
        self.assertTrue(self.permission.has_permission(self._make_request(user), view))

    def test_custom_permission_mapping(self):
        ct = ContentType.objects.get_for_model(User)
        # Use a real permission code "view_user" — view is a built-in Django permission
        perm = Permission.objects.get(content_type=ct, codename="view_user")
        user = User.objects.create_user(username="custom", password="pass", is_staff=True)
        user.user_permissions.add(perm)

        view = self._make_view(
            action="custom_action", model=User,
            mapping={"custom_action": "auth.view_user"},
        )
        self.assertTrue(self.permission.has_permission(self._make_request(user), view))

    def test_get_required_permission_custom(self):
        view = self._make_view(
            action="export", model=User,
            mapping={"export": "auth.view_user"},
        )
        perm = self.permission.get_required_permission(view, "export")
        self.assertEqual(perm, "auth.view_user")

    def test_get_required_permission_standard(self):
        view = self._make_view(action="create", model=User)
        perm = self.permission.get_required_permission(view, "create")
        self.assertEqual(perm, "auth.add_user")

    def test_get_required_permission_unmapped_action(self):
        view = self._make_view(action="custom_action", model=User)
        perm = self.permission.get_required_permission(view, "custom_action")
        self.assertEqual(perm, "auth.custom_action_user")

    def test_get_model_class_from_queryset(self):
        from django.contrib.auth.models import User as UserModel
        view = self._make_view(action="list", queryset=UserModel.objects.all())
        self.assertIs(self.permission._get_model_class(view), UserModel)