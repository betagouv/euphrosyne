## Context
PRD – Data model changes

## Description
Add:
- project_run_data table (storage_class, lifecycle_state, cooling_eligible_at, run_size_bytes, file_count, last_lifecycle_operation_id, last_lifecycle_error)
- lifecycle_operation table (operation_id, run_id, type, status, started_at/finished_at, bytes/files totals and copied, error fields)

## Acceptance criteria
- Migrations created and applied
- Enums for lifecycle state and operation status/type exist
- Useful indexes added (lifecycle_state, cooling_eligible_at)

## Notes
- Implementation links lifecycle operations to `RunData` instead of directly to `Run` (requested change vs PRD/TASK wording).
