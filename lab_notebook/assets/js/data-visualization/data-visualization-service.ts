import type { EuphrosyneFile } from "../../../../lab/assets/js/file-service";
import type { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import { TRAUPIXE_FORMAT } from "./formats/traupixe";
import type { DataVisualizationResponse } from "./types";

const SUPPORTED_FORMATS = [TRAUPIXE_FORMAT];

export function findVisualizableDataFiles(
  files: EuphrosyneFile[],
): EuphrosyneFile[] {
  return files
    .filter((file) => SUPPORTED_FORMATS.some((format) => format.accepts(file)))
    .sort((left, right) => {
      const dateDifference =
        right.lastModified.getTime() - left.lastModified.getTime();
      return dateDifference || left.name.localeCompare(right.name);
    });
}

export class DataVisualizationError extends Error {
  constructor(
    public readonly requestId: string | null,
    public readonly reason: string | null,
  ) {
    super("Data visualization request failed");
  }
}

export async function createDataVisualization({
  fetchFn,
  projectSlug,
  dataFile,
  question,
}: {
  fetchFn: ToolsFetch;
  projectSlug: string;
  dataFile: EuphrosyneFile;
  question: string;
}): Promise<DataVisualizationResponse> {
  const response = await fetchFn(
    `/data/${encodeURIComponent(projectSlug)}/visualizations`,
    {
      method: "POST",
      body: JSON.stringify({ path: dataFile.path, question }),
    },
  );
  if (!response.ok) {
    const details = await readErrorDetails(response);
    throw new DataVisualizationError(
      response.headers.get("X-Request-ID") || details.requestId,
      details.reason,
    );
  }
  return (await response.json()) as DataVisualizationResponse;
}

async function readErrorDetails(
  response: Response,
): Promise<{ requestId: string | null; reason: string | null }> {
  try {
    const payload = (await response.json()) as {
      detail?: string | { reason?: unknown; request_id?: unknown };
    };
    if (typeof payload.detail === "string") {
      return { requestId: null, reason: payload.detail.slice(0, 500) };
    }
    return {
      reason:
        typeof payload.detail?.reason === "string"
          ? payload.detail.reason.slice(0, 500)
          : null,
      requestId:
        typeof payload.detail?.request_id === "string"
          ? payload.detail.request_id
          : null,
    };
  } catch {
    return { requestId: null, reason: null };
  }
}
