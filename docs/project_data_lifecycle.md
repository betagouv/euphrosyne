# Project Data Lifecycle

The `data_management` feature adds project-level data lifecycle management to
Euphrosyne. It moves inactive project data from HOT to COOL
data storage, keeps cooled projects browsable, and allows an admin to
restore a project back to the hot workspace when writes are needed again.

This document describes the implemented behavior in this repository. The product
requirements remain in [`data_management/PRD.md`](../data_management/PRD.md).

## Scope

The feature manages project data as a single unit:

- run data
- project documents
- any other files stored under the project folder

The implementation is intentionally project-scoped. There is no partial
cooling, no mixed hot/cool project contents, and no direct write path to cool
storage from Euphrosyne.

In user-facing UI, the feature is mostly described as archive/restore. In code,
the lifecycle states remain `HOT`, `COOLING`, `COOL`, `RESTORING`, and `ERROR`.

## Enablement and Configuration

The feature is optional. It is enabled by adding `data_management` to
`EUPHROSYNE_FEATURES`.

Example:

```bash
EUPHROSYNE_FEATURES=data_management,lab_notebook
```

Relevant settings:

- `EUPHROSYNE_FEATURES`
  Enables the Django app and its UI/API/admin surfaces.
- `DATA_COOLING_ENABLE`
  Enables the automatic scheduler path. If it is false, the feature can still
  be used for manual archive and restore actions.
- `EUPHROSYNE_TOOLS_API_URL`
  Base URL used for server-to-server calls to `euphrosyne-tools-api`.

Operationally, leaving `DATA_COOLING_ENABLE=false` is a valid setup when you
want the feature available but do not want automatic cooling yet.

## Domain Model

### `ProjectData`

`ProjectData` is a `OneToOne` model attached to `lab.Project`. It stores the
current lifecycle state and the project cooling eligibility date.

`ProjectData.for_project(project)` lazily creates the row when needed and
ensures `cooling_eligible_at` is populated.

### `LifecycleOperation`

`LifecycleOperation` tracks each archive or restore attempt, including status,
timing, transfer totals, copied totals, and error payloads.

The latest operation is derived from timestamps and used to drive both admin
views and the workplace panel.

## Lifecycle States and Eligibility

The lifecycle states are defined in `data_management.models.LifecycleState`:

- `HOT`
  Project data is available in the hot workspace and may be modified.
- `COOLING`
  An archive operation is running. The project is treated as read-only.
- `COOL`
  Project data is archived in cool storage. The project remains browsable but
  is read-only until restored.
- `RESTORING`
  A restore operation is running. The project remains read-only.
- `ERROR`
  The last lifecycle operation failed. Retry is allowed only when it is
  compatible with the last failed operation.

Cooling eligibility is computed in `data_management.eligibility` and stored on
`ProjectData.cooling_eligible_at`.

Implemented behavior:

- the default eligibility date is based on project creation time
- planning a new run recomputes eligibility from the run end date
- automatic cooling only considers projects that are `HOT` and already eligible

## Runtime Flows

### Manual archive

Lab admins can trigger archive from the workplace lifecycle panel. The backend
flow is:

1. `POST /api/data-management/projects/{project_id}/cool`
2. `trigger_cool_operation(...)` creates a `LifecycleOperation`
3. Euphrosyne calls `euphrosyne-tools-api`
4. after the tools API accepts the request, the project state becomes
   `COOLING` and the operation becomes `RUNNING`
5. completion is finalized only when the callback is received and verified

The same operation semantics also back admin-visible state and retry behavior.

### Scheduled cooling

Automatic archive is handled by `data_management.scheduler.run_cooling_scheduler`.

Selection rules:

- `DATA_COOLING_ENABLE` must be true
- project must currently be `HOT`
- `cooling_eligible_at` must be in the past
- no active cooling operation may already exist

The scheduler creates pending operations in the database first, then dispatches
network requests outside the row-locking transaction.

Operational entrypoints:

- `python manage.py schedule_project_cooling`
- `python manage.py run_checks`

