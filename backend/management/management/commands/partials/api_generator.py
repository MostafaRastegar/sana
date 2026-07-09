from typing import Any, List
from .base import BaseTsGenerator
import os


class ApiGenerator(BaseTsGenerator):
    """
    Generates 'endpoints.ts' and individual service files (e.g., 'CategoryService.ts')
    from DRF ViewSets. Handles mapping DRF actions to TypeScript methods.
    """

    def __init__(
        self, app_name: str, app_dir: str, stdout: Any, style: Any, data: List[Any]
    ):
        super().__init__(app_name, app_dir, stdout, style)
        self.data = data
        self.interfaces_content = {}

    def _load_service_interfaces(self):
        """Load service interfaces from the generated file."""
        interface_filename = f"I{self.app_name}Service.ts"
        interfaces_file = os.path.join(self.app_dir, interface_filename)
        if os.path.exists(interfaces_file):
            with open(interfaces_file, "r") as f:
                content = f.read()
                # Extract interface names and their content
                # This is a simple parser - you might need to make it more robust
                import re

                pattern = r"export interface (I\w+Service) \{(.*?)\};"
                matches = re.findall(pattern, content, re.DOTALL)
                for interface_name, interface_body in matches:
                    self.interfaces_content[interface_name] = interface_body.strip()

    def _generate_service_methods(
        self, model_name: str, prefix: str, viewset_class: type
    ) -> list[str]:
        """Generates TypeScript service method lines for a given model and ViewSet."""
        svc_lines = []

        # Check actions on the viewset class
        action_map = getattr(viewset_class, "action_map", {})
        if "list" in action_map or hasattr(viewset_class, "list"):
            svc_lines.append(f"  getList: () => api.get({model_name}Endpoints.list()),")
        if "retrieve" in action_map or hasattr(viewset_class, "retrieve"):
            svc_lines.append(
                f"  getById: (id) => api.get({model_name}Endpoints.getById(id)),"
            )
        if "create" in action_map or hasattr(viewset_class, "create"):
            svc_lines.append(
                f"  create: (data) => api.post({model_name}Endpoints.create(), data),"
            )
        if "update" in action_map or hasattr(viewset_class, "update"):
            svc_lines.append(
                f"  update: (id, data) => api.put({model_name}Endpoints.update(id), data),"
            )
        if "partial_update" in action_map or hasattr(viewset_class, "partial_update"):
            svc_lines.append(
                f"  patch: (id, data) => api.patch({model_name}Endpoints.patch(id), data),"
            )
        if "destroy" in action_map or hasattr(viewset_class, "destroy"):
            svc_lines.append(
                f"  delete: (id) => api.delete({model_name}Endpoints.delete(id)),"
            )

        # Add custom actions from ViewSet
        for method_name in dir(viewset_class):
            if not method_name.startswith("_") and callable(
                getattr(viewset_class, method_name)
            ):
                # Skip standard CRUD methods and built-in DRF methods
                if method_name in [
                    "list",
                    "retrieve",
                    "create",
                    "update",
                    "partial_update",
                    "destroy",
                    "get_queryset",
                    "get_serializer_class",
                    "get_permissions",
                    "get_serializer",
                    "get_object",
                    "perform_create",
                    "perform_update",
                    "perform_destroy",
                    "filter_queryset",
                ]:
                    continue

                # Check if it's an action decorator method
                method_attr = getattr(viewset_class, method_name)
                if hasattr(method_attr, "mapping"):
                    # This is a custom action
                    # Handle MethodMapper.get() issue
                    try:
                        http_method = method_attr.mapping.get("method", "GET").lower()
                    except TypeError:
                        # Fallback if get() doesn't accept default value
                        try:
                            # Try to get the method directly
                            if "method" in method_attr.mapping:
                                http_method = method_attr.mapping["method"].lower()
                            else:
                                http_method = "get"
                        except (TypeError, KeyError):
                            # If still issues, default to get
                            http_method = "get"

                    # Handle detail property with same approach
                    try:
                        detail = method_attr.mapping.get("detail", False)
                    except TypeError:
                        # Fallback if get() doesn't accept default value
                        try:
                            if "detail" in method_attr.mapping:
                                detail = method_attr.mapping["detail"]
                            else:
                                detail = False
                        except (TypeError, KeyError):
                            detail = False

                    if detail:
                        # For detail actions, we need to get the endpoint from the action_map
                        endpoint_name = method_name
                        current_action_map = getattr(viewset_class, "action_map", {})
                        if current_action_map and method_name in current_action_map:
                            endpoint_name = method_name
                        else:
                            # Try to find the method in action_map by its URL path
                            for (
                                action_name,
                                action_details,
                            ) in current_action_map.items():
                                if (
                                    getattr(action_details, "method", None)
                                    == http_method
                                    and getattr(action_details, "detail", None)
                                    == detail
                                ):
                                    endpoint_name = action_name
                                    break

                        svc_lines.append(
                            f"  {method_name}: (id) => api.{http_method}({model_name}Endpoints.{endpoint_name}(id)),"
                        )
                    else:
                        # For list actions
                        endpoint_name = method_name
                        current_action_map = getattr(viewset_class, "action_map", {})
                        if current_action_map and method_name in current_action_map:
                            endpoint_name = method_name
                        else:
                            # Try to find the method in action_map by its URL path
                            for (
                                action_name,
                                action_details,
                            ) in current_action_map.items():
                                if (
                                    getattr(action_details, "method", None)
                                    == http_method
                                    and getattr(action_details, "detail", None)
                                    == detail
                                ):
                                    endpoint_name = action_name
                                    break

                        svc_lines.append(
                            f"  {method_name}: () => api.{http_method}({model_name}Endpoints.{endpoint_name}()),"
                        )

        return svc_lines

    def generate(self) -> None:
        """Creates endpoints.ts and individual service files dynamically based on ViewSet methods."""
        # Load service interfaces first
        self._load_service_interfaces()

        endpoints_content = []

        for router in self.data:
            for prefix, viewset_class, basename in router.registry:
                model_name = basename.capitalize().replace("-", "")

                # Generate endpoints content
                ep_lines = []
                # Check actions on the viewset class for endpoints
                action_map = getattr(viewset_class, "action_map", {})
                if "list" in action_map or hasattr(viewset_class, "list"):
                    ep_lines.append(f"  list: () => '/{prefix}/',")
                if "retrieve" in action_map or hasattr(viewset_class, "retrieve"):
                    ep_lines.append(f"  getById: (id) => `/{prefix}/${{id}}/`,")
                if "create" in action_map or hasattr(viewset_class, "create"):
                    ep_lines.append(f"  create: () => '/{prefix}/',")
                if "update" in action_map or hasattr(viewset_class, "update"):
                    ep_lines.append(f"  update: (id) => `/{prefix}/${{id}}/`,")
                if "partial_update" in action_map or hasattr(
                    viewset_class, "partial_update"
                ):
                    ep_lines.append(f"  patch: (id) => `/{prefix}/${{id}}/`,")
                if "destroy" in action_map or hasattr(viewset_class, "destroy"):
                    ep_lines.append(f"  delete: (id) => `/{prefix}/${{id}}/`,")

                # Add custom actions to endpoints
                for method_name in dir(viewset_class):
                    if not method_name.startswith("_") and callable(
                        getattr(viewset_class, method_name)
                    ):
                        # Skip standard CRUD methods and built-in DRF methods
                        if method_name in [
                            "list",
                            "retrieve",
                            "create",
                            "update",
                            "partial_update",
                            "destroy",
                            "get_queryset",
                            "get_serializer_class",
                            "get_permissions",
                            "get_serializer",
                            "get_object",
                            "perform_create",
                            "perform_update",
                            "perform_destroy",
                            "filter_queryset",
                        ]:
                            continue

                        # Check if it's an action decorator method
                        method_attr = getattr(viewset_class, method_name)
                        if hasattr(method_attr, "mapping"):
                            # This is a custom action
                            # Handle MethodMapper.get() issue
                            try:
                                http_method = method_attr.mapping.get(
                                    "method", "GET"
                                ).lower()
                            except TypeError:
                                # Fallback if get() doesn't accept default value
                                try:
                                    # Try to get the method directly
                                    if "method" in method_attr.mapping:
                                        http_method = method_attr.mapping[
                                            "method"
                                        ].lower()
                                    else:
                                        http_method = "get"
                                except (TypeError, KeyError):
                                    # If still issues, default to get
                                    http_method = "get"

                            # Handle detail property with same approach
                            try:
                                detail = method_attr.mapping.get("detail", False)
                            except TypeError:
                                # Fallback if get() doesn't accept default value
                                try:
                                    if "detail" in method_attr.mapping:
                                        detail = method_attr.mapping["detail"]
                                    else:
                                        detail = False
                                except (TypeError, KeyError):
                                    detail = False

                            if detail:
                                ep_lines.append(
                                    f"  {method_name}: (id) => `/{prefix}/${{id}}/{method_name}/`,"
                                )
                            else:
                                ep_lines.append(
                                    f"  {method_name}: () => `/{prefix}/{method_name}/`,"
                                )

                if ep_lines:  # Only add if there are endpoints
                    endpoints_content.append(
                        f"export const {model_name}Endpoints = {{\n"
                        + "\n".join(ep_lines)
                        + "\n};\n"
                    )

                    # Generate individual service file
                    svc_lines = self._generate_service_methods(
                        model_name, prefix, viewset_class
                    )
                    if svc_lines:
                        model_name_normalize = basename.replace("-", "")
                        interface_name = f"I{model_name}Service"
                        interface_filename = f"I{self.app_name}Service.ts"

                        service_file_content = [
                            f"import {{ api }} from '../../config/api';",
                            f"import {{ {interface_name} }} from './{interface_filename}';",
                            f"import {{ {model_name}Endpoints }} from './{self.app_name}.endpoints';",
                            "",
                            f"export const {model_name}Service: {interface_name} = {{",
                            *svc_lines,  # Unpack the list of method lines
                            "};",
                        ]
                        full_service_content = "\n".join(service_file_content)
                        self._write_file(
                            f"{model_name_normalize}.service.ts", full_service_content
                        )

        if endpoints_content:
            full_content = "\n".join(endpoints_content)
            self._write_file(f"{self.app_name}.endpoints.ts", full_content)
