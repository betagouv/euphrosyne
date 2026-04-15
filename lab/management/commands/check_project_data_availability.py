import os

import requests
import sentry_sdk
from django.apps import apps
from django.core.management.base import BaseCommand

from euphro_auth.jwt.tokens import EuphroToolsAPIToken

from ...models import Project


class Command(BaseCommand):
    help = "Check if data is available for projects with finished status."

    def handle(self, *args, **options):
        projects = Project.objects.only_finished().filter(is_data_available=False)

        # If cooling project data is enable, we just check HOT projects
        # because euphro-tools can call write methods during this check
        # whick is not permited for non HOT data
        if apps.is_installed("data_management"):
            # pylint: disable=import-outside-toplevel
            from data_management.models import (
                LifecycleState,
            )

            projects = projects.filter(project_data__lifecycle_state=LifecycleState.HOT)
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
                    + f"/data/available/{project.slug}",
                    timeout=10,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if not response.ok:
                    self.stderr.write(
                        "[data availability] Failed to check project %s.\
                            \n\tReason : [%s] %s"
                        % (
                            project.slug,
                            response.status_code,
                            response.text,
                        ),
                        self.style.WARNING,
                    )
                    sentry_sdk.set_extra("response", response.text)
                    sentry_sdk.set_extra("status_code", response.status_code)
                    sentry_sdk.capture_message(
                        "Failed to check project data availability",
                        level="error",
                    )
                    continue
                if response.json()["available"]:
                    project.is_data_available = True
                    project.save()
            except requests.exceptions.Timeout as e:
                self.stderr.write(
                    "[data availability] Timeout for project %s" % project.name,
                    self.style.WARNING,
                )
                sentry_sdk.capture_exception(e)
                continue

        self.stdout.write(
            self.style.SUCCESS(
                "[data availability] Checked %s projects" % len(projects)
            )
        )
