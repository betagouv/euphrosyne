## [TASK] Implement automatic cooling scheduler (daily)

### Context

PRD – Cooling eligibility and workflow (project-level, immutable COOL).
Cooling is executed by `euphrosyne-tools-api` via a long-running operation; Euphrosyne is the source of truth for lifecycle state.

---

### Description

Implement a **daily scheduler job** that:

1. **Is gated by a feature flag**

   * Environment variable: `PROJECT_COOLING_ENABLED`
   * Defaults to **false** (disabled unless explicitly enabled)
   * If disabled: job exits without doing anything (logs “disabled”)

2. **Selects eligible projects (project-level)**

   * Only projects with:

     * `lifecycle_state = HOT`
     * `cooling_eligible_at <= now()`
   * Ignores all others (`COOLING`, `COOL`, `RESTORING`, `ERROR`, or non-eligible HOT)

3. **Applies a daily throughput limit**

   * Enqueue **at most 3 projects per daily run**
   * Selection order: `cooling_eligible_at ASC` (oldest eligible first)

4. **Enqueues cooling as a lifecycle operation**
   For each selected project:

   * Create `LifecycleOperation`:

     * `type = COOL`
     * `status = PENDING`
     * `operation_id = UUID`
     * `bytes_total = project_size_bytes` (expected)
     * `files_total = file_count` (expected)
     * timestamps initialized
   * Call tools-api:

     * `POST /data/projects/{project_slug}/cool`
     * include `operation_id` (idempotency key)

5. **Transitions lifecycle state only if tools-api accepts**

   * If tools-api responds **ACCEPTED** (e.g. HTTP 202):

     * Update `LifecycleOperation` → `RUNNING` (or keep `PENDING` if that’s your model, but it must be “in progress”)
     * Transition project lifecycle `HOT → COOLING`
     * Set `last_lifecycle_operation_id = operation_id`
   * If tools-api call fails (timeout/network/5xx) or returns non-accepted:

     * Update `LifecycleOperation` → `FAILED` with error details
     * Project lifecycle **stays `HOT`** (no read-only lock since cooling wasn’t accepted)

---

### Idempotency requirements

The scheduler must be safe to run multiple times:

* Projects not in `HOT` must never be enqueued
* A project must not produce multiple COOL operations due to concurrent scheduler runs
* Implementation must use an atomic/locking strategy, e.g.:

  * row locking with `SELECT … FOR UPDATE SKIP LOCKED`, and/or
  * atomic “claim” update before calling tools-api (recommended)

**Important:** the “claim” must ensure two scheduler instances do not enqueue the same project.

---

### Operational behavior

* Runs **once per day**
* Processes up to **3 projects** per execution
* Logs:

  * run start/end
  * whether flag is enabled
  * number of eligible projects found
  * number enqueued (≤3)
  * per-project: project_id/slug, operation_id, tools-api result

---

### Acceptance criteria

* ✅ Eligible `HOT` projects (eligible_at <= now) are enqueued, up to **3 per day**
* ✅ Non-eligible projects are ignored
* ✅ If `PROJECT_COOLING_ENABLED` is unset/false → scheduler does nothing
* ✅ Idempotent: repeated runs do not duplicate operations or enqueue the same project twice
* ✅ If tools-api call is not accepted → operation is `FAILED` and project remains `HOT`
