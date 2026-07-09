from typing import Any, List
from .drf_mapper import map_drf_type_to_ts
from .base import BaseTsGenerator


class ServiceInterfaceGenerator(BaseTsGenerator):
    """
    Generates 'service-interfaces.ts' file containing TypeScript interfaces for API services.
    Defines the contract for each service with method signatures, parameters, and return types.
    """

    def __init__(
        self, app_name: str, app_dir: str, stdout: Any, style: Any, data: List[Any]
    ):
        super().__init__(app_name, app_dir, stdout, style)
        self.data = data

    def _generate_service_interface_methods(
        self, model_name: str, prefix: str, viewset_class: type
    ) -> list[str]:
        """Generates TypeScript service interface method lines for a given model and ViewSet."""
        interface_lines = []

        # Check actions on the viewset class
        action_map = getattr(viewset_class, "action_map", {})
        if "list" in action_map or hasattr(viewset_class, "list"):
            interface_lines.append(f"    getList(): Promise<{model_name}Model[]>;")
        if "retrieve" in action_map or hasattr(viewset_class, "retrieve"):
            interface_lines.append(
                f"    getById(id: number | string): Promise<{model_name}Model>;"
            )
        if "create" in action_map or hasattr(viewset_class, "create"):
            interface_lines.append(
                f"    create(data: {model_name}Request): Promise<{model_name}Model>;"
            )
        if "update" in action_map or hasattr(viewset_class, "update"):
            interface_lines.append(
                f"    update(id: number | string, data: {model_name}Request): Promise<{model_name}Model>;"
            )
        if "partial_update" in action_map or hasattr(viewset_class, "partial_update"):
            interface_lines.append(
                f"    patch(id: number | string, data: Partial<{model_name}Request>): Promise<{model_name}Model>;"
            )
        if "destroy" in action_map or hasattr(viewset_class, "destroy"):
            interface_lines.append(f"    delete(id: number | string): Promise<void>;")

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
                        interface_lines.append(
                            f"    {method_name}(id: number | string): Promise<any>;"
                        )
                    else:
                        interface_lines.append(f"    {method_name}(): Promise<any>;")

        return interface_lines

    def generate(self) -> None:
        """Creates service-interfaces.ts file with interface definitions for all services."""
        interfaces_content = []

        for router in self.data:
            for prefix, viewset_class, basename in router.registry:
                model_name = basename.capitalize().replace("-", "")

                # Generate interface content
                interface_lines = self._generate_service_interface_methods(
                    model_name, prefix, viewset_class
                )

                if interface_lines:  # Only add if there are methods
                    interface_name = f"I{model_name}Service"
                    interface_lines_str = "\n".join(interface_lines)
                    interface_content = (
                        f"export interface {interface_name} {{\n"
                        f"{interface_lines_str}\n"
                        "};\n"
                    )
                    interfaces_content.append(interface_content)

        if interfaces_content:
            full_content = "\n".join(interfaces_content)
            interface_filename = f"I{self.app_name}Service.ts"
            self._write_file(interface_filename, full_content)
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No service interfaces generated for {self.app_name}."
                )
            )
