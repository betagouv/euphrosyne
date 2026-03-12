import { act, useState } from "react";
import type { Root } from "react-dom/client";
import { createRoot } from "react-dom/client";

import type {
  LifecycleOperationType,
  LifecycleState,
} from "../assets/js/lifecycle-state";
import type { LifecycleOperationDetails } from "../assets/js/project-lifecycle-service";
import useProjectLifecycle from "../assets/js/useProjectLifecycle";

interface HarnessProps {
  initialLifecycleState: LifecycleState | null;
  initialOperationId: string | null;
  initialOperationType: LifecycleOperationType | null;
  projectId?: string;
  projectSlug?: string;
  actionErrorMessage?: string;
}

interface HarnessSnapshot {
  actionError: string | null;
  isSubmittingAction: boolean;
  lifecycleState: LifecycleState | null;
  operationDetails: LifecycleOperationDetails | null;
  operationTypeLabel: string;
  stateChanges: LifecycleState[];
}

let latestSnapshot: HarnessSnapshot | null = null;
let latestPerformLifecycleAction:
  | ((
      actionType: LifecycleOperationType,
      targetState: LifecycleState,
    ) => Promise<void>)
  | null = null;

function createJSONResponse<T>(
  payload: T,
  status = 200,
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

async function flushAsyncWork(iterations = 5): Promise<void> {
  for (let index = 0; index < iterations; index += 1) {
    await act(async () => {
      await Promise.resolve();
    });
  }
}

function HookHarness({
  initialLifecycleState,
  initialOperationId,
  initialOperationType,
  projectId = "42",
  projectSlug = "project-slug",
  actionErrorMessage = "Could not update lifecycle state.",
}: HarnessProps) {
  const [lifecycleState, setLifecycleState] = useState<LifecycleState | null>(
    initialLifecycleState,
  );
  const [stateChanges, setStateChanges] = useState<LifecycleState[]>([]);
  const {
    actionError,
    isSubmittingAction,
    operationDetails,
    operationTypeLabel,
    performLifecycleAction,
  } = useProjectLifecycle({
    projectId,
    projectSlug,
    lifecycleState,
    lastLifecycleOperationId: initialOperationId,
    lastLifecycleOperationType: initialOperationType,
    onLifecycleStateChange(nextState) {
      setLifecycleState(nextState);
      setStateChanges((previousStateChanges) => [
        ...previousStateChanges,
        nextState,
      ]);
    },
    actionErrorMessage,
  });

  latestSnapshot = {
    actionError,
    isSubmittingAction,
    lifecycleState,
    operationDetails,
    operationTypeLabel,
    stateChanges,
  };
  latestPerformLifecycleAction = performLifecycleAction;

  return null;
}

describe("useProjectLifecycle", () => {
  let container: HTMLDivElement;
  let root: Root | null;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
    fetchMock = vi.fn();
    global.fetch = fetchMock as typeof fetch;
    vi.spyOn(console, "error").mockImplementation(() => {});
    latestSnapshot = null;
    latestPerformLifecycleAction = null;
  });

  afterEach(async () => {
    if (root) {
      await act(async () => {
        root?.unmount();
      });
    }
    container.remove();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  async function renderHarness(props: HarnessProps): Promise<void> {
    await act(async () => {
      root?.render(<HookHarness {...props} />);
    });
    await flushAsyncWork();
  }

  it("refreshes lifecycle state when polling reaches a succeeded terminal operation", async () => {
    vi.useFakeTimers();
    let operationFetchCount = 0;

    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.endsWith("/api/data-management/operations/op-success")) {
        operationFetchCount += 1;
        if (operationFetchCount < 3) {
          return createJSONResponse({
            operation_id: "op-success",
            type: "COOL",
            status: "RUNNING",
          });
        }
        return createJSONResponse({
          operation_id: "op-success",
          type: "COOL",
          status: "SUCCEEDED",
          finished_at: "2026-03-12T10:05:00Z",
        });
      }

      if (
        url.endsWith("/api/data-management/projects/project-slug/lifecycle")
      ) {
        return createJSONResponse({
          lifecycle_state: "COOL",
          last_operation_id: "op-success",
          last_operation_type: "COOL",
        });
      }

      throw new Error(`Unexpected fetch URL: ${url}`);
    });

    await renderHarness({
      initialLifecycleState: "COOLING",
      initialOperationId: "op-success",
      initialOperationType: "COOL",
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    await flushAsyncWork();

    expect(latestSnapshot).toMatchObject({
      lifecycleState: "COOL",
      operationDetails: {
        operationId: "op-success",
        status: "SUCCEEDED",
        type: "COOL",
        finishedAt: "2026-03-12T10:05:00Z",
      },
    });
    expect(latestSnapshot?.stateChanges).toContain("COOL");
  });

  it("refreshes lifecycle state when polling reaches a failed terminal operation", async () => {
    vi.useFakeTimers();
    let operationFetchCount = 0;

    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.endsWith("/api/data-management/operations/op-failed")) {
        operationFetchCount += 1;
        if (operationFetchCount < 3) {
          return createJSONResponse({
            operation_id: "op-failed",
            type: "RESTORE",
            status: "RUNNING",
          });
        }
        return createJSONResponse({
          operation_id: "op-failed",
          type: "RESTORE",
          status: "FAILED",
          error: {
            title: "Restore failed.",
            message: "Blob copy failed.",
          },
        });
      }

      if (
        url.endsWith("/api/data-management/projects/project-slug/lifecycle")
      ) {
        return createJSONResponse({
          lifecycle_state: "ERROR",
          last_operation_id: "op-failed",
          last_operation_type: "RESTORE",
        });
      }

      throw new Error(`Unexpected fetch URL: ${url}`);
    });

    await renderHarness({
      initialLifecycleState: "RESTORING",
      initialOperationId: "op-failed",
      initialOperationType: "RESTORE",
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    await flushAsyncWork();

    expect(latestSnapshot).toMatchObject({
      lifecycleState: "ERROR",
      operationDetails: {
        operationId: "op-failed",
        status: "FAILED",
        type: "RESTORE",
        errorTitle: "Restore failed.",
        errorMessage: "Blob copy failed.",
      },
      stateChanges: ["ERROR"],
    });
  });

  it("surfaces an action error when the lifecycle refresh returns error after triggering cooling", async () => {
    document.cookie = "csrftoken=test-csrf-token";

    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input);

      if (url.endsWith("/api/data-management/projects/42/cool")) {
        return createJSONResponse(
          {
            operation_id: "op-retry",
          },
          202,
        );
      }

      if (
        url.endsWith("/api/data-management/projects/project-slug/lifecycle")
      ) {
        return createJSONResponse({
          lifecycle_state: "ERROR",
          last_operation_id: "op-retry",
          last_operation_type: "COOL",
        });
      }

      if (url.endsWith("/api/data-management/operations/op-retry")) {
        return createJSONResponse({
          operation_id: "op-retry",
          type: "COOL",
          status: "FAILED",
          error: {
            title: "Cooling failed.",
            message: "Verification failed.",
          },
        });
      }

      throw new Error(`Unexpected fetch URL: ${url}`);
    });

    await renderHarness({
      initialLifecycleState: "HOT",
      initialOperationId: null,
      initialOperationType: null,
    });

    await act(async () => {
      await latestPerformLifecycleAction?.("COOL", "COOLING");
    });
    await flushAsyncWork();

    expect(latestSnapshot).toMatchObject({
      actionError: "Could not update lifecycle state.",
      isSubmittingAction: false,
      lifecycleState: "ERROR",
      operationDetails: {
        operationId: "op-retry",
        status: "FAILED",
        type: "COOL",
      },
      stateChanges: ["ERROR"],
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/data-management/projects/42/cool",
      {
        method: "POST",
        headers: {
          "X-CSRFToken": "test-csrf-token",
          Accept: "application/json",
        },
      },
    );
  });
});
