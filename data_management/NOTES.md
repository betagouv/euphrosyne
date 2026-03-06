- We should make a script in ProjectData migrations to populate existing Project instances with corresponding ProjectData records.
- TASK restore endpoint note: `ProjectData` currently has no `last_lifecycle_operation_id`,
  `project_size_bytes`, or `file_count` fields (removed by migration `0002`), so restore
  trigger stores operation linkage via `LifecycleOperation.project_data` only and leaves
  `bytes_total/files_total` unset unless provided elsewhere.
- Workplace lifecycle UI relies on tools-api `/data/operations/{operation_id}` payload fields for status/metrics/error title. The UI accepts both snake_case and camelCase keys and parses JSON-encoded `error_details` defensively because the payload contract is not yet documented in this repo.
