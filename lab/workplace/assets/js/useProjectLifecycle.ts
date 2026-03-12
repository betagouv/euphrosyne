import { useCallback, useEffect, useMemo, useState } from "react";

import {
  LifecycleOperationType,
  LifecycleState,
} from "./lifecycle-state";
import {
  LifecycleOperationDetails,
  LifecycleOperationStatus,
  fetchLifecycleOperation,
  fetchProjectLifecycle,
  ProjectLifecycleSnapshot,
  triggerProjectCool,
  triggerProjectRestore,
} from "./project-lifecycle-service";

interface LifecycleOperationSummary {
  id: string | null;
  type: LifecycleOperationType | null;
}

interface RetryTarget {
  actionType: LifecycleOperationType;
  targetState: LifecycleState;
}

interface UseProjectLifecycleOptions {
  projectId: string;
  projectSlug: string;
  lifecycleState: LifecycleState | null;
  lastLifecycleOperationId: string | null;
  lastLifecycleOperationType: LifecycleOperationType | null;
  onLifecycleStateChange: (state: LifecycleState) => void;
  actionErrorMessage: string;
}

interface UseProjectLifecycleResult {
  operationDetails: LifecycleOperationDetails | null;
  operationTypeLabel: string;
  retryTarget: RetryTarget | null;
  actionError: string | null;
  isSubmittingAction: boolean;
  performLifecycleAction: (
    actionType: LifecycleOperationType,
    targetState: LifecycleState,
  ) => Promise<void>;
}

const POLLING_INTERVAL_MS = 5000;
const TRANSITION_WAIT_MS = 60000;
const TRANSITION_WAIT_INTERVAL_MS = 2000;
const TERMINAL_OPERATION_STATUSES = new Set<LifecycleOperationStatus>([
  "SUCCEEDED",
  "FAILED",
]);

function sleep(delayMs: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(() => resolve(), delayMs);
  });
}

function isRunningLifecycleState(state: LifecycleState): boolean {
  return state === "COOLING" || state === "RESTORING";
}

export default function useProjectLifecycle({
  projectId,
  projectSlug,
  lifecycleState,
  lastLifecycleOperationId,
  lastLifecycleOperationType,
  onLifecycleStateChange,
  actionErrorMessage,
}: UseProjectLifecycleOptions): UseProjectLifecycleResult {
  const [currentOperation, setCurrentOperation] = useState<LifecycleOperationSummary>({
    id: lastLifecycleOperationId,
    type: lastLifecycleOperationType,
  });
  const [operationDetails, setOperationDetails] =
    useState<LifecycleOperationDetails | null>(null);
  const [isSubmittingAction, setIsSubmittingAction] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  useEffect(() => {
    setCurrentOperation((previousOperation) => {
      if (
        previousOperation.id === lastLifecycleOperationId &&
        previousOperation.type === lastLifecycleOperationType
      ) {
        return previousOperation;
      }
      return {
        id: lastLifecycleOperationId,
        type: lastLifecycleOperationType,
      };
    });
  }, [lastLifecycleOperationId, lastLifecycleOperationType]);

  const refreshLifecycle = useCallback(async (): Promise<ProjectLifecycleSnapshot> => {
    const snapshot = await fetchProjectLifecycle(projectSlug);
    onLifecycleStateChange(snapshot.lifecycleState);
    setCurrentOperation({
      id: snapshot.lastOperationId,
      type: snapshot.lastOperationType,
    });
    return snapshot;
  }, [projectSlug, onLifecycleStateChange]);

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
          setCurrentOperation({
            id: createdOperation.operationId,
            type: createdOperation.type ?? actionType,
          });
        }

        const transitioned = await waitForLifecycleTransition(targetState);
        if (!transitioned) {
          setActionError(actionErrorMessage);
        }
      } catch (error) {
        console.error(error);
        setActionError(actionErrorMessage);
      } finally {
        setIsSubmittingAction(false);
      }
    },
    [actionErrorMessage, projectId, waitForLifecycleTransition],
  );

  useEffect(() => {
    if (!currentOperation.id) {
      setOperationDetails(null);
      return;
    }

    let cancelled = false;

    void fetchLifecycleOperation(currentOperation.id)
      .then((nextOperation) => {
        if (cancelled) {
          return;
        }
        setOperationDetails(nextOperation);
        if (nextOperation?.type) {
          setCurrentOperation((previousOperation) => ({
            ...previousOperation,
            type: nextOperation.type,
          }));
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
  }, [currentOperation.id]);

  useEffect(() => {
    if (
      !currentOperation.id ||
      !lifecycleState ||
      !isRunningLifecycleState(lifecycleState)
    ) {
      return;
    }

    let cancelled = false;

    const poll = async () => {
      try {
        const nextOperation = await fetchLifecycleOperation(currentOperation.id!);
        if (cancelled || !nextOperation) {
          return;
        }

        setOperationDetails(nextOperation);
        if (nextOperation.type) {
          setCurrentOperation((previousOperation) => ({
            ...previousOperation,
            type: nextOperation.type,
          }));
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

    void poll();
    const intervalId = window.setInterval(() => {
      void poll();
    }, POLLING_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [currentOperation.id, lifecycleState, refreshLifecycle]);

  const operationTypeLabel = useMemo(() => {
    if (!currentOperation.type) {
      return "-";
    }
    return currentOperation.type;
  }, [currentOperation.type]);

  const retryTarget = useMemo((): RetryTarget | null => {
    if (currentOperation.type === "COOL") {
      return {
        actionType: "COOL",
        targetState: "COOLING",
      };
    }
    if (currentOperation.type === "RESTORE") {
      return {
        actionType: "RESTORE",
        targetState: "RESTORING",
      };
    }
    return null;
  }, [currentOperation.type]);

  return {
    operationDetails,
    operationTypeLabel,
    retryTarget,
    actionError,
    isSubmittingAction,
    performLifecycleAction,
  };
}
