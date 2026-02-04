
# TASK: Pivot Hot → Cool lifecycle from RUN-level to PROJECT-level

## Context

The initial implementation of the Hot → Cool lifecycle was done at **run level**:

- #1683 Add project_run_data and lifecycle_operation tables
- #1684 Implement run lifecycle state machine and guards
- #1685 Compute run_size_bytes and file_count when run data is finalized

We have since validated that the correct granularity is **PROJECT-level**:

- Entire project data (runs + documents + any project-scoped files) must move together
- Lifecycle state must apply to the whole project
- New runs must not be created when project data is COOL or COOLING

The PRD and EPIC documents in `data_management/` have been updated accordingly.

This task performs a **pivot/refactor** of the existing run-level implementation to a
**project-level lifecycle**, reusing and adapting existing code where possible.

---

## Goal

Refactor the existing run-level lifecycle implementation into a **project-level lifecycle**
that matches the updated PRD and EPIC, without introducing physical data movement or
tools-api integration.

---

## Scope (what to change)

### A) Data model pivot

- Replace run-level lifecycle tracking with project-level lifecycle tracking.
- Lifecycle state MUST be attached to the project (or a `ProjectData` table keyed by `project_id`).
- `lifecycle_operation` must reference `project_id` (not `run_id`).
- Replace run-level totals:
  - `run_size_bytes` → `project_size_bytes`
  - `file_count` must represent **entire project folder**.
- Remove, rename, or repurpose `project_run_data` so naming reflects project-level lifecycle.

All database changes MUST be done via:

```bash
venv/bin/python manage.py makemigrations
````

(do not hand-write migrations).

---

### B) Eligibility logic (project-level)

Implement the following policy:

* Initial eligibility:

  ```
  project.created + 6 months
  ```
* Each time a new run is planned:

  ```
  eligibility = run.end_date + 6 months
  ```
* If `run.end_date` is null at planning time:

  * keep the existing eligibility unchanged
  * document this behavior in code comments and/or tests

Eligibility must be stored and updated at the project level.

---

### C) State machine pivot

Refactor the existing run-level lifecycle state machine to project-level:

States:

* `HOT`
* `COOLING`
* `COOL`
* `RESTORING`
* `ERROR`

Requirements:

* Guards and transitions must be project-scoped.
* Any code referring to “run lifecycle” must be updated to “project lifecycle”.
* Ensure no remaining logic assumes mixed hot/cool runs within a project.

---

### D) Immutability & behavior changes

When a project is in `COOL` or `COOLING`:

* Forbid **all writes** under project data:

  * document uploads / edits / deletes
  * run outputs
  * rename / delete operations
* **Prevent creation or planning of new runs**.

  * This must be enforced at the application/service layer, not only in the UI.

Existing behavior that only blocks run-level writes must be generalized to project-level.

---

### E) Totals computation

Refactor totals computation to project scope:

* Compute:

  * `project_size_bytes`
  * `file_count`
* Totals must include:

  * runs
  * documents
  * any files under the project folder

Reuse existing logic where possible; correctness > performance for v1.

---

### F) Naming & internal API cleanup

* Rename variables, functions, services, and UI labels from run-level to project-level where they relate to lifecycle.
* Remove misleading names such as `project_run_data` if they no longer match semantics.
* Ensure codebase terminology aligns with PRD and EPIC.

---

## Out of scope (explicit)

* tools-api integration
* AzCopy execution
* Physical data movement
* Cold/archive tiers
* Hot data deletion
* Per-project file shares
* Large refactors unrelated to lifecycle

---

## Testing requirements

Update or add tests to cover:

* Project-level lifecycle transitions and guards
* Eligibility computation:

  * default from `project.created`
  * update on run planning with `run.end_date`
* Prevention of run creation when project is `COOL` or `COOLING`
* Project-level totals computation

Existing run-level tests must be updated or removed if no longer relevant.

All tests must pass.

---

## Translations

If any user-facing strings are modified:

```bash
venv/bin/python manage.py makemessages --all --verbosity 0 --no-location --no-obsolete --ignore 'venv/*'
venv/bin/python manage.py makemessages --all --verbosity 0 --no-obsolete --no-location -d djangojs \
  --ignore 'node_modules/*' \
  --ignore 'venv/*' \
  --ignore 'euphrosyne/assets/dist/*' \
  -e js,tsx,ts,jsx
venv/bin/python manage.py compilemessages
```

* No empty translations
* No fuzzy entries

---

## Typing requirements

* Type-hint new and modified Python code as much as reasonably possible.
* Prefer concrete types (`datetime`, `UUID`, `QuerySet[Model]`, etc.).
* It is acceptable to relax typing where Django dynamics make strict typing impractical.

---

## Notes & discoveries

* Record any unexpected findings, assumptions, or deferred work in:

  * `data_management/NOTES.md`
* Do NOT modify PRD.md or EPIC.md unless explicitly instructed.

---

## Definition of done

* No remaining run-level lifecycle logic for this feature.
* Project-level lifecycle state machine is authoritative.
* Project eligibility follows the new policy.
* Run creation is blocked in `COOL` / `COOLING`.
* Totals are project-level.
* Migrations generated via `makemigrations`.
* Tests pass.
