import type {
  RunObjectGroup,
  ObjectGroup,
} from "../../../../../lab/objects/assets/js/types";
import type { IMeasuringPoint } from "../../../../../shared/js/images/types";
import type { IStandard } from "../../../../../standard/assets/js/IStandard";
import { normalizeMeasuringPointName } from "../notebook-hdf5";
import type { HDF5NotebookGenerationCandidate } from "../types";
import type { HDF5NotebookGenerationProgress } from "./types";

/**
 * Preview entities do not exist in the database yet: they get negative ids so
 * they can never collide with a real primary key.
 */
export function previewId(id: number) {
  return -id;
}

/**
 * Placeholder for a run object group created during generation: its primary
 * key is not returned by the API and is not needed afterwards.
 */
export const UNKNOWN_RUN_OBJECT_GROUP_ID = 0;

export function createPreviewPoint(
  candidate: HDF5NotebookGenerationCandidate,
  id: number,
): IMeasuringPoint {
  return {
    id: previewId(id),
    name: candidate.pointName,
    objectGroupId: null,
    comments: null,
  };
}

export function createPreviewObjectGroup(
  label: string,
  id: number,
): ObjectGroup {
  return {
    id: previewId(id),
    label,
    objectCount: 1,
    dating: "",
    materials: [],
    externalReference: null,
  };
}

export function findPointByCandidate(
  points: IMeasuringPoint[],
  candidate: HDF5NotebookGenerationCandidate,
) {
  return points.find(
    (point) => normalizeMeasuringPointName(point.name) === candidate.pointKey,
  );
}

export function findRunObjectGroupById(
  runObjectGroups: RunObjectGroup[],
  objectGroupId: number,
) {
  return runObjectGroups.find(
    ({ objectGroup }) => objectGroup.id === objectGroupId,
  );
}

export function findRunObjectGroupByLabel(
  runObjectGroups: RunObjectGroup[],
  label: string,
) {
  return runObjectGroups.find(({ objectGroup }) => objectGroup.label === label);
}

export function findAvailableObjectGroupByLabel(
  availableObjectGroups: ObjectGroup[],
  label: string,
) {
  return availableObjectGroups.find(
    (objectGroup) => objectGroup.label === label,
  );
}

export function findStandardByReferenceLabel(
  standards: IStandard[],
  label: string,
) {
  return standards.find((standard) =>
    standardLabelsMatch(standard.label, label),
  );
}

export function addProgressError(
  progress: HDF5NotebookGenerationProgress,
  message: string,
  ...args: string[]
) {
  progress.errors.push(window.interpolate(window.gettext(message), args));
}

export function standardLabelsMatch(left: string, right: string) {
  return normalizeStandardLabel(left) === normalizeStandardLabel(right);
}

export function upsertMeasuringPoint(
  points: IMeasuringPoint[],
  updatedPoint: IMeasuringPoint,
) {
  if (points.some(({ id }) => id === updatedPoint.id)) {
    return points.map((point) =>
      point.id === updatedPoint.id ? updatedPoint : point,
    );
  }
  return [...points, updatedPoint];
}

function normalizeStandardLabel(label: string) {
  return label
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}
