import { useCallback, useEffect, useMemo, useState } from "react";

import { formatBytes } from "../../../../assets/js/utils";
import toolsFetch from "../../../../../shared/js/euphrosyne-tools-client";
import {
  LifecycleOperationType,
  LifecycleState,
  isLifecycleState,
} from "../lifecycle-state";

type LifecycleOperationStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";

interface ProjectLifecyclePanelProps {
  projectSlug: string;
  lifecycleState: LifecycleState;
  lastLifecycleOperationId: string | null;
  lastLifecycleOperationType: LifecycleOperationType | null;
  onLifecycleStateChange: (state: LifecycleState) => void;
  fetchFn?: typeof toolsFetch;
}

interface LifecycleSnapshot {
  lifecycleState: LifecycleState;
  lastOperationId: string | null;
  lastOperationType: LifecycleOperationType | null;
}

interface LifecycleOperationDetails {
  operationId: string;
  type: LifecycleOperationType | null;
  status: LifecycleOperationStatus | null;
  startedAt: string | null;
  finishedAt: string | null;
  bytesTotal: number | null;
  filesTotal: number | null;
  bytesCopied: number | null;
  filesCopied: number | null;
  errorMessage: string | null;
  errorTitle: string | null;
}

const POLLING_INTERVAL_MS = 5000;
const TRANSITION_WAIT_MS = 60000;
const TRANSITION_WAIT_INTERVAL_MS = 2000;
const TERMINAL_OPERATION_STATUSES = new Set<LifecycleOperationStatus>([
  "SUCCEEDED",
  "FAILED",
]);

const BADGE_CLASS_BY_STATE: Record<LifecycleState, string> = {
  HOT: "fr-badge fr-badge--success fr-badge--no-icon",
  COOLING: "fr-badge fr-badge--info fr-badge--no-icon",
  COOL: "fr-badge fr-badge--no-icon",
  RESTORING: "fr-badge fr-badge--info fr-badge--no-icon",
  ERROR: "fr-badge fr-badge--error fr-badge--no-icon",
};

function asRecord(value: unknown): Record<string, unknown> | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function getRecordValue(
  record: Record<string, unknown>,
  keys: string[],
): unknown | null {
  for (const key of keys) {
    if (key in record) {
      return record[key];
    }
  }
  return null;
}

function getString(
  record: Record<string, unknown>,
  keys: string[],
): string | null {
  const value = getRecordValue(record, keys);
  if (typeof value !== "string") {
    return null;
  }
  return value;
}

function getNumber(
  record: Record<string, unknown>,
  keys: string[],
): number | null {
  const value = getRecordValue(record, keys);
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return null;
}

function isOperationType(
  value: string | null,
): value is LifecycleOperationType {
  return value === "COOL" || value === "RESTORE";
}

function isOperationStatus(
  value: string | null,
): value is LifecycleOperationStatus {
  return (
    value === "PENDING" ||
    value === "RUNNING" ||
    value === "SUCCEEDED" ||
    value === "FAILED"
  );
}

function parseErrorTitle(
  rawErrorDetails: unknown,
  fallbackMessage: string | null,
): string | null {
  const detailsRecord = asRecord(rawErrorDetails);
  if (detailsRecord) {
    const title = getString(detailsRecord, ["title"]);
    if (title) {
      return title;
    }

    const message = getRecordValue(detailsRecord, ["message"]);
    if (typeof message === "string") {
      return message;
    }
    const messageRecord = asRecord(message);
    if (messageRecord) {
      const messageTitle = getString(messageRecord, ["title"]);
      if (messageTitle) {
        return messageTitle;
      }
    }
  }

  if (typeof rawErrorDetails === "string" && rawErrorDetails.trim() !== "") {
    try {
      const parsed = JSON.parse(rawErrorDetails) as unknown;
      const parsedTitle = parseErrorTitle(parsed, fallbackMessage);
      if (parsedTitle) {
        return parsedTitle;
      }
    } catch {
      return rawErrorDetails;
    }
  }

  return fallbackMessage;
}