`run_checks` invokes `schedule_project_cooling` when `data_management` is
installed.

### Restore

Lab admins can trigger restore from the workplace lifecycle panel when a project
is `COOL`.

The backend flow mirrors archive:

1. `POST /api/data-management/projects/{project_id}/restore`
2. `trigger_restore_operation(...)` creates a `LifecycleOperation`
3. Euphrosyne calls `euphrosyne-tools-api`
4. after acceptance, the project becomes `RESTORING`
5. callback verification is required before the project returns to `HOT`

### Admin-triggered source data deletion

Lab admins can trigger source data deletion from the `LifecycleOperation`
changelist in Django admin after a successful `COOL` operation.

The backend flow is:

1. admin confirms the `Delete source data` bulk action
2. Euphrosyne validates the selected operation:
   - type must be `COOL`
   - status must be `SUCCEEDED`
   - project lifecycle state must be `COOL`
   - source-data deletion state must be `NOT_REQUESTED` or `FAILED`
   - no other lifecycle operation may be active for the project
3. the existing `LifecycleOperation` is updated with:
   - `from_data_deletion_status=RUNNING`
   - `from_data_deletion_error=NULL`
   - `from_data_deleted_at=NULL`
4. Euphrosyne calls `euphrosyne-tools-api`
5. the admin request returns immediately after asynchronous acceptance

Deletion is intentionally tracked as a sub-status of the lifecycle operation.
It does not create a new operation row, and it does not change the project
lifecycle state.

### Callback completion and verification

`POST /api/data-management/operations/callback` is the final authority for
marking an operation as succeeded or failed.

Success path:

- callback payload includes copied totals and optional total counts
- Euphrosyne stores these values on the operation
- `verify_operation(...)` requires copied totals to exactly match total values
- only a verified success can transition:
  - `COOLING -> COOL`
  - `RESTORING -> HOT`

Failure path:

- failed callbacks store `error_message`, serialized `error_details`, and
  `finished_at`
- verification mismatches are converted into a structured failure payload
- the project transitions to `ERROR` when allowed

Once an operation is already terminal (`SUCCEEDED` or `FAILED`), later callback
retries are treated as no-op `200 OK` responses.

Deletion callback path:

- callback payload sets `phase=FROM_DATA_DELETION`
- callback payload also includes:
  - `from_data_deletion_status`
  - optional `error`
- Euphrosyne updates only:
  - `from_data_deletion_status`
  - `from_data_deleted_at`
  - `from_data_deletion_error`
- Euphrosyne does not modify:
  - `operation.status`
  - `project_data.lifecycle_state`
- repeated deletion callbacks are no-op once deletion is already terminal

## Immutability Rules

The feature treats the following states as immutable:

- `COOL`
- `COOLING`
- `RESTORING`
- `ERROR`

This is implemented in `data_management.immutability` and consumed from the lab
app through `lab.project_immutability`.

Practical effects in this repository:

- document uploads are disabled
- document deletion is disabled
- project document pages remain browsable
- run data deletion is disabled in the workplace
- new runs are blocked by permission checks
- starting the virtual office is blocked when the project is immutable

In short: cooled projects stay visible, but write-capable actions are withheld
until the project is restored to `HOT`.

## Public Interfaces

### Django API

All routes are mounted under `/api/data-management/`.

#### `POST /api/data-management/projects/{project_id}/cool`

- purpose: trigger an archive operation
- permission: lab admin only (`IsLabAdminUser`)
- response:
  - `202 Accepted` with `operation_id` and `lifecycle_state=COOLING`
  - `400 Bad Request` when the lifecycle state does not allow archive
  - `502 Bad Gateway` when the tools API call could not be started

#### `POST /api/data-management/projects/{project_id}/restore`

- purpose: trigger a restore operation
- permission: lab admin only (`IsLabAdminUser`)
- response:
  - `202 Accepted` with `operation_id` and `lifecycle_state=RESTORING`
  - `400 Bad Request` when the lifecycle state does not allow restore
  - `502 Bad Gateway` when the tools API call could not be started

