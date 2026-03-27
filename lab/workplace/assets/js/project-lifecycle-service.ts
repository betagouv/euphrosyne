import { getCSRFToken } from "../../../assets/js/utils";
import { LifecycleOperationType, LifecycleState } from "./lifecycle-state";

async function parseJSONResponse(response: Response): Promise<unknown | null> {
  try {
    return (await response.json()) as unknown;
  } catch {
    return null;
  }
}

export type LifecycleOperationStatus =
  | "PENDING"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED";

export interface LifecycleOperationDetails {
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

export interface ProjectLifecycleSnapshot {
  lifecycleState: LifecycleState;
  lastOperationId: string | null;
  lastOperationType: LifecycleOperationType | null;
}

interface LifecycleOperationErrorResponse {
  title?: string | null;
  message?: string | null;
}

interface ProjectLifecycleResponse {
  lifecycle_state: LifecycleState;
  last_operation_id: string | null;
  last_operation_type: LifecycleOperationType | null;
}

interface LifecycleOperationResponse {
  operation_id: string;
  type?: LifecycleOperationType | null;
  status?: LifecycleOperationStatus | null;
  started_at?: string | null;
  finished_at?: string | null;
  bytes_total?: number | null;
  files_total?: number | null;
  bytes_copied?: number | null;
  files_copied?: number | null;
  error?: LifecycleOperationErrorResponse | null;
}

function convertDataToLifecycleOperation(
  data: LifecycleOperationResponse,
): LifecycleOperationDetails {
  const errorTitle = data.error?.title || data.error?.message || null;
  const errorMessage = data.error?.message || data.error?.title || null;

  return {
    operationId: data.operation_id,
    type: data.type ?? null,
    status: data.status ?? null,
    startedAt: data.started_at ?? null,
    finishedAt: data.finished_at ?? null,
    bytesTotal: data.bytes_total ?? null,
    filesTotal: data.files_total ?? null,
    bytesCopied: data.bytes_copied ?? null,
    filesCopied: data.files_copied ?? null,
    errorMessage,
    errorTitle,
  };
}

function convertDataToProjectLifecycle(
  data: ProjectLifecycleResponse,
): ProjectLifecycleSnapshot {
  return {
    lifecycleState: data.lifecycle_state,
    lastOperationId: data.last_operation_id,
    lastOperationType: data.last_operation_type,
  };
}

export async function fetchProjectLifecycle(
  projectSlug: string,
): Promise<ProjectLifecycleSnapshot> {
  const response = await fetch(
    `/api/data-management/projects/${encodeURIComponent(projectSlug)}/lifecycle`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    },
  );

  if (response.status === 404) {
    // endpoint is deactivated : treat all project data as hot
    return {
      lifecycleState: "HOT",
      lastOperationId: null,
      lastOperationType: null,
    };
  }

  if (!response.ok) {
    throw new Error(
      `Failed to fetch project lifecycle (status: ${response.status})`,
    );
  }

  const payload = await parseJSONResponse(response);
  if (!payload) {
    throw new Error("Project lifecycle payload is invalid.");
  }

  return convertDataToProjectLifecycle(payload as ProjectLifecycleResponse);
}

export async function fetchLifecycleOperation(
  operationId: string,
): Promise<LifecycleOperationDetails | null> {
  const response = await fetch(
    `/api/data-management/operations/${encodeURIComponent(operationId)}`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
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

  const payload = await parseJSONResponse(response);
  if (!payload) {
    return null;
  }
  return convertDataToLifecycleOperation(payload as LifecycleOperationResponse);
}

export async function triggerProjectCool(
  projectId: string,
): Promise<LifecycleOperationDetails | null> {
  const response = await fetch(
    `/api/data-management/projects/${encodeURIComponent(projectId)}/cool`,
    {
      method: "POST",
      headers: {
        "X-CSRFToken": getCSRFToken() || "",
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(`Lifecycle action failed with status ${response.status}.`);
  }

  const payload = await parseJSONResponse(response);
  if (!payload) {
    return null;
  }
  return convertDataToLifecycleOperation(payload as LifecycleOperationResponse);
}

export async function triggerProjectRestore(
  projectId: string,
): Promise<LifecycleOperationDetails | null> {
  const response = await fetch(
    `/api/data-management/projects/${encodeURIComponent(projectId)}/restore`,
    {
      method: "POST",
      headers: {
        "X-CSRFToken": getCSRFToken() || "",
        Accept: "application/json",
      },
    },
  );

  if (!response.ok) {
    throw new Error(`Lifecycle action failed with status ${response.status}.`);
  }

  const payload = await parseJSONResponse(response);
  if (!payload) {
    return null;
  }
  return convertDataToLifecycleOperation(payload as LifecycleOperationResponse);
}
