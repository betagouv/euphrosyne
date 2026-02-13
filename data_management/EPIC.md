# [EPIC] Project data mover (Files ↔ Blob Cool) with AzCopy

## Context

This EPIC is part of the **Hot → Cool Project Data Management (Immutable Cool)** initiative.

After delivering the **lifecycle state machine, immutability rules, eligibility logic, and admin visibility** (EPIC 1), the system now needs a **reliable, auditable, and verifiable mechanism** to physically move project data between storage tiers.

Project data transitions must be:

* **explicitly triggered**
* **long-running**
* **idempotent**
* **verifiable**
* **fully observable**

Actual data movement is delegated to **euphrosyne-tools-api**, using **AzCopy** for storage-native, high-throughput transfers.

---

## Goal

Implement **project-level COOL and RESTORE operations** that:

* move **entire project data** between:

  * Azure Files (HOT)
  * Azure Blob Storage (Cool tier)
* are executed via **AzCopy**
* are tracked as **long-running lifecycle operations**
* are verified using **AzCopy transfer summaries**
* drive project lifecycle state transitions in Euphrosyne

This EPIC is the first one that **moves bytes**, not just states.

---

## Scope

### In scope

* Project-level data copy:

  * Files → Blob Cool (COOL)
  * Blob Cool → Files (RESTORE)
* Long-running operation tracking
* Operation polling and status reconciliation
* Verification based on:

  * expected file count
  * expected byte size
* Automatic triggering for eligible projects
* Manual triggering for restore
* Full auditability

### Out of scope (explicit)

* Deletion of HOT data after cooling
* Cold / Archive tier
* Partial project tiering
* Delta sync or incremental copy
* Deduplication
* Concurrent HOT + COOL writes

---

## High-level design

### Source of truth

* **Euphrosyne DB** is the authoritative source for:

  * lifecycle state
  * storage class
  * eligibility
  * expected bytes / files
* **tools-api** is the executor and reporter of physical copy operations

State transitions **never happen based on AzCopy alone** —
they only occur after **verified success** is reported back.

---

### Lifecycle operations

Each COOL or RESTORE is modeled as a **single lifecycle operation** with:

* a unique `operation_id`
* a fixed direction (`COOL` or `RESTORE`)
* immutable expectations (bytes/files)
* monotonic status progression:

  ```
  PENDING → RUNNING → SUCCEEDED | FAILED
  ```

Operations are:

* idempotent per `(project_id, operation_id)`
* never reused across retries
* fully auditable

---

### Storage movement model

**COOL**

```
Azure Files (project folder)
        ↓
Azure Blob Storage (Cool tier, project prefix)
```

**RESTORE**

```
Azure Blob Storage (Cool tier)
        ↓
Azure Files (project folder)
```

Characteristics:

* Entire project moves as a single unit
* Directory structure is preserved
* COOL storage is treated as **immutable**
* HOT storage is treated as **ephemeral workspace**

---

## AzCopy integration model

### Role of AzCopy

AzCopy is used as the **only mechanism** for data transfer:

* high throughput
* resumable
* storage-native verification

tools-api is responsible for:

* starting AzCopy jobs
* polling job progress
* parsing AzCopy summaries
* translating AzCopy outcomes into lifecycle operation status

---

### Verification contract

A lifecycle operation is considered **successful** if and only if:

* AzCopy job completes successfully
* `files_copied == expected_files`
* `bytes_copied == expected_bytes`

Any mismatch or execution error results in **FAILED**.

There is no partial success.

---

## Execution flow (nominal)

### COOL (automatic)

1. Project becomes eligible for cooling
2. Euphrosyne starts a COOL operation
3. Project enters `COOLING`
4. tools-api launches AzCopy (Files → Blob Cool)
5. AzCopy completes
6. tools-api reports verified success + stats
7. Euphrosyne marks project `COOL`

---

### RESTORE (manual)

1. User or admin triggers restore
2. Project enters `RESTORING`
3. tools-api launches AzCopy (Blob Cool → Files)
4. AzCopy completes
5. tools-api reports verified success + stats
6. Euphrosyne marks project `HOT`

---

## Failure model

* Any failure during copy or verification:

  * lifecycle operation → `FAILED`
  * project lifecycle → `ERROR`
* Errors are:

  * persisted
  * visible to admins
  * retryable via a new operation

Project state never flips on partial or unverified success.

---

## Observability & auditability

For each operation, the system records:

* type (COOL / RESTORE)
* timestamps (start / finish)
* status
* expected vs actual bytes/files
* error details (if any)

Admins can:

* inspect operation history
* understand failures
* retry safely

---

## Success criteria

This EPIC is considered complete when:

* COOL and RESTORE operations move full project data via AzCopy
* Operations are fully tracked and observable
* Verification gates lifecycle state transitions
* Automatic cooling works end-to-end
* Restore reliably returns projects to HOT
