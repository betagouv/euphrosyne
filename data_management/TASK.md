## [TASK] Update cooling eligibility computation to support embargo date

### Context

Project cooling eligibility is currently derived from lifecycle rules tied to project creation and planned runs.

We need to revise this logic to support an explicit `embargo_date` while keeping automatic cooling scheduling based on a single computed field (`cooling_eligible_at`).

---

## Description

Update the computation rules for `cooling_eligible_at` so that embargo dates take precedence over run-based eligibility.

### Eligibility rules

1. **Default value**

When a project is created:

```
cooling_eligible_at = project.created + 24 months
```

2. **Embargo-based eligibility**

When `embargo_date` is set or modified:

```
cooling_eligible_at = embargo_date
```

Embargo date always takes priority over run-based eligibility.

3. **Run-based eligibility**

When a run is planned:

```
cooling_eligible_at = run.end_date + 24 months
```

but **only if the project has no embargo_date**.

If `embargo_date` exists, planning runs must **not override** embargo-based eligibility.

---

## Scheduler behavior

The automatic cooling scheduler must continue to rely **only on `cooling_eligible_at`** when selecting projects eligible for cooling.

No embargo-specific logic should be added to the scheduler itself.

---

## Acceptance criteria

- New projects get `cooling_eligible_at = project.created + 24 months`.
- Setting `embargo_date` sets `cooling_eligible_at = embargo_date`.
- Updating `embargo_date` recomputes `cooling_eligible_at`.
- Planning a run recomputes `cooling_eligible_at = run.end_date + 24 months` **only when no embargo_date exists**.
- Planning runs does not override embargo-based eligibility.
- The scheduler continues to select projects based solely on `cooling_eligible_at`.
- Tests cover:
  - project creation
  - setting embargo date
  - updating embargo date
  - planning a run without embargo
  - planning a run with embargo present

---

## Small implementation advice (important)

When implementing, **centralize the computation** in a single function/service like:

```
compute_cooling_eligible_at(project)
```

and call it from:

- project creation
- embargo_date update
- run planning

This avoids spreading lifecycle logic across multiple places — which will otherwise become fragile very quickly.

---

If you want, I can also show you a **very common edge case in lifecycle systems** that your current rule might trigger (it’s subtle but happens a lot with embargo + runs).
