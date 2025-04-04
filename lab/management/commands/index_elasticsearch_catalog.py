import logging

from django.core.management.base import BaseCommand

from ...elasticsearch.client import CatalogClient
from ...models import Project

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--skip_eros",
            action="store_true",
            help="Skip indexing of EROS-related projects",
        )

    def handle(self, *args, **options):
        projects = (
            Project.objects.only_finished()
            .only_public()
            .order_by("-created")
            .prefetch_related("runs__run_object_groups")
            .distinct()
        )
        self.stdout.write(f"Found {len(projects)} projects to index")

        # Get client instance
        catalog_client = CatalogClient()

        # Delete the index if it exists
        catalog_client.delete_index()

        # First, index all public projects (updates existing entries)
        catalog_client.index_from_projects(projects, skip_eros=options["skip_eros"])
