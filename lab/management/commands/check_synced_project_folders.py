import os
import typing

import requests
import sentry_sdk
from django.core.management.base import BaseCommand

from euphro_auth.jwt.tokens import EuphroToolsAPIToken

from ...models import Project


class ResponseBody(typing.TypedDict):
    unsynced_dirs: list[str]
    orphan_dirs: list[str]


class Command(BaseCommand):
    help = "Check if project data folders are synced with project names in DB."

    def handle(self, *args, **options):
        self.stdout.write("Checking project folders are synced...")
        project_slugs = Project.objects.values_list("slug", flat=True)
        if not project_slugs:
            return
        token = EuphroToolsAPIToken.for_euphrosyne().access_token
        results: ResponseBody | None = None
        try:
            response = requests.post(
                os.environ["EUPHROSYNE_TOOLS_API_URL"] + "/data/check-folders-sync",
                json={"project_slugs": list(project_slugs)},
                timeout=5,
                headers={"Authorization": f"Bearer {token}"},
            )
            if not response.ok:
                self.stderr.write(
                    "[check-folders-sync] Request to Euphro Tools failed.\
                        \n\tReason : [%s] %s"
                    % (
                        response.status_code,
                        response.text,
                    ),
                    self.style.WARNING,
                )
                sentry_sdk.set_extra("response", response.text)
                sentry_sdk.set_extra("status_code", response.status_code)
                sentry_sdk.capture_message("Failed to check project folders sync")
                return
            results = response.json()
        except requests.exceptions.Timeout as e:
            self.stderr.write(
                "[check-folders-sync] Timeout",
                self.style.WARNING,
            )
            sentry_sdk.capture_exception(e)
            return

        if results and (results["orphan_dirs"] or results["unsynced_dirs"]):
            message = "[check-folders-sync] Folders not synced."
            self.stdout.write(
                "%s\n%s" % (message, results),
                self.style.WARNING,
            )
            sentry_sdk.set_context("folders", results)
            sentry_sdk.capture_message(message)
            return

        self.stdout.write(
            "[check-folders-sync] Folders synced. Ok.", self.style.SUCCESS
        )
