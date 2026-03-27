import {
  fetchLifecycleOperation,
  fetchProjectLifecycle,
  triggerProjectCool,
  triggerProjectRestore,
} from "../assets/js/project-lifecycle-service";

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

describe("project-lifecycle-service", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    global.fetch = fetchMock as typeof fetch;
    document.cookie = "csrftoken=test-csrf-token";
  });

  afterEach(() => {
    document.cookie =
      "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    vi.restoreAllMocks();
  });

  it("fetches and converts the project lifecycle snapshot", async () => {
    fetchMock.mockResolvedValueOnce(
      createJSONResponse({
        lifecycle_state: "COOLING",
        last_operation_id: "op-1",
        last_operation_type: "COOL",
      }),
    );

    const snapshot = await fetchProjectLifecycle("project slug");

    expect(snapshot).toEqual({
      lifecycleState: "COOLING",
      lastOperationId: "op-1",
      lastOperationType: "COOL",
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/data-management/projects/project%20slug/lifecycle",
      {
        method: "GET",
        headers: {
          Accept: "application/json",
        },
      },
    );
  });

  it("returns a hot snapshot when the lifecycle endpoint is unavailable", async () => {
    fetchMock.mockResolvedValueOnce(createJSONResponse({}, 404));

    const snapshot = await fetchProjectLifecycle("project slug");

    expect(snapshot).toEqual({
      lifecycleState: "HOT",
      lastOperationId: null,
      lastOperationType: null,
    });
  });

  it("throws when the lifecycle endpoint rejects access", async () => {
    fetchMock.mockResolvedValueOnce(createJSONResponse({}, 403));

    await expect(fetchProjectLifecycle("project slug")).rejects.toThrow(
      "Failed to fetch project lifecycle (status: 403)",
    );
  });

  it("returns normalized operation details", async () => {
    fetchMock.mockResolvedValueOnce(
      createJSONResponse({
        operation_id: "op-1",
        type: "RESTORE",
        status: "FAILED",
        started_at: "2026-03-12T12:00:00Z",
        finished_at: "2026-03-12T12:05:00Z",
        bytes_total: 200,
        files_total: 20,
        bytes_copied: 50,
        files_copied: 5,
        error: {
          title: "Restore failed.",
          message: "Blob copy failed.",
        },
      }),
    );

    const details = await fetchLifecycleOperation("op-1");

    expect(details).toEqual({
      operationId: "op-1",
      type: "RESTORE",
      status: "FAILED",
      startedAt: "2026-03-12T12:00:00Z",
      finishedAt: "2026-03-12T12:05:00Z",
      bytesTotal: 200,
      filesTotal: 20,
      bytesCopied: 50,
      filesCopied: 5,
      errorTitle: "Restore failed.",
      errorMessage: "Blob copy failed.",
    });
  });

  it("returns null for missing operations", async () => {
    fetchMock.mockResolvedValueOnce(createJSONResponse({}, 404));

    const details = await fetchLifecycleOperation("missing-op");

    expect(details).toBeNull();
  });

  it("posts cooling requests with the csrf token and converts the response", async () => {
    fetchMock.mockResolvedValueOnce(
      createJSONResponse({
        operation_id: "op-2",
        type: "COOL",
        status: "RUNNING",
      }, 202),
    );

    const details = await triggerProjectCool("123");

    expect(details).toEqual({
      operationId: "op-2",
      type: "COOL",
      status: "RUNNING",
      startedAt: null,
      finishedAt: null,
      bytesTotal: null,
      filesTotal: null,
      bytesCopied: null,
      filesCopied: null,
      errorTitle: null,
      errorMessage: null,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/data-management/projects/123/cool",
      {
        method: "POST",
        headers: {
          "X-CSRFToken": "test-csrf-token",
          Accept: "application/json",
        },
      },
    );
  });

  it("throws when the restore trigger endpoint rejects the request", async () => {
    fetchMock.mockResolvedValueOnce(createJSONResponse({}, 502));

    await expect(triggerProjectRestore("123")).rejects.toThrow(
      "Lifecycle action failed with status 502.",
    );
  });
});
