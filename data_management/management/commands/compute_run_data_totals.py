from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand
from django.db.models import Q, QuerySet

from data_management.models import RunData
from euphro_tools.exceptions import EuphroToolsException
from euphro_tools.run_data import RunDataTotals, compute_run_data_totals
from lab.runs.models import Run


class Command(BaseCommand):
    help = "Compute run_size_bytes and file_count for finished runs."

    def handle(self, *args: Any, **options: Any) -> None:
        run_data_qs: QuerySet[RunData] = RunData.objects.select_related(
            "run", "run__project"
        ).filter(
            run__status=Run.Status.FINISHED,
        )
        run_data_qs = run_data_qs.filter(
            Q(run_size_bytes__isnull=True) | Q(file_count__isnull=True)
        )
        attempted = 0
        updated = 0
        failed = 0
        for run_data in run_data_qs:
            attempted += 1
            run = run_data.run
            try:
                totals: RunDataTotals = compute_run_data_totals(
                    run.project.slug, run.label
                )
            except EuphroToolsException as exc:
                failed += 1
                self.stderr.write(
                    "[run-data] Failed to compute totals for run " f"{run.id}: {exc}"
                )
                continue
            run_data.run_size_bytes = totals.bytes_total
            run_data.file_count = totals.files_total
            run_data.save(update_fields=["run_size_bytes", "file_count"])
            updated += 1

        if attempted == 0:
            self.stdout.write("No run data totals to compute.")
            return

        self.stdout.write(
            self.style.SUCCESS(f"Computed run data totals for {updated} run(s).")
        )
        if failed:
            self.stderr.write(
                f"[run-data] Failed to compute totals for {failed} run(s)."
            )
