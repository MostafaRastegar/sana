import os
from abc import ABC, abstractmethod
from typing import Any


# --- Abstract Base Class for Generators ---
class BaseTsGenerator(ABC):
    """
    Abstract base class for all TypeScript file generators.
    Ensures a common interface for generating different types of TS files.
    """

    def __init__(self, app_name: str, app_dir: str, stdout: Any, style: Any):
        self.app_name = app_name
        self.app_dir = app_dir
        self.stdout = stdout
        self.style = style

    @abstractmethod
    def generate(self) -> None:
        """
        Abstract method to generate TypeScript content.
        Subclasses must implement this to define their specific generation logic.
        """
        pass

    def _write_file(self, filename: str, content: str) -> None:
        """
        Helper method to write content to a file within the app's directory.
        """
        filepath = os.path.join(self.app_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.stdout.write(self.style.SUCCESS(f"Successfully generated: {filepath}"))
        except IOError as e:
            self.stdout.write(self.style.ERROR(f"Error writing file {filepath}: {e}"))
