import { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import { HDF5Dataset, HDF5Entity, HDF5Group } from "./types";

export const HDF5_DATA_TRANSFER_PROGRESS_EVENT = "hdf5:data-transfer-progress";

export interface HDF5DataTransferProgressDetail {
  file: string | null;
  path: string | null;
  loaded: number;
  total: number | null;
  done: boolean;
}

type HDF5MetadataGroupResponse = Omit<HDF5Group, "path" | "children"> & {
  children?: HDF5MetadataEntityResponse[];
};
type HDF5MetadataDatasetResponse = Omit<HDF5Dataset, "path">;
type HDF5MetadataEntityResponse =
  | HDF5MetadataGroupResponse
  | HDF5MetadataDatasetResponse;

export async function fetchHDF5Metadata(
  fetchFn: ToolsFetch,
  filePath: string,
  path: string,
): Promise<HDF5Entity> {
  const query = new URLSearchParams({ file: filePath, path });
  const response = await fetchFn(`/hdf5/meta/?${query.toString()}`, {
    method: "GET",
  });
  if (!response.ok) {
    throw new Error(
      `Failed to fetch HDF5 metadata for ${filePath}${path}. Response status: ${response.status}`,
    );
  }
  return addEntityPaths(
    (await response.json()) as HDF5MetadataEntityResponse,
    path,
  );
}

export async function fetchHDF5AttributeValues(
  fetchFn: ToolsFetch,
  filePath: string,
  path: string,
): Promise<Record<string, unknown>> {
  const query = new URLSearchParams({ file: filePath, path });
  const response = await fetchFn(`/hdf5/attr/?${query.toString()}`, {
    method: "GET",
  });
  if (!response.ok) {
    throw new Error(
      `Failed to fetch HDF5 attributes for ${filePath}${path}. Response status: ${response.status}`,
    );
  }
  return (await response.json()) as Record<string, unknown>;
}

export function createToolsH5GroveFetcher(fetchFn: ToolsFetch) {
  return async (
    url: string,
    params: Record<string, string>,
    opts?: { abortSignal?: AbortSignal },
  ) => {
    const query = new URLSearchParams(params);
    const response = await fetchFn(`${url}?${query.toString()}`, {
      method: "GET",
      signal: opts?.abortSignal,
    });
    if (!response.ok) {
      throw new Error(
        `Failed to fetch HDF5 data. Response status: ${response.status}`,
      );
    }
    return readResponseWithProgress(response, {
      file: params.file || null,
      path: params.path || null,
    });
  };
}

async function readResponseWithProgress(
  response: Response,
  request: Pick<HDF5DataTransferProgressDetail, "file" | "path">,
): Promise<ArrayBuffer> {
  const total = getContentLength(response);

  dispatchDataTransferProgress({
    ...request,
    loaded: 0,
    total,
    done: false,
  });

  if (!response.body) {
    const buffer = await response.arrayBuffer();
    dispatchDataTransferProgress({
      ...request,
      loaded: buffer.byteLength,
      total: total ?? buffer.byteLength,
      done: true,
    });
    return buffer;
  }

  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let loaded = 0;
  let isReading = true;

  while (isReading) {
    const { done, value } = await reader.read();
    if (done) {
      isReading = false;
      continue;
    }
    if (!value) {
      continue;
    }
    chunks.push(value);
    loaded += value.byteLength;
    dispatchDataTransferProgress({
      ...request,
      loaded,
      total,
      done: false,
    });
  }

  const buffer = concatenateChunks(chunks, loaded);
  dispatchDataTransferProgress({
    ...request,
    loaded,
    total: total ?? loaded,
    done: true,
  });
  return buffer;
}

function getContentLength(response: Response): number | null {
  const contentLength = response.headers.get("Content-Length");
  if (!contentLength) {
    return null;
  }
  const parsedLength = Number(contentLength);
  return Number.isFinite(parsedLength) && parsedLength >= 0
    ? parsedLength
    : null;
}

function concatenateChunks(chunks: Uint8Array[], byteLength: number) {
  const bytes = new Uint8Array(byteLength);
  let offset = 0;
  chunks.forEach((chunk) => {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  });
  return bytes.buffer;
}

function dispatchDataTransferProgress(detail: HDF5DataTransferProgressDetail) {
  window.dispatchEvent(
    new CustomEvent<HDF5DataTransferProgressDetail>(
      HDF5_DATA_TRANSFER_PROGRESS_EVENT,
      { detail },
    ),
  );
}

function addEntityPaths(
  entity: HDF5MetadataEntityResponse,
  path: string,
): HDF5Entity {
  if (entity.kind === "group") {
    return {
      ...entity,
      path,
      children: (entity.children ?? []).map((child) =>
        addEntityPaths(child, getEntityPath(path, child.name)),
      ),
    };
  }

  if (entity.kind === "dataset") {
    return {
      ...entity,
      path,
    };
  }

  throw new Error("Unexpected HDF5 entity kind.");
}

function getEntityPath(parentPath: string, childName: string): string {
  if (parentPath === "/") {
    return `/${childName}`;
  }
  return `${parentPath}/${childName}`;
}
