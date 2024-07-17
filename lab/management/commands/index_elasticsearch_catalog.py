import logging

from django.core.management.base import BaseCommand

from ...elasticsearch.client import CatalogClient
from ...models import Project

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        projects = (
            Project.objects.only_finished()
            .only_public()
            .order_by("-created")
            .prefetch_related("runs__run_object_groups")
            .distinct()
        )
        self.stdout.write(f"Found {len(projects)} projects to index")

        CatalogClient().index_from_projects(projects)
