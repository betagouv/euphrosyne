import { IMeasuringPoint } from "../../../lab_notebook/assets/js/IMeasuringPoint";
import { getCSRFToken } from "./utils";

interface IMeasuringPointUpdate {
  comments?: string;
  object_group?: string;
}

interface IMeasuringPointCreate extends IMeasuringPointUpdate {
  name: string;
}

interface IMeasurePointResponse {
  id: string;
  name: string;
  comments: string | null;
  object_group: number | null;
}

export async function listMeasuringPoints(
  runId: string,
): Promise<IMeasuringPoint[]> {
  const response = await fetch(`/api/lab/runs/${runId}/measuring-points`, {
    method: "GET",
  });
  const points = (await response.json()) as IMeasurePointResponse[];
  return points.map(({ id, name, object_group, comments }) => ({
    id,
    name,
    objectGroupId: object_group?.toString() || null,
    comments,
  }));
}

export async function createMeasuringPoint(
  runId: string,
  body: IMeasuringPointCreate,
) {
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");
  headers.set("Content-Type", "application/json");

  await fetch(`/api/lab/runs/${runId}/measuring-points`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
}

export function updateMeasuringPointObjectId(
  runId: string,
  pointId: string,
  objectGroupId: string,
) {
  return updateMeasuringPoint(runId, pointId, {
    object_group: objectGroupId,
  });
}

export function updateMeasuringPointComments(
  runId: string,
  pointId: string,
  comments: string,
) {
  return updateMeasuringPoint(runId, pointId, {
    comments: comments,
  });
}

async function updateMeasuringPoint(
  runId: string,
  pointId: string,
  body: IMeasuringPointUpdate,
) {
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");
  headers.set("Content-Type", "application/json");

  await fetch(`/api/lab/runs/${runId}/measuring-points/${pointId}`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(body),
  });
}
