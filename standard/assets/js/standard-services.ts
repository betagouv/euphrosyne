import { getCSRFToken } from "../../../lab/assets/js/utils";
import {
  IMeasuringPointStandard,
  IStandard,
  RunMeasuringPointStandards,
} from "./IStandard";

interface IMeasuringPointStandardResponse {
  id: number;
  standard: { label: string };
}

interface IRunMeasuringPointStandardResponse {
  id: number;
  measuring_point: number;
  standard: { label: string };
}

export async function listStandards(): Promise<IStandard[]> {
  const response = await fetch(`/api/standard/standards`, {
    method: "GET",
  });
  if (response.ok) {
    return (await response.json()) as IStandard[];
  }
  throw new Error("Failed to fetch standards");
}

export async function addOrUpdateStandardToMeasuringPoint(
  standard: string,
  pointId: number,
  create: boolean = true,
): Promise<IMeasuringPointStandard> {
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");
  headers.set("Content-Type", "application/json");
  const response = await fetch(
    `/api/standard/measuring-points/${pointId}/standard`,
    {
      method: create ? "POST" : "PATCH",
      headers,
      body: JSON.stringify({ standard: { label: standard } }),
    },
  );
  if (!response.ok) {
    throw new Error(
      `Failed to add standard ${standard} to measuring point ${pointId}`,
    );
  }
  return parseMeasuringPointStandardData(
    (await response.json()) as IMeasuringPointStandardResponse,
  );
}

export async function listRunMeasuringPointsStandard(
  runId: number,
): Promise<RunMeasuringPointStandards> {
  const response = await fetch(`/api/standard/runs/${runId}`, {
    method: "GET",
  });
  if (response.ok) {
    const data =
      (await response.json()) as IRunMeasuringPointStandardResponse[];
    return data.reduce((acc, item) => {
      acc[item.measuring_point] = {
        standard: item.standard,
        id: item.id,
      };
      return acc;
    }, {} as RunMeasuringPointStandards);
  }
  throw new Error("Failed to fetch measuring points");
}

export async function retrieveMeasuringPointStandard(
  pointId: number,
): Promise<IMeasuringPointStandard | null> {
  const response = await fetch(
    `/api/standard/measuring-points/${pointId}/standard`,
    {
      method: "GET",
    },
  );
  if (response.ok) {
    return parseMeasuringPointStandardData(
      (await response.json()) as IMeasuringPointStandardResponse,
    );
  } else if (response.status === 404) {
    return null;
  }
  throw new Error(`Failed to retrieve standard for measuring point ${pointId}`);
}

export async function deleteMeasuringPointStandard(
  pointId: number,
): Promise<void> {
  const headers: HeadersInit = new Headers();
  headers.set("X-CSRFToken", getCSRFToken() || "");
  const response = await fetch(
    `/api/standard/measuring-points/${pointId}/standard`,
    {
      method: "DELETE",
      headers,
    },
  );
  if (response.ok) {
    return;
  }
  throw new Error(`Failed to retrieve standard for measuring point ${pointId}`);
}

function parseMeasuringPointStandardData(
  data: IMeasuringPointStandardResponse,
) {
  return {
    id: data.id,
    standard: data.standard,
  };
}
