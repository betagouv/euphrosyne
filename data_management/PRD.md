# PRD: Hot → Cool Data Management (Immutable Cool)

## Goal

Reduce storage costs and improve long-term manageability by moving run data from **Azure Files (hot workspace)** to **Azure Blob Storage (cool tier)** after a configurable delay, while keeping projects **browsable in the UI** and **restorable on demand**.

## Non-goals (v1)

* No cold/archive tier
* No partial tiering (entire project transitions as a unit)
* No deduplication
* No delta-sync; cool data is immutable

---

# User stories

## U1 — Automatic cooling after post-processing window

As an admin, I want project data to automatically move from Files to Blob Cool after **run_end_date + 6 months**, so hot storage remains small.
If run_end_date is null, compute eligibility from run.created.

## U2 — Browse cooled projects

As a user, I want to view my project files list in the UI even after cooling.

## U3 — Restore to workspace

As a user (or admin), I want to restore a cooled project back to hot workspace to re-run analysis.

## U4 — Audit and traceability

As an admin, I want to see when a project was cooled/restored, how many bytes/files moved, and whether the operation succeeded.

---

# Key decisions

* **Source of truth:** Euphrosyne DB controls lifecycle state and storage location.
* **Execution:** euphrosyne-tools-api performs copy/move operations and verification.
* **Cool is immutable:** once cooled, no writes are allowed to the cool location; updates require restore.

---

# Definitions

## Storage locations

* **Hot**: `azure_files://<account>/<share>/<project_prefix>/`
* **Cool**: `azure_blob://<account>/<container>/<project_prefix>/` with **blob access tier = Cool**

## Storage path resolution

euphrosyne-tools-api is responsible for resolving source and destination storage paths.

Given a `(project_slug, run_slug)`, tools-api deterministically computes:
- the Azure Files source path for HOT runs
- the Azure Blob destination prefix for COOL runs

The mapping is based on fixed conventions and environment configuration
(storage accounts, file shares, blob containers) and must remain stable
over time to allow reliable restores of cooled runs.

Euphrosyne does not pass explicit storage URIs to tools-api; it passes
identifiers (`project_slug`, `run_slug`, `operation_id`).

## Concurrency considerations

In v1, cooling may proceed even if existing VMs or processes still have the
run data mounted.

Writes are blocked at the application level during `COOLING`, but the system
does not actively detect or prevent concurrent readers or existing mounts.

The data is assumed to be stable at the time cooling begins.



## Run data lifecycle states (v1)

* `HOT` — project data lives in Files
* `COOLING` — migration in progress (read-only / restricted writes)
* `COOL` — project data lives in Blob Cool (immutable)
* `RESTORING` — moving back to hot
* `ERROR` — last lifecycle operation failed; manual retry possible

## Timers

* Cooling eligibility date = `run_end_date + 6 months` (configurable)

---

# Functional requirements


## FR1 — Cooling workflow

When a run becomes eligible:

1. Euphrosyne marks project run `COOLING`
2. tools-api copies data from Files → Blob prefix
3. tools-api verifies the operation using AzCopy job results:
   * the AzCopy job must complete successfully
   * number of files transferred must match expected `file_count`
   * total bytes transferred must match expected `run_size_bytes`
4. tools-api reports success with stats
5. Euphrosyne marks project run `COOL` and updates storage address
6. Optionally delete hot data after success (v1: **config flag**, keep disabled initially)

## FR2 — Restore workflow

User/admin triggers restore:

1. run enters `RESTORING`
2. tools-api copies from Blob → Files workspace prefix
3. verifies count + size
4. Euphrosyne marks run `HOT`

## FR3 — Immutability rules

* In `COOL` state, application forbids:
  * upload / delete / rename operations
  * pipeline writes to run data paths

* In `COOLING`, writes are blocked:
  * **Hard lock **: set project workspace as read-only in app logic; reject writes

Euphrosyne tools API should deny write operations for COOL / COOLING (specific class for Readonly Cool Storage Client with only read methods). We will not issue write SAS for COOL Blob client.

After COOL succeeds, HOT copy is treated as read-only and may be deleted later.

Euphrosyne flips HOT→COOL only after tools-api reports SUCCEEDED and verification passed.


## FR4 — Admin visibility

Admin UI shows:

* state
* eligibility date
* last lifecycle operation + timestamps
* bytes/files moved
* error details and retry button

## FR5 — Idempotency & retries

* Each lifecycle operation (COOL or RESTORE) is identified by a unique `operation_id`.
* tools-api endpoints must be idempotent for the same `(run_id, operation_id)`:
  * repeated calls with the same identifiers must not start duplicate copy jobs
  * they must return the current status of the existing operation
* If an operation fails, the run enters `ERROR` state.
* Retries are performed by creating a **new operation with a new `operation_id`**.
* A run in `ERROR` state may be retried only with a new `operation_id`.
* A run must never transition to `COOL` or `HOT` unless the corresponding operation completes successfully and verification passes.