function normalizeLifecycleSnapshot(
  payload: unknown,
): LifecycleSnapshot | null {
  const data = asRecord(payload);
  if (!data) {
    return null;
  }

  const lifecycleStateValue = getString(data, [
    "lifecycle_state",
    "lifecycleState",
  ]);
  if (!isLifecycleState(lifecycleStateValue)) {
    return null;
  }

  const lastOperationTypeValue = getString(data, [
    "last_operation_type",
    "lastOperationType",
  ]);

  return {
    lifecycleState: lifecycleStateValue,
    lastOperationId: getString(data, ["last_operation_id", "lastOperationId"]),
    lastOperationType: isOperationType(lastOperationTypeValue)
      ? lastOperationTypeValue
      : null,
  };
}

function normalizeOperation(
  payload: unknown,
  fallbackOperationId: string,
): LifecycleOperationDetails | null {
  const data = asRecord(payload);
  if (!data) {
    return null;
  }

  const operationId =
    getString(data, ["operation_id", "operationId"]) ?? fallbackOperationId;
  if (!operationId) {
    return null;
  }

  const typeValue = getString(data, ["type"]);
  const statusValue = getString(data, ["status"]);
  const errorMessage = getString(data, ["error_message", "errorMessage"]);

  return {
    operationId,
    type: isOperationType(typeValue) ? typeValue : null,
    status: isOperationStatus(statusValue) ? statusValue : null,
    startedAt: getString(data, ["started_at", "startedAt"]),
    finishedAt: getString(data, ["finished_at", "finishedAt"]),
    bytesTotal: getNumber(data, ["bytes_total", "bytesTotal"]),
    filesTotal: getNumber(data, ["files_total", "filesTotal"]),
    bytesCopied: getNumber(data, ["bytes_copied", "bytesCopied"]),
    filesCopied: getNumber(data, ["files_copied", "filesCopied"]),
    errorMessage,
    errorTitle: parseErrorTitle(
      getRecordValue(data, ["error_details", "errorDetails"]),
      errorMessage,
    ),
  };
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    return value;
  }
  return date.toLocaleString();
}

function formatNumber(value: number | null): string {
  if (value === null) {
    return "-";
  }
  return new Intl.NumberFormat().format(value);
}

function formatByteValue(value: number | null): string {
  if (value === null) {
    return "-";
  }
  return formatBytes(value);
}

function formatProgress(
  copied: number | null,
  total: number | null,
  formatter: (value: number | null) => string,
): string {
  if (copied === null && total === null) {
    return "-";
  }
  return `${formatter(copied)} / ${formatter(total)}`;
}

function sleep(delayMs: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(), delayMs);
  });
}

function isRunningLifecycleState(state: LifecycleState): boolean {
  return state === "COOLING" || state === "RESTORING";
}

