# [TASK] UI — Show lifecycle badge + restore/retry actions (admin-only)

## Context

Project data lifecycle is tracked at the **project level**:

`HOT → COOLING → COOL → RESTORING → ERROR`

Lifecycle operations (`COOL` / `RESTORE`) are long-running and verified.

We must expose lifecycle visibility and actions in the **Workplace view**, using **DSFR components**, implemented in **React (.tsx)**.

---

## Goal

In Workplace:

- Display lifecycle badge
- Allow **admin-only restore**
- Allow **admin-only retry on error**
- Display last operation metadata
- Poll operation endpoint while running
- Disable writes when project ≠ HOT

This UI is visible **only to lab admins**.

---

## Scope

### In scope

- Lifecycle badge (admin-only)
- Restore button (COOL only, admin-only)
- Error banner + retry (ERROR only, admin-only)
- Operation metadata card (last operation only)
- Polling during COOLING / RESTORING
- Disable mutation UI when state ≠ HOT
- Implementation in `.tsx`
- Use DSFR components only

### Out of scope

- Operation history list
- Eligibility date display
- Non-admin lifecycle UI

---

## Functional Requirements

### 1️⃣ Lifecycle badge (Workplace)

Display DSFR badge based on `project.lifecycle_state`:

| State     | Badge severity |
| --------- | -------------- |
| HOT       | success        |
| COOLING   | info           |
| COOL      | default        |
| RESTORING | info           |
| ERROR     | error          |

Requirements:

- Must reflect backend state only
- No optimistic state changes
- Updates after polling

---

### 2️⃣ Restore (admin-only)

When:

```

lifecycle_state == COOL

```

Show button:

> “Restore project”

Call:

```

POST /data/projects/{project_slug}/restore

```

After click:

- Disable button
- Wait for backend to transition to `RESTORING`
- Start polling operation endpoint

Only lab admins can see/use this.

---

### 3️⃣ Error banner + retry (admin-only)

When:

```

lifecycle_state == ERROR

```

Display DSFR error alert with:

- Last operation type
- Raw tools-api error **title message**
- Timestamp
- Files/bytes copied vs expected (if available)

Retry button:

- If last op = COOL → `POST /data/projects/{project_slug}/cool`
- If last op = RESTORE → `POST /data/projects/{project_slug}/restore`

Retry must create new `operation_id` (backend responsibility).

---

### 4️⃣ Operation metadata

When state ∈ `{COOLING, RESTORING, COOL, ERROR}`:

Display “Lifecycle details” card showing:

- Operation type
- Status
- Started at
- Finished at
- Files total / copied
- Bytes total / copied

Data from:

```

GET /data/operations/{operation_id}

```

(No history list — last operation only.)

---

### 5️⃣ Polling

When state ∈ `{COOLING, RESTORING}`:

Poll:

```

GET /data/operations/{operation_id}

```

- Interval: ~5 seconds
- Stop when status ∈ `{SUCCEEDED, FAILED}`
- Refetch project lifecycle state
- Update badge accordingly

No WebSocket required.

---

### 6️⃣ Immutability UI

When state ≠ HOT:

Disable:

- Upload
- Delete
- Rename
- Run creation

Add DSFR notice:

> “Project is currently in Cool storage. Restore to modify.”

Backend remains authoritative for write enforcement.

---

## API Dependencies

- `POST /data/projects/{project_slug}/restore`
- `POST /data/projects/{project_slug}/cool` (retry)
- `GET /data/operations/{operation_id}`

---

## Acceptance Criteria

- Lifecycle badge visible in Workplace (admin-only).
- Restore visible only when COOL.
- Retry visible only when ERROR.
- Raw tools-api error title displayed.
- Operation metadata displayed correctly.
- Polling active during COOLING/RESTORING.
- Polling stops on terminal state.
- Badge updates after operation completion.
- All mutation UI disabled when state ≠ HOT.
- Implemented in `.tsx` with DSFR components.
- No operation history implemented.