#### `GET /api/data-management/projects/{project_slug}/lifecycle`

- purpose: expose current lifecycle state for workplace UI and other consumers
- permission:
  - project member
  - lab admin
  - backend service account (`euphrosyne`)
- response:
  - `200 OK` with `lifecycle_state`, `last_operation_id`,
    `last_operation_type`

#### `GET /api/data-management/operations/{operation_id}`

- purpose: fetch archive/restore progress and error details
- permission: lab admin only (`IsLabAdminUser`)
- response:
  - `200 OK` with operation detail payload
  - `404 Not Found` when the operation does not exist

#### `POST /api/data-management/operations/callback`

- purpose: receive final status from `euphrosyne-tools-api`
- authentication:
  - `EuphrosyneAdminJWTAuthentication`
  - authenticated request required
- response:
  - `200 OK` on success and on repeated callback for a terminal operation
  - `404 Not Found` if the operation is unknown

### Euphrosyne to tools-api contract

This repository currently initiates lifecycle operations through:

- `POST data/projects/{project_slug}/cool?operation_id={operation_id}`
- `POST data/projects/{project_slug}/restore?operation_id={operation_id}`
- `POST data/projects/{project_slug}/delete/{storage_role}?operation_id={operation_id}&file_count={files_total}&total_size={bytes_total}`

These requests are sent by `euphro_tools.project_data` using the shared tools
API authentication header.

For deletion requests, `storage_role` is the inactive side to delete, while
`file_count` and `total_size` are the verified retained-side totals from the
completed lifecycle operation. `total_size` is expressed in bytes.

The implementation assumes the tools API will:

- accept the request asynchronously with `202 Accepted`
- execute the storage operation out of band
- call back into Euphrosyne using the callback endpoint above
- provide counts that allow Euphrosyne to verify success before state changes

## Admin and UI Surfaces

### Admin navigation

When `data_management` is installed, lab admins get a new Admin navigation item:

- `Project data lifecycle`

It points to the `ProjectData` changelist in Django admin.

### Admin changelist

The `ProjectData` admin changelist provides:

- project link
- lifecycle state badge
- cooling eligibility date
- last operation lifecycle summary
- last operation timestamp

The changelist is read-only. Opening a project row redirects to the project
workplace rather than a model edit form.

The `LifecycleOperation` changelist remains read-only as well, but now exposes
an admin-only bulk action:

- `Delete source data`

The action shows a confirmation page before dispatching deletion requests. The
change form and changelist also display:

- `from_data_deletion_status`
- `from_data_deleted_at`
- `from_data_deletion_error`

### Workplace

The workplace page now exposes lifecycle state to the frontend and renders a
project lifecycle panel for lab admins.

The panel supports:

- archive action when the project is `HOT`
- restore action when the project is `COOL`
- error display and retry action when the project is `ERROR`

The workplace also uses lifecycle state to disable write-capable behaviors such
as VM startup and run-data deletion.

## Failure and Retry Semantics

The implementation is intentionally strict about state transitions.

- only one active lifecycle operation is allowed at a time
- invalid source states are rejected before contacting the tools API
- failed start requests create failed operations and surface `502`
- projects only transition to `COOL` or `HOT` after verified success
- failure transitions move the project to `ERROR` when valid

Retry rules are operation-aware:

- archive can be retried from `ERROR` only if the last failed operation was
  `COOL`
- restore can be retried from `ERROR` only if the last failed operation was
  `RESTORE`
- source-data deletion can be retried only from
  `from_data_deletion_status=FAILED`

This keeps retry semantics aligned with the last known storage transition.

## Operational Commands

### `python manage.py schedule_project_cooling`

Use this for batch scheduling of eligible projects. It is the normal
operator-facing entrypoint for automatic cooling.

### `python manage.py cool_project <project_slug>`

Use this for targeted manual dispatch of a cooling operation for one project.
It is useful for operational intervention or testing a specific project flow.
The command only dispatches projects currently in `HOT`.
