## Context
PRD: Hot → Cool Project Data Management (Immutable Cool)

This epic implements the **project-level** data lifecycle described in the PRD.
The lifecycle applies to the **entire project data folder**, including runs,
documents, and any other project-scoped files.

---

## Goal
Implement **project-level** lifecycle state machine, automation, immutability
enforcement, and UI visibility.

The lifecycle controls when a project’s data is stored in:
- Azure Files (HOT workspace), or
- Azure Blob Storage (COOL, immutable).

---

## Success criteria

- Projects automatically become eligible for cooling based on activity:
  - Initial eligibility: `project.created + 6 months`
  - Updated eligibility each time a new run is planned:
    `run.end_date + 6 months`
- Entire project data (runs + documents) is cooled as a single unit.
- Restore works on demand and returns the project to HOT.
- Writes are blocked when the project is in `COOL` or `COOLING`:
  - document uploads/edits/deletes
  - run outputs
  - any write under the project folder
- **New runs cannot be created** when the project is `COOL` or `COOLING`.
- Admins can see:
  - lifecycle state
  - cooling eligibility date
  - last lifecycle operation and error (if any).

---

## Non-goals (explicit for this epic)

- No cold/archive tier
- No partial (per-run) cooling
- No deletion of hot data after cooling
- No detection of concurrent readers (existing VM mounts tolerated)

---

## Notes

- Lifecycle state is tracked **at the project level**, not run level.
- Euphrosyne is the source of truth for lifecycle state and eligibility.
- Physical data movement is handled by euphrosyne-tools-api and is out of scope
  for this epic.