export default function ProjectLifecyclePanel({
  projectSlug,
  lifecycleState,
  lastLifecycleOperationId,
  lastLifecycleOperationType,
  onLifecycleStateChange,
  fetchFn = toolsFetch,
}: ProjectLifecyclePanelProps) {
  const t = {
    "Project lifecycle": window.gettext("Project lifecycle"),
    Lifecycle: window.gettext("Lifecycle"),
    HOT: window.gettext("HOT"),
    COOLING: window.gettext("COOLING"),
    COOL: window.gettext("COOL"),
    RESTORING: window.gettext("RESTORING"),
    ERROR: window.gettext("ERROR"),
    "Restore project": window.gettext("Restore project"),
    "Retry operation": window.gettext("Retry operation"),
    "Lifecycle operation failed": window.gettext("Lifecycle operation failed"),
    "Operation type": window.gettext("Operation type"),
    "Finished at": window.gettext("Finished at"),
    "Files copied / total": window.gettext("Files copied / total"),
    "Bytes copied / total": window.gettext("Bytes copied / total"),
    "Error title": window.gettext("Error title"),
    "Could not update lifecycle state.": window.gettext(
      "Could not update lifecycle state.",
    ),
  };

  const [operationId, setOperationId] = useState<string | null>(
    lastLifecycleOperationId,
  );
  const [operationType, setOperationType] =
    useState<LifecycleOperationType | null>(lastLifecycleOperationType);
  const [operationDetails, setOperationDetails] =
    useState<LifecycleOperationDetails | null>(null);
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const stateLabel = useMemo(
    () => t[lifecycleState],
    [lifecycleState, t.COOL, t.COOLING, t.ERROR, t.HOT, t.RESTORING],
  );

  const refreshLifecycle = useCallback(async (): Promise<LifecycleSnapshot> => {
    const response = await fetch(
      `/api/data-management/projects/${encodeURIComponent(projectSlug)}/lifecycle`,
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      },
    );
    if (!response.ok) {
      throw new Error(
        `Failed to fetch project lifecycle (status: ${response.status})`,
      );
    }

    const payload = (await response.json()) as unknown;
    const snapshot = normalizeLifecycleSnapshot(payload);
    if (!snapshot) {
      throw new Error("Project lifecycle payload is invalid.");
    }

    onLifecycleStateChange(snapshot.lifecycleState);
    setOperationId(snapshot.lastOperationId);
    setOperationType(snapshot.lastOperationType);
    return snapshot;
  }, [projectSlug, onLifecycleStateChange]);

  const fetchOperationDetails = useCallback(
    async (
      targetOperationId: string,
    ): Promise<LifecycleOperationDetails | null> => {
      const response = await fetchFn(
        `/data/operations/${encodeURIComponent(targetOperationId)}`,
        {
          method: "GET",
        },
      );

      if (response.status === 404) {
        return null;
      }
      if (!response.ok) {
        throw new Error(
          `Failed to fetch operation details (status: ${response.status})`,
        );
      }

      const payload = (await response.json()) as unknown;
      return normalizeOperation(payload, targetOperationId);
    },
    [fetchFn],
  );

  const waitForLifecycleTransition = useCallback(
    async (targetState: LifecycleState): Promise<boolean> => {
      const deadline = Date.now() + TRANSITION_WAIT_MS;
      while (Date.now() < deadline) {
        try {
          const snapshot = await refreshLifecycle();
          if (snapshot.lifecycleState === targetState) {
            return true;
          }
          if (snapshot.lifecycleState === "ERROR" && targetState !== "ERROR") {
            return false;
          }
        } catch (error) {
          console.error(error);
        }
        await sleep(TRANSITION_WAIT_INTERVAL_MS);
      }
      return false;
    },
    [refreshLifecycle],
  );

  const performLifecycleAction = useCallback(
    async (url: string, targetState: LifecycleState): Promise<void> => {
      setActionError(null);
      setIsSubmittingAction(true);

      try {
        const response = await fetchFn(url, {
          method: "POST",
        });
        if (!response.ok) {
          throw new Error(
            `Lifecycle action failed with status ${response.status}.`,
          );
        }

        try {
          const payload = (await response.json()) as unknown;
          const createdOperation = normalizeOperation(payload, "");
          if (createdOperation) {
            setOperationDetails(createdOperation);
            setOperationId(createdOperation.operationId);
            if (createdOperation.type) {
              setOperationType(createdOperation.type);
            }
          }
        } catch {
          // Some tools-api responses do not return operation payloads.
        }

        const transitioned = await waitForLifecycleTransition(targetState);
        if (!transitioned) {
          setActionError(t["Could not update lifecycle state."]);
        }
      } catch (error) {
        console.error(error);
        setActionError(t["Could not update lifecycle state."]);
      } finally {
        setIsSubmittingAction(false);
      }
    },
    [fetchFn, t, waitForLifecycleTransition],
  );

  useEffect(() => {
    if (!operationId) {
      setOperationDetails(null);
      return;
    }

    let cancelled = false;

    fetchOperationDetails(operationId)
      .then((nextOperation) => {
        if (cancelled) {
          return;
        }
        setOperationDetails(nextOperation);
        if (nextOperation?.type) {
          setOperationType(nextOperation.type);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          console.error(error);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [operationId, fetchOperationDetails]);

  useEffect(() => {
    if (!operationId || !isRunningLifecycleState(lifecycleState)) {
      return;
    }

    let cancelled = false;

    const poll = async () => {
      try {
        const nextOperation = await fetchOperationDetails(operationId);
        if (cancelled || !nextOperation) {
          return;
        }

        setOperationDetails(nextOperation);
        if (nextOperation.type) {
          setOperationType(nextOperation.type);
        }

        if (
          nextOperation.status &&
          TERMINAL_OPERATION_STATUSES.has(nextOperation.status)
        ) {
          await refreshLifecycle();
        }
      } catch (error) {
        if (!cancelled) {
          console.error(error);
        }
      }
    };

    poll();
    const intervalId = window.setInterval(poll, POLLING_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [operationId, lifecycleState, fetchOperationDetails, refreshLifecycle]);

  const operationTypeLabel = useMemo(() => {
    const value = operationDetails?.type ?? operationType;
    if (!value) {
      return "-";
    }
    return value;
  }, [operationDetails?.type, operationType]);

  const retryTarget = useMemo(() => {
    const latestOperationType = operationDetails?.type ?? operationType;
    if (latestOperationType === "COOL") {
      return {
        url: `/data/projects/${encodeURIComponent(projectSlug)}/cool`,
        targetState: "COOLING" as LifecycleState,
      };
    }
    if (latestOperationType === "RESTORE") {
      return {
        url: `/data/projects/${encodeURIComponent(projectSlug)}/restore`,
        targetState: "RESTORING" as LifecycleState,
      };
    }
    return null;
  }, [operationDetails?.type, operationType, projectSlug]);

  return (
    <section className="fr-mb-3w">
      <h2 className="fr-h5 fr-mb-1w">{t["Project lifecycle"]}</h2>
      <p className="fr-mb-2w">
        <span className={BADGE_CLASS_BY_STATE[lifecycleState]}>
          {t.Lifecycle}: {stateLabel}
        </span>
      </p>

      {lifecycleState === "COOL" && (
        <button
          type="button"
          className="fr-btn fr-btn--secondary fr-mb-2w"
          disabled={isSubmittingAction}
          onClick={() =>
            performLifecycleAction(
              `/data/projects/${encodeURIComponent(projectSlug)}/restore`,
              "RESTORING",
            )
          }
        >
          {t["Restore project"]}
        </button>
      )}

      {lifecycleState === "ERROR" && (
        <div className="fr-alert fr-alert--error fr-mb-2w">
          <h3 className="fr-alert__title">{t["Lifecycle operation failed"]}</h3>
          <p>
            <strong>{t["Operation type"]}:</strong> {operationTypeLabel}
          </p>
          <p>
            <strong>{t["Error title"]}:</strong>{" "}
            {operationDetails?.errorTitle ||
              operationDetails?.errorMessage ||
              "-"}
          </p>
          <p>
            <strong>{t["Finished at"]}:</strong>{" "}
            {formatDateTime(operationDetails?.finishedAt || null)}
          </p>
          <p>
            <strong>{t["Files copied / total"]}:</strong>{" "}
            {formatProgress(
              operationDetails?.filesCopied ?? null,
              operationDetails?.filesTotal ?? null,
              formatNumber,
            )}
          </p>
          <p>
            <strong>{t["Bytes copied / total"]}:</strong>{" "}
            {formatProgress(
              operationDetails?.bytesCopied ?? null,
              operationDetails?.bytesTotal ?? null,
              formatByteValue,
            )}
          </p>
          {retryTarget && (
            <button
              type="button"
              className="fr-btn fr-btn--secondary"
              disabled={isSubmittingAction}
              onClick={() =>
                performLifecycleAction(retryTarget.url, retryTarget.targetState)
              }
            >
              {t["Retry operation"]}
            </button>
          )}
        </div>
      )}

      {actionError && (
        <div className="fr-alert fr-alert--error fr-alert--sm fr-mb-2w">
          <p>{actionError}</p>
        </div>
      )}
    </section>
  );
}
