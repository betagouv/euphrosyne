# Project Immutability (COOL / COOLING)

This document lists what is currently blocked when
`project.lifecycle_state in {COOL, COOLING}`.

## Central rule

- Source of truth: `data_management/immutability.py`
- Lab bridge (feature-safe import): `lab/project_immutability.py`

## Backend-enforced blocks (server-side)

- Run creation is blocked (`PermissionDenied` / HTTP 403)
  - `lab/runs/admin.py` (`RunAdmin.save_model`)
- Run rename (label change) is blocked (`PermissionDenied` / HTTP 403)
  - `lab/runs/admin.py` (`RunAdmin.save_model`)
- Run planning/scheduling is blocked (`PermissionDenied` / HTTP 403)
  - `lab/runs/admin.py` (`RunAdmin._schedule_action`)
- Project rename (name change) is blocked (`PermissionDenied` / HTTP 403)
  - `lab/projects/admin.py` (`ProjectAdmin.save_model`)

## Frontend/UI-disabled behaviors

- Runs admin
  - "Create new run" / "Create a first run" buttons stay visible but are disabled
  - Run rename is disabled (run `label` becomes read-only in admin form)
  - Sources: `lab/templatetags/run_list.py`, `lab/templates/admin/lab/run/run_list.html`, `lab/templates/admin/lab/run/change_list__no_run.html`, `lab/runs/admin.py`
- Projects admin
  - Project rename is disabled (project `name` becomes read-only in admin form)
  - Source: `lab/projects/admin.py`
- Documents page
  - Upload button remains visible but is disabled
  - Upload modal remains visible but form controls are disabled
  - Delete action is disabled via `canDelete: false`
  - Sources: `lab/documents/views.py`, `lab/documents/assets/js/components/DocumentManager.tsx`, `lab/documents/assets/js/components/DocumentUploadModal.tsx`
- Workplace page
  - Raw/processed run data delete actions are disabled via `canDelete: false`
  - Source: `lab/workplace/views.py`
