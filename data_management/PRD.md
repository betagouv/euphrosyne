## PRD: Hot → Cool Project Data Management (Immutable Cool)

## Goal

Reduce storage costs and improve long-term manageability by moving **all project data**
from **Azure Files (hot workspace)** to **Azure Blob Storage (cool tier)** after a configurable delay,
while keeping projects **browsable in the UI** and **restorable on demand**.

Project data includes:

* run data
* documents
* any other files under the project folder

---

## Non-goals (v1)

* No cold/archive tier
* No partial tiering (entire project transitions as a unit)
* No deduplication
* No delta-sync; cool data is immutable
* No concurrent mixed hot/cool projects

---

## User stories

### U1 — Automatic cooling after inactivity window

As an admin, I want project data to automatically move from Files to Blob Cool after a post-activity window, so hot storage remains small.

Eligibility rules:

* Initial eligibility is computed from `project.created + 6 months`
* Each time a new run is planned:

  * the project eligibility date is recomputed as `run.end_date + 6 months`

### U2 — Browse cooled projects

As a user, I want to view my project files list (including documents) in the UI even after the project is cooled.

### U3 — Restore project to workspace

As a user (or admin), I want to restore a cooled project back to the hot workspace to add documents or run new analyses.

### U4 — Audit and traceability

As an admin, I want to see when a project was cooled/restored, how many bytes/files were moved, and whether the operation succeeded.

---

## Key decisions

* **Lifecycle granularity:** lifecycle is tracked at the **project** level.
* **Source of truth:** Euphrosyne DB controls lifecycle state and storage location.
* **Execution:** euphrosyne-tools-api performs copy/move operations and verification.
* **Cool is immutable:** once cooled, no writes are allowed; restore is required.

---

## Definitions

### Storage locations

* **Hot:**
  `azure_files://<account>/<share>/<project_prefix>/`

* **Cool:**
  `azure_blob://<account>/<container>/<project_prefix>/`
  (blob access tier = Cool)

### Storage path resolution

euphrosyne-tools-api is responsible for resolving storage paths.

Given a `project_slug`, tools-api deterministically computes:

* the Azure Files project folder (HOT)
* the Azure Blob project prefix (COOL)

Euphrosyne never passes raw storage URIs; it passes identifiers.

---

## Project data lifecycle states (v1)

* `HOT` — project data lives in Azure Files
* `COOLING` — migration in progress; project is read-only
* `COOL` — project data lives in Blob Cool (immutable)
* `RESTORING` — moving project back to hot
* `ERROR` — last lifecycle operation failed; retry possible

---

## Eligibility rules

* Default eligibility date:

  ```
  project.created + 6 months
  ```
* Each time a new run is planned:

  ```
  eligibility = run.end_date + 6 months
  ```
* A project in `COOL` or `COOLING` **must not allow new runs to be planned**.

---

## Functional requirements

### FR1 — Cooling workflow (project-level)

When a project becomes eligible:

1. Euphrosyne marks project `COOLING`
2. tools-api copies **entire project folder** from Files → Blob prefix
3. tools-api verifies using AzCopy job results:

   * job completed successfully
   * files transferred == expected `project_file_count`
   * bytes transferred == expected `project_size_bytes`
4. tools-api reports success with stats
5. Euphrosyne marks project `COOL`
6. HOT copy becomes read-only (deletion deferred to later versions)

---

### FR2 — Restore workflow

User/admin triggers restore:

1. project enters `RESTORING`
2. tools-api copies project folder from Blob → Files
3. verification (files + bytes)
4. Euphrosyne marks project `HOT`

---

### FR3 — Immutability rules

In `COOL` and `COOLING`:

* Application forbids:

  * document uploads / edits / deletes
  * run creation
  * run outputs
  * renames or deletions under project folder

Euphrosyne tools API:

* must not issue write-capable storage clients for COOL projects
* must deny write operations for COOL / COOLING explicitly

Euphrosyne flips `HOT → COOL` only after tools-api reports `SUCCEEDED`.

---

### FR4 — Admin visibility

Admin UI shows:

* lifecycle state
* eligibility date
* last lifecycle operation + timestamps
* bytes/files moved
* error details and retry action

---

### FR5 — Idempotency & retries

* Each lifecycle operation has a unique `operation_id`
* tools-api endpoints are idempotent per `(project_id, operation_id)`
* Failures put project in `ERROR`
* Retries always create a **new operation_id**
* Project state must never flip unless verification passes

---

## Data model changes (Euphrosyne DB)

### Project data lifecycle table (new)

* `project_id`
* `storage_class`: `AZURE_FILES`, `AZURE_BLOB`
* `lifecycle_state`
* `cooling_eligible_at`
* `project_size_bytes`
* `file_count`
* `last_lifecycle_operation_id`
* `last_lifecycle_error`

### Lifecycle operation table

* `operation_id`
* `project_id`
* `type`: `COOL`, `RESTORE`
* `status`: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`
* timestamps
* `bytes_total`, `files_total`
* `bytes_copied`, `files_copied`
* error details

---

## API specs (tools-api)

* `POST /data/projects/{project_slug}/cool`
* `GET /data/projects/{project_slug}/cool/{operation_id}`
* `POST /data/projects/{project_slug}/restore`
* `GET /data/projects/{project_slug}/restore/{operation_id}`

---

## Acceptance criteria (v1)

* A project transitions to COOLING then COOL after eligibility date.
* Entire project data (runs + documents) is moved together.
* Cooled projects are browse-only.
* New runs cannot be created when project is COOL or COOLING.
* Restore returns project to HOT.
* Admins can audit and retry operations.
