import type { EuphrosyneFile } from "../../../../lab/assets/js/file-service";
import type { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import { TRAUPIXE_FORMAT } from "./formats/traupixe";
import {
  DATA_VISUALIZATION_ERROR_CODES,
  type DataVisualizationErrorCode,
  type DataVisualizationResponse,
} from "./types";

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
    public readonly code: DataVisualizationErrorCode | null,
    public readonly requestId: string | null,
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
    throw new DataVisualizationError(details.code, details.requestId);
  }
  return (await response.json()) as DataVisualizationResponse;
}

async function readErrorDetails(response: Response): Promise<{
  code: DataVisualizationErrorCode | null;
  requestId: string | null;
}> {
  try {
    const payload = (await response.json()) as {
      detail?: { code?: unknown; request_id?: unknown };
    };
    return {
      code: isDataVisualizationErrorCode(payload.detail?.code)
        ? payload.detail.code
        : null,
      requestId:
        typeof payload.detail?.request_id === "string"
          ? payload.detail.request_id
          : null,
    };
  } catch {
    return { code: null, requestId: null };
  }
}

function isDataVisualizationErrorCode(
  value: unknown,
): value is DataVisualizationErrorCode {
  return DATA_VISUALIZATION_ERROR_CODES.some((code) => code === value);
}
