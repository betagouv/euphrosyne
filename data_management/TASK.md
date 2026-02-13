# [TASK] Enforce immutability for COOL and COOLING runs in app layer

Based on PRD – Project immutability rules.

---

# Functional Goal

When a project has:

```
lifecycle_state ∈ {COOL, COOLING}
```

the application must behave as **strictly read-only** at the project level.

This means:

- ❌ Block document uploads
- ❌ Block document edits
- ❌ Block document deletes
- ❌ Block run creation
- ❌ Block run planning/scheduling
- ❌ Block run outputs / artifact writes
- ❌ Block rename operations
- ❌ Block delete operations

Reads remain allowed.

The PRD explicitly states that COOL is immutable and restore is required before modification.

---

# Architectural Strategy

## 1. Centralize the rule

Create a single authoritative check, e.g.:

- `project.is_immutable?`
- or `ensure_project_writable!(project)`
- or a reusable policy / guard

Definition:

```
immutable if lifecycle_state in {COOL, COOLING}
```

The rule must exist in **one place only**, reused everywhere.

Goal: prevent drift or forgotten endpoints.

---

## 2. Apply the guard to ALL write entry points

The rule must be enforced at application layer entrypoints (controllers, services, commands).

You must audit the repo and apply it consistently.

---

# Areas That Must Be Blocked

## A. Documents

Block:

- Upload
- Metadata edits
- Content edits
- Delete

Expected behavior:

- Return 403 Forbidden or 409 Conflict
- Clear error message
- No side effects

---

## B. Runs (creation & planning)

PRD explicitly states:

> A project in COOL or COOLING must not allow new runs to be planned.

Therefore block:

- Run creation
- Run scheduling / planning endpoints

---

## C. Run outputs / artifacts

Any operation that writes files as run outputs must be blocked.

Important edge case:

Even if a run was created before COOLING, once lifecycle_state changes to COOLING:

- Output writes must fail
- No new artifacts should be persisted

This prevents corruption during migration.

---

## D. Rename / delete operations

Block any mutation of project storage:

- Rename files/folders
- Delete files/folders
- Any filesystem-level mutation

---

# HTTP Behavior

## Recommended Status Codes

Choose one consistently:

- **409 Conflict** → state makes operation invalid
- **403 Forbidden** → business rule prohibits it

Either is acceptable if consistent.

---

## Error Response (clear & actionable)

Example:

```json
{
  "error": "PROJECT_IMMUTABLE",
  "message": "Project is read-only while lifecycle_state is COOL or COOLING. Restore the project to HOT to modify files or create runs.",
  "lifecycle_state": "COOL"
}
```

Must clearly explain:

- Why it failed
- What to do (restore)

PRD explicitly requires restore before modification.

---

# Required Test Coverage

Acceptance criteria require tests for blocked operations.

## 1. Documents

- COOLING → upload → rejected
- COOL → edit → rejected
- COOL → delete → rejected

## 2. Runs

- COOLING → create run → rejected
- COOL → plan run → rejected

## 3. Outputs

- COOLING → attempt artifact write → rejected
- COOL → attempt artifact write → rejected

## 4. Rename/Delete

- COOL/COOLING → rename → rejected
- COOL/COOLING → delete → rejected

## 5. Control tests

- HOT → all operations still succeed

---

# Important Behavioral Distinction

### COOLING

- Transitional state (migration in progress)
- Must block writes to avoid divergence between source and destination

### COOL

- Terminal immutable state
- No writes allowed
- Restore required before modification

---

# Definition of Done

- All project-level write operations blocked when lifecycle_state ∈ {COOL, COOLING}
- Run creation/planning explicitly prevented
- Clear and consistent error responses
- Full test coverage of blocked paths
- No regression for HOT projects
