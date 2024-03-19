import { getCSRFToken } from "../../../assets/js/utils";
import { RunObjectGroup, ObjectGroup } from "./types";

interface ObjectGroupResponseElement {
  id: number;
  label: string;
  object_count: number;
  dating: string;
  materials: string[];
}

interface RunObjectGroupsResponseElement {
  id: number;
  objectgroup: ObjectGroupResponseElement;
}

export async function fetchRunObjectGroups(
  runId: string,
): Promise<RunObjectGroup[]> {
  const runObjectGroups = (await (
    await fetch(`/api/lab/runs/${runId}/objectgroups`)
  ).json()) as RunObjectGroupsResponseElement[];
  return runObjectGroups.map((ro) => ({
    id: ro.id.toString(),
    objectGroup: {
      id: ro.objectgroup.id.toString(),
      label: ro.objectgroup.label,
      objectCount: ro.objectgroup.object_count,
      dating: ro.objectgroup.dating,
      materials: ro.objectgroup.materials,
    },
  }));
}

export async function fetchAvailableObjectGroups(
  runId: string,
): Promise<ObjectGroup[]> {
  const availableObjectGroups = (await (
    await fetch(`/api/lab/runs/${runId}/available-objectgroups`)
  ).json()) as ObjectGroupResponseElement[];
  return availableObjectGroups.map((objectgroup) => ({
    id: objectgroup.id.toString(),
    label: objectgroup.label,
    objectCount: objectgroup.object_count,
    dating: objectgroup.dating,
    materials: objectgroup.materials,
  }));
}

export async function addObjectGroupToRun(
  runId: string,
  objectGroupId: string,
) {
  let response;
  try {
    response = await fetch(`/api/lab/runs/${runId}/objectgroups`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken() || "",
      },
      body: JSON.stringify({ objectgroup: objectGroupId }),
    });
  } catch (error) {
    console.error("Error adding object group to run", error);
  }
  if (!response || !response.ok) {
    console.error("Error adding object group to run", response);
  }
  return response;
}

export async function deleteRunObjectGroup(runObjectGroupId: string) {
  let response;
  try {
    response = await fetch(`/api/lab/run_objectgroups/${runObjectGroupId}`, {
      method: "DELETE",
      headers: {
        "X-CSRFToken": getCSRFToken() || "",
      },
    });
  } catch (error) {
    console.error("Error deleting object group from run", error);
  }
  if (!response || !response.ok) {
    console.error("Error deleting object group from run", response);
  }
  return response;
}
