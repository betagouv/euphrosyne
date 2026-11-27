from datetime import timedelta

from django.core.management.base import BaseCommand

from data_management.reconciliation import (
    fail_stale_lifecycle_operations,
    get_stale_after,
)


class Command(BaseCommand):
    help = (
        "Fail lifecycle operations that never received a completion callback "
        "and move their project to ERROR so they can be retried."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--stale-after-hours",
            type=float,
            default=None,
            help=(
                "Consider an operation stale after this many hours "
                "(default: DATA_LIFECYCLE_OPERATION_TIMEOUT_HOURS, 6)."
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List stale operations without changing anything.",
        )

    def handle(self, *args, **options) -> None:
        stale_after_hours = options["stale_after_hours"]
        stale_after = (
            timedelta(hours=stale_after_hours)
            if stale_after_hours is not None
            else get_stale_after()
        )
        dry_run = options["dry_run"]

        stale_operations = fail_stale_lifecycle_operations(
            stale_after=stale_after, dry_run=dry_run
        )

        for stale in stale_operations:
            self.stdout.write(
                "%s%s %s (%s, started %s)%s"
                % (
                    "[dry-run] " if dry_run else "",
                    stale.operation_id,
                    stale.project_slug,
                    stale.type,
                    stale.started_at,
                    ", project set to ERROR" if stale.project_moved_to_error else "",
                )
            )
        self.stdout.write(
            self.style.SUCCESS(
                "%s %s stale lifecycle operation(s)."
                % ("Found" if dry_run else "Failed", len(stale_operations))
            )
        )
