from rest_framework.permissions import BasePermission
from django.core.exceptions import ImproperlyConfigured
from typing import Any


class IsAdminUserOrReadOnly(BasePermission):
    """
    Permission that allows read-only access to any authenticated user,
    and write access only to admin/superuser.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.is_staff or request.user.is_superuser


class ModelActionPermission(BasePermission):
    """
    Permission class that maps ViewSet actions to model permissions.

    Supports both standard ViewSet actions and custom actions defined with @action decorator.

    Maps actions to Django permissions in format: app_label.permission_action_model

    Standard mapping:
    - list -> app.view_model
    - create -> app.add_model
    - retrieve -> app.view_model
    - update -> app.change_model
    - partial_update -> app.change_model
    - destroy -> app.delete_model

    Custom actions can be mapped via model_permission_mapping dict on ViewSet:
    class MyViewSet(ModelViewSet):
        model_permission_mapping = {
            'archive': 'myapp.archive_mymodel',  # Custom permission
            'export': 'myapp.export_mymodel',    # Custom permission
        }
    """

    # Standard action to permission mapping
    action_permission_map = {
        "list": "view",
        "retrieve": "view",
        "create": "add",
        "update": "change",
        "partial_update": "change",
        "destroy": "delete",
    }

    def get_required_permission(self, view, action):
        """
        Get the required permission string for the given view and action.
        """
        # Get model class from view
        model_cls = self._get_model_class(view)

        # Get app_label and model_name
        app_label = model_cls._meta.app_label
        model_name = model_cls._meta.model_name

        # Check if custom permission mapping exists for this action
        mapping = getattr(view, "model_permission_mapping", None)
        if mapping is not None and action in mapping:
            return view.model_permission_mapping[action]

        # Use standard action mapping
        if action in self.action_permission_map:
            permission_codename = f"{self.action_permission_map[action]}_{model_name}"
        else:
            # For unmapped actions, use action as permission type
            permission_codename = f"{action}_{model_name}"

        return f"{app_label}.{permission_codename}"

    def has_permission(self, request, view) -> Any:
        """
        Check if the user has permission for the current action.

        - Superusers always pass.
        - Staff users must have the required django permission.
        - Regular users pass authentication check — actual access control
          is enforced by the view's get_queryset() and perform_*() methods.
        """
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers bypass all permission checks
        if request.user.is_superuser:
            return True

        action = view.action
        if not action:
            return False

        # Staff users: enforce django model permissions
        if request.user.is_staff:
            required_permission = self.get_required_permission(view, action)
            if not request.user.has_perm(required_permission):
                # Allow read-only actions even without explicit permission
                if action in ("list", "retrieve"):
                    return True
                return False
            return True

        # Regular (non-staff) users: allow if authenticated.
        # Fine-grained access control is delegated to:
        #   - get_queryset() — filters visible objects
        #   - perform_create/update/destroy — checks ownership/permissions
        return True

    def _get_model_class(self, view):
        """
        Get the model class from the view.
        Supports both ModelViewSet and custom views with model attribute.
        """
        if hasattr(view, "queryset") and view.queryset is not None:
            return view.queryset.model
        elif hasattr(view, "model"):
            return view.model
        elif hasattr(view, "get_queryset"):
            try:
                queryset = view.get_queryset()
                return queryset.model
            except:
                pass

        raise ImproperlyConfigured(
            f"{view.__class__.__name__} must define a queryset, model, or override get_queryset()"
        )