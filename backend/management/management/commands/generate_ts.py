from django.core.management.base import BaseCommand
from django.apps import apps
from .partials.extract_path import ExtractPath
from .partials.generate_ts_files import GenerateTsFiles


class Command(BaseCommand):
    help = "Generate TypeScript files (Interfaces, Endpoints, Services, Presentation) from DRF serializers and routers."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="frontend/modules",
            help="Output directory for TypeScript files",
        )

    def handle(self, *args, **options):
        output_dir = options["output"]
        project_apps: list[str] = [
            app.name
            for app in apps.get_app_configs()
            if not app.name.startswith("django.")
        ]

        app_data = {app: {"serializers": [], "routers": []} for app in project_apps}

        # Data structure to hold app-specific data
        extract_path: ExtractPath = ExtractPath(project_apps, app_data)
        extract_path.extract_serializers()
        extract_path.extract_routers()

        generate_ts_files = GenerateTsFiles(
            app_data, output_dir, self.stdout, self.style
        )

        generate_ts_files.execute()
