import { IPointLocation } from "../../../lab_notebook/assets/js/IImagePointLocation";
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
  image?: {
    id: number;
    point_location: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
    run_object_group_image: {
      id: number;
      path: string;
      transform: {
        x: number;
        y: number;
        width: number;
        height: number;
        rotate: number;
        scaleX: number;
        scaleY: number;
      };
    };
  };
}

export async function listMeasuringPoints(
  runId: string,
): Promise<IMeasuringPoint[]> {
  const response = await fetch(`/api/lab/runs/${runId}/measuring-points`, {
    method: "GET",
  });
  const points = (await response.json()) as IMeasurePointResponse[];
  return points.map(({ id, name, object_group, comments, image }) => ({
    id,
    name,
    objectGroupId: object_group?.toString() || null,
    comments,
    image: image && {
      id: image.id.toString(),
      pointLocation: image.point_location,
      runObjectGroupImage: {
        ...image.run_object_group_image,
        id: image.run_object_group_image.id.toString(),
      },
    },
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

interface IAddMeasuringPointImageResponse {
  id: number;
  point_location: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  run_object_group_image: number;
}

export async function addMeasuringPointImage(
  pointId: string,
  runObjectImageId: string,
  location: IPointLocation,
  create: boolean = true, // whether object should be a creation (POST) or a modification (PATCH)
) {
  const body = {
    point_location: location,
    run_object_group_image: runObjectImageId,
  };
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");
  headers.set("Content-Type", "application/json");

  const response = await fetch(`/api/lab/measuring-points/${pointId}/image`, {
    method: create ? "POST" : "PATCH",
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const action = create ? "creating" : "modifying";
    throw new Error(
      `An error occured while ${action} measuring poitn image. Response: ${response}`,
    );
  }

  const image = (await response.json()) as IAddMeasuringPointImageResponse;
  return {
    id: image.id.toString(),
    pointLocation: image.point_location,
    runObjectImageId: image.run_object_group_image.toString(),
  };
}

export async function deleteMeasuringPointImage(pointId: string) {
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");

  await fetch(`/api/lab/measuring-points/${pointId}/image`, {
    method: "DELETE",
    headers,
  });
}
