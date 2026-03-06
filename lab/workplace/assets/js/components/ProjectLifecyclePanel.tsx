import { useCallback, useEffect, useMemo, useState } from "react";

import { formatBytes } from "../../../../assets/js/utils";
import {
  LIFECYCLE_STATE_CHANGED_EVENT,
  LifecycleOperationType,
  LifecycleState,
  isLifecycleState,
} from "../lifecycle-state";
import {
  LifecycleOperationDetails,
  LifecycleOperationStatus,
  fetchLifecycleOperation,
  fetchProjectLifecycle,
  ProjectLifecycleSnapshot,
  triggerProjectCool,
  triggerProjectRestore,
} from "../project-lifecycle-service";

interface ProjectLifecyclePanelProps {
  projectId: string;
  projectSlug: string;
  lifecycleState: LifecycleState;
  lastLifecycleOperationId: string | null;
  lastLifecycleOperationType: LifecycleOperationType | null;
  onLifecycleStateChange: (state: LifecycleState) => void;
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
  projectId,
  projectSlug,
  lifecycleState: initialLifecycleState,
  lastLifecycleOperationId,
  lastLifecycleOperationType,
  onLifecycleStateChange,
}: ProjectLifecyclePanelProps) {
  const t = {
    "Data availability": window.gettext("Data availability"),
    Lifecycle: window.gettext("Lifecycle"),
    HOT: window.gettext("available"),
    COOL: window.gettext("archived"),
    COOLING: window.gettext("archiving"),
    RESTORING: window.gettext("restoring"),
    ERROR: window.gettext("error"),
    "Archive project data": window.gettext("Archive project data"),
    "Restore project data": window.gettext("Restore project data"),
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
    availabilityDescription: {
      HOT: "Project data is available and can be accessed from the virtual workstation.",
      COOL: "Project data is archived in cold storage and is not currently accessible. Restore the data to make it available again.",
      COOLING:
        "Project data is currently being archived to cold storage. Some operations may be temporarily unavailable during this process.",
      RESTORING:
        "Archived project data is currently being restored. The data will become available once the restoration is complete.",
      ERROR:
        "An error occurred while processing the project data. You can retry the operation.",
    },
  };

  const [operationId, setOperationId] = useState<string | null>(
    lastLifecycleOperationId,
  );
  const [lifecycleState, setLifecycleState] = useState<LifecycleState>(
    initialLifecycleState,
  );
  const [operationType, setOperationType] =
    useState<LifecycleOperationType | null>(lastLifecycleOperationType);
  const [operationDetails, setOperationDetails] =
    useState<LifecycleOperationDetails | null>(null);
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    const handler = (event: Event): void => {
      const customEvent = event as CustomEvent<unknown>;
      if (isLifecycleState(customEvent.detail)) {
        setLifecycleState(customEvent.detail);
      }
    };

    window.addEventListener(LIFECYCLE_STATE_CHANGED_EVENT, handler);
    return () => {
      window.removeEventListener(LIFECYCLE_STATE_CHANGED_EVENT, handler);
    };
  }, []);

  useEffect(() => {
    setLifecycleState(initialLifecycleState);
  }, [initialLifecycleState]);

  const refreshLifecycle =
    useCallback(async (): Promise<ProjectLifecycleSnapshot> => {
      const snapshot = await fetchProjectLifecycle(projectSlug);
      onLifecycleStateChange(snapshot.lifecycleState);
      setOperationId(snapshot.lastOperationId);
      setOperationType(snapshot.lastOperationType);
      return snapshot;
    }, [projectSlug, onLifecycleStateChange]);

  const fetchOperationDetails = useCallback(
    async (
      targetOperationId: string,
    ): Promise<LifecycleOperationDetails | null> => {
      return fetchLifecycleOperation(targetOperationId);
    },
    [],
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
    async (
      actionType: LifecycleOperationType,
      targetState: LifecycleState,
    ): Promise<void> => {
      setActionError(null);
      setIsSubmittingAction(true);

      try {
        const createdOperation =
          actionType === "COOL"
            ? await triggerProjectCool(projectId)
            : await triggerProjectRestore(projectId);
        if (createdOperation) {
          setOperationDetails(createdOperation);
          setOperationId(createdOperation.operationId);
          if (createdOperation.type) {
            setOperationType(createdOperation.type);
          }
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
    [projectId, projectSlug, t, waitForLifecycleTransition],
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
        actionType: "COOL" as LifecycleOperationType,
        targetState: "COOLING" as LifecycleState,
      };
    }
    if (latestOperationType === "RESTORE") {
      return {
        actionType: "RESTORE" as LifecycleOperationType,
        targetState: "RESTORING" as LifecycleState,
      };
    }
    return null;
  }, [operationDetails?.type, operationType]);

  return (
    <section className="fr-mb-3w">
      <h2 className="fr-h5 fr-mb-1w">{t["Data availability"]}</h2>
      <div className="fr-mb-2w">
        <p>
          <span className={BADGE_CLASS_BY_STATE[lifecycleState]}>
            {t[lifecycleState]}
          </span>
        </p>
        <p>{t.availabilityDescription[lifecycleState]}</p>
      </div>

      {lifecycleState === "HOT" && (
        <div className="fr-px-1w">
          <button
            type="button"
            className="fr-btn fr-btn--secondary fr-mb-2w"
            disabled={isSubmittingAction}
            onClick={() => performLifecycleAction("COOL", "COOLING")}
          >
            {t["Archive project data"]}
          </button>
        </div>
      )}

      {lifecycleState === "COOL" && (
        <div className="fr-px-1w">
          <button
            type="button"
            className="fr-btn fr-btn--secondary fr-mb-2w"
            disabled={isSubmittingAction}
            onClick={() => performLifecycleAction("RESTORE", "RESTORING")}
          >
            {t["Restore project data"]}
          </button>
        </div>
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
                performLifecycleAction(
                  retryTarget.actionType,
                  retryTarget.targetState,
                )
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
