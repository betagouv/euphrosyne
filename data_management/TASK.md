## [TASK] Implement Euphrosyne RESTORE endpoint (admin-triggered) that starts tools-api restore operation

### Context

Project data lifecycle is tracked at **project level** with states `HOT / COOLING / COOL / RESTORING / ERROR`, and **RESTORE** copies data from **Blob Cool → Azure Files** via `euphrosyne-tools-api` (AzCopy).

This task is specifically about adding the **Euphrosyne backend endpoint** used by the **admin panel** to trigger a restore (UI work is out of scope).

---

### Scope

**In scope**

- Euphrosyne backend **RESTORE endpoint** implementation (admin-triggered)
- Create a `RESTORE` lifecycle operation in Euphrosyne DB
- Call `euphrosyne-tools-api` `POST /data/projects/{project_slug}/restore` (returns `202`)
- Return `202 ACCEPTED` from Euphrosyne

**Out of scope**

- UI integration / frontend
- Operation callback handling / reconciliation (handled by other tasks/components)

---

### Description

Implement an admin-only endpoint in **Euphrosyne** (route name/path should match existing API conventions in the repo) that:

1. **Authorizes** the caller as an **admin** (admin panel use-case).
2. **Validates** project lifecycle state:
   - Allowed: `COOL` (restore makes sense)
   - Optional: allow `ERROR` if last op failed and we want to let admins restore anyway (still creates a new `operation_id`)
   - Reject: `HOT` (nothing to restore), and typically reject `COOLING/RESTORING` (operation already running)

3. **Creates a new lifecycle operation** row:
   - `type = RESTORE`
   - `operation_id = uuid`
   - status set to initial value used by the existing state machine (e.g. `PENDING` or `RUNNING`, depending on current conventions)
   - stores expected totals if available (`bytes_total/files_total`) from project lifecycle fields (if those are already computed and stored)

4. **Moves the project to `RESTORING`** in DB and sets `last_lifecycle_operation_id` accordingly (again, following existing model conventions).
5. **Calls tools-api**:
   - `POST /data/projects/{project_slug}/restore` (empty body)
   - Treat tools-api response as “accepted and running async” (it returns `202`)

6. **Returns `202 ACCEPTED`** from Euphrosyne with a payload that includes at least:
   - `operation_id`
   - current `lifecycle_state` (should now be `RESTORING`)
   - optionally: a URL to fetch operation status (if such endpoint exists in Euphrosyne)

**Error handling**

- If tools-api call fails (network/5xx/unexpected), persist a meaningful error on:
  - the lifecycle operation (mark failed if your workflow does that immediately), and/or
  - project `last_lifecycle_error`
  - and return an appropriate HTTP error to the caller (while keeping DB consistent).

- Do **not** reuse `operation_id` for retries: each trigger creates a new operation id.

---

### Acceptance criteria

- Admin-only RESTORE endpoint exists in Euphrosyne backend and is reachable by the admin panel (UI not implemented here).
- When called on a `COOL` project:
  - Creates a new `RESTORE` lifecycle operation (`operation_id` generated)
  - Transitions project lifecycle state to `RESTORING`
  - Calls `euphrosyne-tools-api` `POST /data/projects/{project_slug}/restore` and handles its `202` response
  - Returns `202 ACCEPTED` with `operation_id`

- When called on invalid states (`HOT`, `COOLING`, `RESTORING`), the endpoint returns a clear `4xx` response and does not start a new operation.
- Automated tests cover:
  - authorization (admin required)
  - state validation
  - DB rows created / state transition performed
  - tools-api client invoked
  - failure path when tools-api is unavailable
