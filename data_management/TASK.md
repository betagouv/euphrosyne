## [TASK] Django admin: lifecycle filters, operations list, retry/restore actions

### Context

PRD – FR4 Admin visibility.

Admins must be able to inspect project lifecycle status, cooling eligibility, lifecycle operation outcomes, and errors, and trigger corrective actions when needed.

Lifecycle state is tracked at the **project level**, and lifecycle operations are stored as auditable records.

This must be implemented in the **Django admin**, following the design and interaction patterns already used by existing admin views, and accessible only to **`lab_admin`** users.

## Description

Extend existing Django admin views to expose project lifecycle visibility and actions.

Implementation must reuse the structure and conventions of existing admin views/screens rather than introducing a separate custom interface.

### Access control

- views and actions accessible only to users with **`lab_admin`** permissions

### Filters

Add admin filters on **projects**:

- `lifecycle_state`
- **eligible for cooling** (`cooling_eligible_at <= now`)

### Lifecycle information

Display in the project admin view:

- `lifecycle_state`
- `cooling_eligible_at`
- last lifecycle operation
- operation timestamps
- bytes/files moved
- last lifecycle error / error details

### Lifecycle operations

- show the **list of lifecycle operations** for a project using the same presentation approach as other related admin views

### Admin actions

Provide actions/buttons, consistent with existing admin patterns, for:

- **retry** failed lifecycle operation
- **restore** cooled project

Retry behavior:

- retry must create a **new `operation_id`**
- failed operation ids are never reused

Permissions:

- retry and restore actions are **`lab_admin` only**

## Acceptance criteria

- Only **`lab_admin`** users can access lifecycle admin views and actions.
- Lifecycle views are implemented **consistently with existing admin view design/patterns**.
- Admin can filter projects by `lifecycle_state`.
- Admin can filter projects **eligible for cooling**.
- Admin can view lifecycle state, eligibility date, last operation details, bytes/files moved, and error details.
- Admin can identify projects in `ERROR` or transitional states (`COOLING`, `RESTORING`).
- Admin can trigger **retry**, creating a new `operation_id`.
- Admin can trigger **restore** when permitted.
- Admin can view the **list of lifecycle operations** for a project.
- Non-`lab_admin` users do not see lifecycle actions.
