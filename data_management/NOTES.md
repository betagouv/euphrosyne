- We should make a script in ProjectData migrations to populate existing Project instances with corresponding ProjectData records.
- TASK restore endpoint note: `ProjectData` currently has no `last_lifecycle_operation_id`,
  `project_size_bytes`, or `file_count` fields (removed by migration `0002`), so restore
  trigger stores operation linkage via `LifecycleOperation.project_data` only and leaves
  `bytes_total/files_total` unset unless provided elsewhere.
