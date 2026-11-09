import {
  IMeasuringPoint,
  IPointLocation,
} from "../../../shared/js/images/types";
import { getCSRFToken } from "./utils";

interface IMeasuringPointUpdate {
  comments?: string;
  object_group?: number | null;
}

interface IMeasuringPointCreate extends IMeasuringPointUpdate {
  name: string;
}

interface IMeasurePointResponse {
  id: number;
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
  runId: number,
): Promise<IMeasuringPoint[]> {
  const response = await fetch(`/api/lab/runs/${runId}/measuring-points`, {
    method: "GET",
  });
  if (!response.ok) {
    throw new Error(`Failed to list measuring points for run ${runId}`);
  }
  const points = (await response.json()) as IMeasurePointResponse[];
  return points.map(parseMeasuringPointResponse);
}

export async function createMeasuringPoint(
  runId: number,
  body: IMeasuringPointCreate,
): Promise<IMeasuringPoint> {
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");
  headers.set("Content-Type", "application/json");

  const response = await fetch(`/api/lab/runs/${runId}/measuring-points`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Failed to create measuring point ${body.name}`);
  }
  return parseMeasuringPointResponse(
    (await response.json()) as IMeasurePointResponse,
  );
}

export function updateMeasuringPointObjectId(
  runId: number,
  pointId: number,
  objectGroupId: number | null,
) {
  return updateMeasuringPoint(runId, pointId, {
    object_group: objectGroupId,
  });
}

export function updateMeasuringPointComments(
  runId: number,
  pointId: number,
  comments: string,
) {
  return updateMeasuringPoint(runId, pointId, {
    comments: comments,
  });
}

async function updateMeasuringPoint(
  runId: number,
  pointId: number,
  body: IMeasuringPointUpdate,
) {
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");
  headers.set("Content-Type", "application/json");

  const response = await fetch(
    `/api/lab/runs/${runId}/measuring-points/${pointId}`,
    {
      method: "PATCH",
      headers,
      body: JSON.stringify(body),
    },
  );
  if (!response.ok) {
    throw new Error(`Failed to update measuring point ${pointId}`);
  }
}

function parseMeasuringPointResponse({
  id,
  name,
  object_group,
  comments,
  image,
}: IMeasurePointResponse): IMeasuringPoint {
  return {
    id,
    name,
    objectGroupId: object_group,
    comments,
    image: image && {
      id: image.id,
      pointLocation: image.point_location,
      runObjectGroupImage: image.run_object_group_image,
    },
  };
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
  pointId: number,
  runObjectImageId: number,
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
      `An error occurred while ${action} measuring poitn image. Response: ${response}`,
    );
  }

  const image = (await response.json()) as IAddMeasuringPointImageResponse;
  return {
    id: image.id,
    pointLocation: image.point_location,
    runObjectImageId: image.run_object_group_image,
  };
}

export async function deleteMeasuringPointImage(pointId: number) {
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");

  await fetch(`/api/lab/measuring-points/${pointId}/image`, {
    method: "DELETE",
    headers,
  });
}
