import os
from datetime import datetime, timedelta, timezone

import requests
import sentry_sdk
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from euphro_auth.jwt.tokens import EuphroToolsAPIToken
from lab.emails import send_long_lasting_email

from ...models import Project


def _get_project_slug_from_vm_name(vm_name: str):
    return vm_name.split("-vm-")[1]


class Command(BaseCommand):
    help = "Check if some VMs have been running for a long time."

    def add_arguments(self, parser):
        parser.add_argument(
            "elapsed_time",
            type=int,
            help="Check VMs started after this time (in minutes).",
        )

        parser.add_argument(
            "--send-alerts",
            action="store_true",
            help="Send alerts to project owners and admin if any VM has been running for a long time.",  # pylint: disable=line-too-long
        )

    def handle(self, *args, **options):
        token = EuphroToolsAPIToken.for_euphrosyne().access_token
        self.stdout.write(
            "[long running vms] Making request to Euphrosyne Tools",
        )

        started_from = datetime.now(timezone.utc) - timedelta(
            minutes=options["elapsed_time"]
        )
        # Format without space before timezone to avoid parsing error
        formatted_time = started_from.strftime("%Y-%m-%dT%H:%M:%SZ")
        response = requests.get(
            os.environ["EUPHROSYNE_TOOLS_API_URL"]
            + f"/vms?created_before={formatted_time}",
            timeout=5,
            headers={"Authorization": f"Bearer {token}"},
        )
        if not response.ok:
            self.stderr.write(
                "[long running vms] Failed to list vms.\
                    \n\tReason : [%s] %s"
                % (
                    response.status_code,
                    response.text,
                ),
                self.style.ERROR,
            )
            sentry_sdk.set_extra("response", response.text)
            sentry_sdk.set_extra("status_code", response.status_code)
            sentry_sdk.capture_message(
                "Failed to list vms",
                level="error",
            )
            return
        vms = response.json()
        if not vms:
            self.stdout.write(
                self.style.SUCCESS(
                    "[long running vms] No long running VM found. Exciting."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                "[long running vms] Found %s VMs: %s" % (len(vms), ",".join(vms)),
            )
        )

        if options["send_alerts"]:
            vm_admin_emails = Group.objects.get(name="vm admin").user_set.values_list(
                "email", flat=True
            )
            if not vm_admin_emails:
                self.stdout.write(
                    self.style.WARNING(
                        "[long running vms] No VM admin found. Not sending email."
                    )
                )
                return
            for vm in vms:
                project = Project.objects.get(
                    slug=_get_project_slug_from_vm_name(vm),
                )
                send_long_lasting_email(list(vm_admin_emails), project)