---

# Non-functional requirements

* **Observability**: structured logs + per-operation status
* **Security**: storage credentials only in server-side identities; no user SAS tokens
* **Performance**: moves should saturate available bandwidth without starving production
* **Cost awareness**: store post-run data to cool storage

---

# Data model changes (Euphrosyne DB)

## Project run data table (new)

* `storage_class` enum: `AZURE_FILES`, `AZURE_BLOB`
* `lifecycle_state` enum (above)
* `cooling_eligible_at` datetime
* `last_lifecycle_operation_id` nullable
* `last_lifecycle_error` text nullable
* `run_size_bytes`, `file_count`

`run_size_bytes` and `file_count` are computed once the run data is finalized
and are used as the expected totals for verification during COOL and RESTORE.


## Lifecycle operation table (new)

* `operation_id` (uuid)
* `run_id`
* `type` enum: `COOL`, `RESTORE`
* `status` enum: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`
* `started_at`, `finished_at`
* `bytes_total`, `files_total`
* `bytes_copied`, `files_copied`
* `error_message`, `error_details`


---

# API specs

## Euphrosyne → tools-api

### POST `data/<same-as-project-run-data-access>/cool`

Request:
* Request body is empty; tools-api resolves storage paths from identifiers.

 Response:
* accepted + polling URL or status + `operation_id`

### POST `data/<same-as-project-run-data-access>/restore`

Same shape, reverse direction.

### GET `data/operations/{operation_id}`

Returns status + progress.

## Euphrosyne internal endpoints (UI/admin)

* `POST /projects/{id}/run/{id}/restore`
* `POST /projects/{id}/run/{id}/retry-cooling`
* `GET /projects/{id}/run/{id}/lifecycle`

---

# UX requirements

## User UI

* Workplace page shows lifecycle badge in run data tab: Hot / Cooling / Cool / Restoring / Error
* If Cool: show “Restore to workspace” button (permissions-based)
* File browser works regardless of state

## Admin UI

* List projects by state
* Filter “eligible for cooling”
* Show last error and retry

---

# Rollout plan

1. Ship cooling without deletion of hot data (safe mode)
2. Ship restore
3. Enable optional hot deletion after X days (later)

---

# Implementation tasks (epics → stories)

## Epic A — Storage abstraction & lifecycle state machine (Euphrosyne)

1. Implement project run data table
2. Implement state transitions + guards:
   * only COOL if HOT and eligible
   * only RESTORE if COOL
   * COOLING_DELAY = 6 months (default), configurable per env.
3. Add background cron to enqueue cooling jobs daily (create Django command and add it to run_checks command).
4. Add admin section in workplace in run tab & add filters in project list view (eligible, has_error, per state)
5. Enforce immutability in app layer:
   * block uploads/writes when COOL/COOLING
   * show clear error message & guidance 

**Deliverable:** Projects can be marked eligible and transitions are tracked.

## Epic B — tools-api mover (Files → Blob Cool)

1. Implement endpoint `POST.../cool`
2. Implement AzCopy invocation:
   * Files share path → Blob prefix
   * ensure blobs land with correct tier (Cool) (set at upload or post-set tier)
3. Track job progress + logs
4. Verification (count + bytes; optional sampling)
5. Return operation status via `GET data/operations/{operation_id}`
6. Idempotency: safe re-run for same operation_id

**Deliverable:** Given a project run folder, tools-api can copy to blob and verify.

## Epic C — tools-api restorer (Blob → Files)

1. Implement endpoint `POST .../restore`
2. AzCopy Blob → Files
3. Verification
4. Progress reporting and idempotency

**Deliverable:** Cool projects can be restored reliably.

## Epic D — Integration & reconciliation

1. Euphrosyne calls tools-api and updates lifecycle operation table
2. Implement reconciliation job and error display
3. Add alerts/metrics dashboard hooks

If COOLING fails → state becomes ERROR, run stays HOT, retry allowed. Will retry in next run.

If RESTORE fails → state becomes ERROR, run remains COOL, retry allowed.

A run in ERROR can be retried idempotently with new operation_id (define which)

**Deliverable:** Robustness against partial moves/drift.

## Epic E — Security & access control

1. Managed identity / service principal permissions:

   * tools-api: read Files, write Blob, read Blob, write Files
2. Ensure users never get direct storage credentials
3. Audit log for lifecycle operations

**Deliverable:** Secure movement with traceability.

## Epic F — Testing

1. Unit tests for state machine guards
2. Integration tests for tools-api mover/restorer (using test storage or Azurite where feasible)
3. End-to-end test scenario:

   * create project → index → cool → browse → restore → browse

**Deliverable:** Confidence and regression safety.

---

# Acceptance criteria (v1)

* A run automatically transitions to COOLING then COOL after eligibility date.
* File list remains visible in UI after cooling.
* Restore returns project to HOT and data is accessible again.
* Cool state enforces immutability (no writes).
* Admin can see operations, progress, errors, and retry.

