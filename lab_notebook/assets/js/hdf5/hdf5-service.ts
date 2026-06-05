import { HDF5Attribute, HDF5Entity, HDF5Type, ToolsFetch } from "./types";

export const HDF5_DATA_TRANSFER_PROGRESS_EVENT = "hdf5:data-transfer-progress";

export interface HDF5DataTransferProgressDetail {
  file: string | null;
  path: string | null;
  loaded: number;
  total: number | null;
  done: boolean;
}

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
  return parseHDF5Entity(await response.json(), path);
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

function parseHDF5Entity(value: unknown, path: string): HDF5Entity {
  function getEntityPath(parentPath: string, childName: string): string {
    if (parentPath === "/") {
      return `/${childName}`;
    }
    return `${parentPath}/${childName}`;
  }

  const entity = getRecord(value, "HDF5 entity");
  const name = getStringField(entity, "name", "HDF5 entity");
  const kind = getStringField(entity, "kind", `HDF5 entity ${name}`);
  const attributes = getAttributeArray(
    entity.attributes,
    `HDF5 entity ${name}`,
  );

  if (kind === "group") {
    const children = Array.isArray(entity.children)
      ? entity.children.map((child) => {
          const childRecord = getRecord(child, `HDF5 child of ${name}`);
          const childName = getStringField(
            childRecord,
            "name",
            `HDF5 child of ${name}`,
          );
          return parseHDF5Entity(child, getEntityPath(path, childName));
        })
      : [];

    return {
      name,
      kind,
      path,
      attributes,
      children,
    };
  }

  if (kind === "dataset") {
    return {
      name,
      kind,
      path,
      attributes,
      shape: getNumberArray(entity.shape, `HDF5 dataset ${name} shape`),
      type: getHDF5Type(entity.type, `HDF5 dataset ${name} type`),
    };
  }

  throw new Error(`Unexpected HDF5 entity kind "${kind}" for ${name}.`);
}

function getAttributeArray(value: unknown, context: string): HDF5Attribute[] {
  if (!Array.isArray(value)) {
    throw new Error(`${context} attributes must be an array.`);
  }

  return value.map((attribute, index) => {
    const record = getRecord(attribute, `${context} attribute ${index}`);
    return {
      name: getStringField(record, "name", `${context} attribute ${index}`),
      shape: getNumberArray(
        record.shape,
        `${context} attribute ${index} shape`,
      ),
      type: getHDF5Type(record.type, `${context} attribute ${index} type`),
      value: record.value,
    };
  });
}

function getHDF5Type(value: unknown, context: string): HDF5Type {
  const record = getRecord(value, context);
  const type: HDF5Type = {
    class: getNumberField(record, "class", context),
    dtype: getStringField(record, "dtype", context),
    size: getNumberField(record, "size", context),
  };

  if (record.sign !== undefined) {
    type.sign = getNumberField(record, "sign", context);
  }
  if (record.order !== undefined) {
    type.order = getNumberField(record, "order", context);
  }

  return type;
}

function getRecord(value: unknown, context: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${context} must be an object.`);
  }
  return value as Record<string, unknown>;
}

function getStringField(
  record: Record<string, unknown>,
  field: string,
  context: string,
): string {
  const value = record[field];
  if (typeof value !== "string") {
    throw new Error(`${context} ${field} must be a string.`);
  }
  return value;
}

function getNumberField(
  record: Record<string, unknown>,
  field: string,
  context: string,
): number {
  const value = record[field];
  if (typeof value !== "number") {
    throw new Error(`${context} ${field} must be a number.`);
  }
  return value;
}

function getNumberArray(value: unknown, context: string): number[] {
  if (
    !Array.isArray(value) ||
    !value.every((item) => typeof item === "number")
  ) {
    throw new Error(`${context} must be a number array.`);
  }
  return value;
}
