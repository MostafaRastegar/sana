from typing import Any, List
from .drf_mapper import map_drf_type_to_ts
from .base import BaseTsGenerator


# --- Interface Generator ---
class InterfaceGenerator(BaseTsGenerator):
    """
    Generates 'interfaces.ts' file from DRF serializers.
    Handles mapping DRF fields to TypeScript types and differentiating
    between model interfaces and request interfaces.
    """

    def __init__(
        self, app_name: str, app_dir: str, stdout: Any, style: Any, data: List[Any]
    ):
        super().__init__(app_name, app_dir, stdout, style)
        self.data = data

    def _get_model_interface_name(self, serializer_class_name: str) -> str:
        """Derives the TS Model interface name from the serializer class name."""
        if serializer_class_name.endswith("Serializer"):
            return serializer_class_name[: -len("Serializer")] + "Model"
        return serializer_class_name + "Model"  # Fallback

    def _get_request_interface_name(self, serializer_class_name: str) -> str:
        """Derives the TS Request interface name from the serializer class name."""
        if serializer_class_name.endswith("Serializer"):
            return serializer_class_name[: -len("Serializer")] + "Request"
        return serializer_class_name + "Request"  # Fallback

    def _generate_ts_type(self, field: Any) -> str:
        """Maps a DRF field to its TypeScript type using the configured mapper."""
        try:
            return map_drf_type_to_ts(field)
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f"Could not map field type for {field}: {e}. Falling back to 'any'."
                )
            )
            return "any"

    def generate(self) -> None:
        """
        Generates the content for 'interfaces.ts'.
        """
        interfaces_content: List[str] = []
        has_interfaces = False

        for serializer_class in self.data:
            serializer_name = serializer_class.__name__
            serializer_instance = None
            try:
                # Instantiate the serializer to access its fields
                serializer_instance = serializer_class()
                # Ensure fields are accessible
                if not hasattr(serializer_instance, "fields"):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Serializer {serializer_name} has no 'fields' attribute. Skipping."
                        )
                    )
                    continue

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Could not instantiate serializer {serializer_name}: {e}. Skipping."
                    )
                )
                continue

            # Check for Meta class and abstract status
            meta = getattr(serializer_instance, "Meta", None)
            if meta and getattr(meta, "abstract", False):
                self.stdout.write(
                    self.style.WARNING(
                        f"Abstract serializer {serializer_name} found. Skipping."
                    )
                )
                continue

            model_interface_name = self._get_model_interface_name(serializer_name)
            request_interface_name = self._get_request_interface_name(serializer_name)

            model_fields_ts: List[str] = []
            request_fields_ts: List[str] = []

            # Iterate over serializer fields
            for field_name, field in serializer_instance.fields.items():
                ts_type = self._generate_ts_type(field)
                is_required = getattr(field, "required", True)
                is_read_only = getattr(field, "read_only", False)

                # Add to model interface
                model_fields_ts.append(f"    {field_name}: {ts_type};")

                # Add to request interface, excluding read_only fields
                if not is_read_only:
                    optional_marker = "?" if not is_required else ""
                    request_fields_ts.append(
                        f"    {field_name}{optional_marker}: {ts_type};"
                    )

            if model_fields_ts:
                has_interfaces = True
                interfaces_content.append(f"export interface {model_interface_name} {{")
                interfaces_content.extend(model_fields_ts)
                interfaces_content.append("}\n")

            if request_fields_ts:
                has_interfaces = True
                interfaces_content.append(
                    f"export interface {request_interface_name} {{"
                )
                interfaces_content.extend(request_fields_ts)
                interfaces_content.append("}\n")

        if has_interfaces:
            full_content = "\n".join(interfaces_content)
            self._write_file(f"{self.app_name}.interfaces.ts", full_content)
        else:
            self.stdout.write(
                self.style.SUCCESS(f"No interfaces generated for {self.app_name}.")
            )
