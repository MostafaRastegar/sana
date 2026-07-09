from rest_framework.permissions import BasePermission
from django.core.exceptions import ImproperlyConfigured
from typing import Any


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
        if (
            hasattr(view, "model_permission_mapping")
            and action in view.model_permission_mapping
        ):
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
        """
        if not request.user or not request.user.is_authenticated:
            return False

        action = view.action
        if not action:
            return False

        required_permission = self.get_required_permission(view, action)

        # Check if user has the required permission
        return request.user.has_perm(required_permission)

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
