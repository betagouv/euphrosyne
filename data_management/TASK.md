## Context

PRD – API specs + FR1/FR2/FR5

- tools-api COOL / RESTORE endpoints are already implemented and integrated.
- `lifecycle_operation` creation and scheduler logic are already implemented.
- tools-api sends a **terminal callback** (SUCCEEDED / FAILED) once the async AzCopy job completes.
- We must update:
  - `lifecycle_operation` status
  - project lifecycle state
- Lifecycle transitions must occur **only if success + verification** (bytes/files match expected totals).

Out of scope:

- COOL / RESTORE starter logic
- Idempotency mechanisms
- tools-api enqueue endpoint implementation

---

## Description

Implement the backend callback endpoint:

`POST /api/data-management/operations/callback`

### Authentication

- Protect as backend-to-backend endpoint (shared token / existing backend auth mechanism).
- Return `401/403` if unauthorized.

### Payload (minimum expected fields)

- `operation_id` (UUID, required)
- `status`: `SUCCEEDED` | `FAILED` (required)
- `bytes_copied` (optional)
- `files_copied` (optional)
- `error` (optional, present on FAILED)

### Processing logic

1. Retrieve `lifecycle_operation` by `operation_id`.
   - If not found → return 404 (or consistent error handling decision).
   - If already terminal (`SUCCEEDED` / `FAILED`) → return 200 (idempotent handling).

2. If `status == FAILED`:
   - Set:
     - `lifecycle_operation.status = FAILED`
     - persist `error` details

   - Transition project lifecycle → `ERROR`
   - Return 200.

3. If `status == SUCCEEDED`:
   - Store received stats:
     - `bytes_copied`
     - `files_copied`

   - Compute verification:
     - `bytes_copied == bytes_total`
     - `files_copied == files_total`

   - If verification passes:
     - Set `lifecycle_operation.status = SUCCEEDED`
     - Transition project lifecycle:
       - `COOL` if operation type is COOL
       - `HOT` if operation type is RESTORE

   - If verification fails:
     - Treat as failure:
       - `lifecycle_operation.status = FAILED`
       - store structured verification error

     - Transition project lifecycle → `ERROR`

   - Return 200.

### Concurrency considerations

- Ensure safe handling of duplicate or concurrent callbacks.
- Avoid double lifecycle transitions.
- Use transaction and row-level locking if necessary.

---

## Acceptance criteria

- Callback endpoint is authenticated and rejects unauthorized requests.
- `operation_id` is used to locate and update the correct `lifecycle_operation`.
- On `FAILED`:
  - lifecycle_operation → FAILED
  - project lifecycle → ERROR

- On `SUCCEEDED` + verified:
  - lifecycle_operation → SUCCEEDED
  - project lifecycle → COOL (COOL op) or HOT (RESTORE op)

- On `SUCCEEDED` + verification mismatch:
  - lifecycle_operation → FAILED
  - project lifecycle → ERROR

- Duplicate callbacks do not cause inconsistent state transitions.
- Lifecycle state transitions occur **only** after successful verification.
