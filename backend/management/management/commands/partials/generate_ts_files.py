import os
from .interface_generator import InterfaceGenerator
from .api_generator import ApiGenerator
from .presentation_generator import PresentationGenerator
from .service_interface_generator import ServiceInterfaceGenerator


class GenerateTsFiles:
    def __init__(self, app_data, output_dir, stdout, style):
        self.app_data = app_data
        self.output_dir = output_dir
        self.stdout = stdout
        self.style = style

    def execute(self):
        """Generates the actual .ts files based on extracted data."""
        for app_name, data in self.app_data.items():
            if not data["serializers"] and not data["routers"]:
                continue

            app_dir = os.path.join(self.output_dir, app_name)
            os.makedirs(app_dir, exist_ok=True)

            generators = [
                InterfaceGenerator(
                    app_name, app_dir, self.stdout, self.style, data["serializers"]
                ),
                ServiceInterfaceGenerator(
                    app_name, app_dir, self.stdout, self.style, data["routers"]
                ),
                ApiGenerator(
                    app_name, app_dir, self.stdout, self.style, data["routers"]
                ),
                PresentationGenerator(
                    app_name,
                    app_dir,
                    self.stdout,
                    self.style,
                    data["routers"],
                    data["serializers"],
                ),
            ]
            for gen in generators:
                gen.generate()
