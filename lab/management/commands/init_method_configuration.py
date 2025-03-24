import argparse
import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from lab.methods.models import (
    AnalysisMethod,
    DetectorType,
    FilterOption,
    FilterSet,
    create_default_new_aglae_configuration,
)


class Command(BaseCommand):
    help = "Initializes the method configuration for a specific machine"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-json",
            type=str,
            help="Initialize from a JSON file",
            dest="json_file",
        )
        parser.add_argument(
            "--default",
            action="store_true",
            help="Initialize with the default New Aglae configuration",
            dest="default",
        )

    def handle(self, *args, **options):
        if options["default"]:
            self.stdout.write("Initializing with default New Aglae configuration...")
            create_default_new_aglae_configuration()
            self.stdout.write(self.style.SUCCESS("Successfully initialized method configuration"))
            return

        if options["json_file"]:
            json_file = options["json_file"]
            if not os.path.exists(json_file):
                raise CommandError(f"JSON file {json_file} does not exist")

            self.stdout.write(f"Initializing from JSON file {json_file}...")
            with open(json_file, "r") as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError as e:
                    raise CommandError(f"Invalid JSON file: {e}")

            self._create_configuration_from_json(config)
            self.stdout.write(self.style.SUCCESS("Successfully initialized method configuration"))
            return

        # If no options are provided, show a message
        self.stdout.write(
            "No initialization options provided. Use --default or --from-json to initialize the method configuration."
        )

    def _create_configuration_from_json(self, config):
        """
        Creates a method configuration from a JSON structure.
        
        Expected format:
        {
            "methods": [
                {
                    "name": "Method Name",
                    "description": "Method description",
                    "detectors": [
                        {
                            "name": "Detector Name",
                            "is_other_field": false,
                            "filters": ["Filter 1", "Filter 2"]
                        }
                    ]
                }
            ]
        }
        """
        methods = config.get("methods", [])
        if not methods:
            raise CommandError("No methods defined in the JSON file")

        for method_data in methods:
            method_name = method_data.get("name")
            if not method_name:
                self.stderr.write("Skipping method without a name")
                continue

            method_field_name = f"method_{slugify(method_name).replace('-', '_')}"
            method, created = AnalysisMethod.objects.get_or_create(
                name=method_name,
                field_name=method_field_name,
                defaults={"description": method_data.get("description", "")},
            )

            if created:
                self.stdout.write(f"Created method: {method_name}")
            else:
                self.stdout.write(f"Found existing method: {method_name}")

            for detector_data in method_data.get("detectors", []):
                detector_name = detector_data.get("name")
                if not detector_name:
                    self.stderr.write(f"Skipping detector without a name for method {method_name}")
                    continue

                detector_field_name = (
                    f"detector_{slugify(method_name).replace('-', '_')}_{slugify(detector_name).replace('-', '_')}"
                )
                is_other_field = detector_data.get("is_other_field", False)

                detector, created = DetectorType.objects.get_or_create(
                    method=method,
                    name=detector_name,
                    defaults={
                        "field_name": detector_field_name,
                        "is_other_field": is_other_field,
                    },
                )

                if created:
                    self.stdout.write(f"  Created detector: {detector_name}")
                else:
                    self.stdout.write(f"  Found existing detector: {detector_name}")

                # Create or update the filter set if filters are defined
                filters = detector_data.get("filters", [])
                if filters:
                    filter_field_name = f"filters_for_detector_{slugify(detector_name).replace('-', '_')}"
                    filter_set, created = FilterSet.objects.get_or_create(
                        detector=detector,
                        defaults={"field_name": filter_field_name},
                    )

                    if created:
                        self.stdout.write(f"    Created filter set for detector {detector_name}")
                    else:
                        self.stdout.write(f"    Found existing filter set for detector {detector_name}")

                    # Create filter options
                    for filter_name in filters:
                        filter_option, created = FilterOption.objects.get_or_create(
                            detector=detector,
                            name=filter_name,
                        )

                        if created:
                            self.stdout.write(f"      Created filter option: {filter_name}")
                        else:
                            self.stdout.write(f"      Found existing filter option: {filter_name}")