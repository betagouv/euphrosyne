import os

import requests
from django.core.management.base import BaseCommand

from euphro_auth.jwt.tokens import EuphroToolsAPIToken

from ...models import Project


class Command(BaseCommand):
    help = "Check if data is available for projects with finished status."

    def handle(self, *args, **options):
        projects = Project.objects.only_finished().filter(is_data_available=False)
        if not projects:
            return
        token = EuphroToolsAPIToken.for_euphrosyne().access_token
        for project in projects:
            self.stdout.write(
                "[data availability] Checking project %s" % project.name,
            )

            try:
                response = requests.get(
                    os.environ["EUPHROSYNE_TOOLS_API_URL"]
                    + f"/data/available/{project.name}",
                    timeout=5,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if not response.ok:
                    self.stderr.write(
                        "[data availability] Failed to check project %s.\n\tReason : [%s] %s"
                        % (
                            project.name,
                            response.status_code,
                            response.text,
                        ),
                        self.style.WARNING,
                    )
                    continue
                if response.json()["available"]:
                    project.is_data_available = True
                    project.save()
            except requests.exceptions.Timeout:
                self.stderr.write(
                    "[data availability] Timeout for project %s" % project.name,
                    self.style.WARNING,
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                "[data availability] Checked %s projects" % len(projects)
            )
        )
