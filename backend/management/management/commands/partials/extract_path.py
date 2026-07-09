from rest_framework import routers, serializers
import importlib
from typing import Any


class ExtractPath:
    def __init__(
        self,
        project_apps: list[str],
        app_data: dict[str, dict[str, list[Any]]],
    ):
        self.app_data = app_data
        self.project_apps = project_apps

    def extract_routers(self):
        """Finds all registered routers in app urls."""
        for app_name in self.project_apps:
            try:
                module = importlib.import_module(f"{app_name}.urls")
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if isinstance(item, routers.BaseRouter):
                        self.app_data[app_name]["routers"].append(item)
            except ModuleNotFoundError:
                continue

    def extract_serializers(self):
        """Finds all DRF serializers in installed apps."""
        for app_name in self.project_apps:
            try:
                module = importlib.import_module(f"{app_name}.serializers")
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (
                        isinstance(item, type)
                        and issubclass(item, serializers.Serializer)
                        and item is not serializers.Serializer
                    ):
                        self.app_data[app_name]["serializers"].append(item)
            except ModuleNotFoundError:
                continue
