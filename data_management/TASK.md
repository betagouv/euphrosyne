## [TASK] Implement `GET /data/operations/{operation_id}` (operation status + stats + errors)

### Context

The Hot→Cool feature tracks long-running **lifecycle operations** (`COOL`, `RESTORE`) in Euphrosyne DB with:

- `operation_id` (uuid)
- `project_id`
- `type` (`COOL` / `RESTORE`)
- `status` (`PENDING` / `RUNNING` / `SUCCEEDED` / `FAILED`)
- timestamps
- `bytes_total/files_total`, `bytes_copied/files_copied`
- error details

This endpoint is needed to expose **operation status, progress, stats, and errors** for admin observability (admin panel), without involving frontend changes.

---

### Scope

**In scope**

- Implement Euphrosyne backend endpoint: `GET /data/operations/{operation_id}`
- Return operation status + progress + stats + error info
- Enforce access control

**Out of scope**

- UI integration / frontend
- Polling logic in UI
- tools-api proxy endpoints (this is Euphrosyne DB read, unless already designed otherwise)

---

### Description

Add a new read endpoint that retrieves a lifecycle operation by `operation_id` and returns a normalized payload with:

**Required fields**

- `operation_id`
- `project_id` (or `project_slug` if that’s the canonical public identifier)
- `type` (`COOL` / `RESTORE`)
- `status` (`PENDING` / `RUNNING` / `SUCCEEDED` / `FAILED`)
- `created_at`, `started_at`, `finished_at` (whatever timestamps exist in the model)

**Stats / progress**

- `bytes_total`, `files_total`
- `bytes_copied`, `files_copied`
- `progress` (0..1 or 0..100) computed server-side when totals are present:
  - if `bytes_total > 0`: `bytes_copied / bytes_total`
  - else if `files_total > 0`: `files_copied / files_total`
  - else: `null`

**Errors**

- `error` object (or equivalent existing structure), including:
  - `title` / `message` (stored raw if available)
  - optional `details` / `code`

**Access control**

- Only **lab admins** can access this endpoint (consistent with “admin visibility” scope).
- Return `404` if not found (and do not leak existence to unauthorized users).

**Edge cases**

- If some fields are not known yet (e.g. totals), return `null` rather than faking `0`.
- If the operation exists but timestamps are partially filled (e.g. started not set), return what you have.

---

### Acceptance criteria

- `GET /data/operations/{operation_id}` exists and returns `200` with:
  - `status` + computed `progress`
  - `bytes/files` totals and copied
  - timestamps
  - error info when `FAILED`

- Access control is enforced (non-admins get `403` or `404` per project conventions).
- Tests cover:
  - happy path (existing operation)
  - not found
  - access control
  - progress computation (bytes-based, files-based, and `null` when no totals)
