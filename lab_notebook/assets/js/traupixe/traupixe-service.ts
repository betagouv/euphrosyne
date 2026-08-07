import type { EuphrosyneFile } from "../../../../lab/assets/js/file-service";
import type { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import type { TraupixeVisualizationResponse } from "./types";

const MAX_TRAUPIXE_SIZE = 100 * 1024 * 1024;

export function filterTraupixeFiles(files: EuphrosyneFile[]): EuphrosyneFile[] {
  return files
    .filter(
      (file) =>
        !file.isDir &&
        file.name.toLocaleLowerCase().includes("traupixe") &&
        file.name.toLocaleLowerCase().endsWith(".xlsx") &&
        file.size !== null &&
        file.size > 0 &&
        file.size <= MAX_TRAUPIXE_SIZE,
    )
    .sort((left, right) => {
      const dateDifference =
        right.lastModified.getTime() - left.lastModified.getTime();
      return dateDifference || left.name.localeCompare(right.name);
    });
}

export class TraupixeVisualizationError extends Error {
  constructor(
    public readonly requestId: string | null,
    public readonly reason: string | null,
  ) {
    super("TRAUPIXE visualization request failed");
  }
}

export async function createTraupixeVisualization({
  fetchFn,
  projectSlug,
  path,
  question,
}: {
  fetchFn: ToolsFetch;
  projectSlug: string;
  path: string;
  question: string;
}): Promise<TraupixeVisualizationResponse> {
  const response = await fetchFn(
    `/aglae/${encodeURIComponent(projectSlug)}/visualizations`,
    {
      method: "POST",
      body: JSON.stringify({ path, question }),
    },
  );
  if (!response.ok) {
    const details = await readErrorDetails(response);
    throw new TraupixeVisualizationError(
      response.headers.get("X-Request-ID") || details.requestId,
      details.reason,
    );
  }
  return (await response.json()) as TraupixeVisualizationResponse;
}

async function readErrorDetails(
  response: Response,
): Promise<{ requestId: string | null; reason: string | null }> {
  try {
    const payload = (await response.json()) as {
      detail?:
        | string
        | {
            reason?: unknown;
            request_id?: unknown;
          };
    };
    if (typeof payload.detail === "string") {
      return {
        requestId: null,
        reason: payload.detail.slice(0, 500),
      };
    }
    const reason =
      typeof payload.detail?.reason === "string"
        ? payload.detail.reason.slice(0, 500)
        : null;
    const requestId =
      typeof payload.detail?.request_id === "string"
        ? payload.detail.request_id
        : null;
    return { requestId, reason };
  } catch {
    return { requestId: null, reason: null };
  }
}
