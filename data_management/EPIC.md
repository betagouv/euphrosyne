## Context
PRD: Hot → Cool Data Management (Immutable Cool)

## Goal
Implement run-level lifecycle state machine, automation, immutability enforcement, and UI visibility.

## Success criteria
- Runs auto-cool after eligibility (run_end_date + 6 months, fallback run.created)
- Restore works on demand
- Writes blocked in COOL/COOLING
- Admin visibility of ops and errors