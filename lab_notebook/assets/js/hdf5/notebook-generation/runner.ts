import type {
  RunObjectGroup,
  ObjectGroup,
} from "../../../../../lab/objects/assets/js/types";
import type { IMeasuringPoint } from "../../../../../shared/js/images/types";
import type {
  IStandard,
  RunMeasuringPointStandards,
} from "../../../../../standard/assets/js/IStandard";
import {
  addProgressError,
  findAvailableObjectGroupByLabel,
  findPointByCandidate,
  findRunObjectGroupById,
  findRunObjectGroupByLabel,
  findStandardByReferenceLabel,
  standardLabelsMatch,
  upsertMeasuringPoint,
} from "./shared";
import type {
  GenerateNotebookFromHDF5Options,
  HDF5NotebookGenerationProgress,
  HDF5NotebookGenerationResult,
  HDF5NotebookGenerationServices,
} from "./types";
import type { HDF5NotebookGenerationCandidate } from "../types";

export async function generateNotebookFromHDF5({
  runId,
  candidates,
  measuringPoints,
  runObjectGroups,
  availableObjectGroups,
  standards,
  runMeasuringPointStandards,
  services,
  onProgress,
}: GenerateNotebookFromHDF5Options): Promise<HDF5NotebookGenerationResult> {
  let pointSnapshot = [...measuringPoints];
  let runObjectGroupSnapshot = [...runObjectGroups];
  let runStandardsSnapshot = { ...runMeasuringPointStandards };

  const progress: HDF5NotebookGenerationProgress = {
    detectedPoints: candidates.length,
    processedPoints: 0,
    currentPointName: null,
    pointsCreated: 0,
    pointsUpdated: 0,
    objectsCreated: 0,
    objectsReused: 0,
    standardsReused: 0,
    errors: [],
  };

  const emitProgress = () =>
    onProgress?.({ ...progress, errors: [...progress.errors] });
  emitProgress();

  for (const candidate of candidates) {
    progress.currentPointName = candidate.pointName;
    emitProgress();

    const pointResult = await getOrCreateMeasuringPoint({
      runId,
      candidate,
      points: pointSnapshot,
      services,
      progress,
    });
    let completedExistingPoint = false;
    let point = pointResult.point;
    pointSnapshot = upsertMeasuringPoint(pointSnapshot, point);

    if (candidate.comment) {
      if (!point.comments?.trim()) {
        await services.updateMeasuringPointComments(
          runId,
          point.id,
          candidate.comment,
        );
        point = { ...point, comments: candidate.comment };
        pointSnapshot = upsertMeasuringPoint(pointSnapshot, point);
        completedExistingPoint ||= !pointResult.created;
      } else if (point.comments.trim() !== candidate.comment) {
        addProgressError(
          progress,
          "Point %s already has a different comment; it was not overwritten.",
          candidate.pointName,
        );
      }
    }

    if (candidate.analysisType === "object") {
      const result = await completeObjectAnalysis({
        runId,
        candidate,
        point,
        runObjectGroups: runObjectGroupSnapshot,
        availableObjectGroups,
        runStandards: runStandardsSnapshot,
        services,
        progress,
      });
      point = result.point;
      pointSnapshot = upsertMeasuringPoint(pointSnapshot, point);
      runObjectGroupSnapshot = result.runObjectGroups;
      if (result.changed) {
        completedExistingPoint ||= !pointResult.created;
      }
    } else {
      const result = await completeStandardAnalysis({
        candidate,
        point,
        standards,
        runStandards: runStandardsSnapshot,
        services,
        progress,
      });
      runStandardsSnapshot = result.runStandards;
      if (result.changed) {
        completedExistingPoint ||= !pointResult.created;
      }
    }

    if (completedExistingPoint) {
      progress.pointsUpdated += 1;
    }

    progress.processedPoints += 1;
    emitProgress();
  }

  progress.currentPointName = null;
  emitProgress();

  return {
    measuringPoints: pointSnapshot,
    runObjectGroups: runObjectGroupSnapshot,
    runMeasuringPointStandards: runStandardsSnapshot,
    progress,
  };
}

async function getOrCreateMeasuringPoint({
  runId,
  candidate,
  points,
  services,
  progress,
}: {
  runId: string;
  candidate: HDF5NotebookGenerationCandidate;
  points: IMeasuringPoint[];
  services: HDF5NotebookGenerationServices;
  progress: HDF5NotebookGenerationProgress;
}) {
  const existingPoint = findPointByCandidate(points, candidate);
  if (existingPoint) {
    return { point: existingPoint, created: false };
  }

  const point = await services.createMeasuringPoint(runId, {
    name: candidate.pointName,
  });
  progress.pointsCreated += 1;
  return { point, created: true };
}

async function completeObjectAnalysis({
  runId,
  candidate,
  point,
  runObjectGroups,
  availableObjectGroups,
  runStandards,
  services,
  progress,
}: {
  runId: string;
  candidate: HDF5NotebookGenerationCandidate;
  point: IMeasuringPoint;
  runObjectGroups: RunObjectGroup[];
  availableObjectGroups: ObjectGroup[];
  runStandards: RunMeasuringPointStandards;
  services: HDF5NotebookGenerationServices;
  progress: HDF5NotebookGenerationProgress;
}): Promise<{
  point: IMeasuringPoint;
  runObjectGroups: RunObjectGroup[];
  changed: boolean;
}> {
  if (!candidate.referenceLabel) {
    addProgressError(
      progress,
      "Point %s has no object reference in HDF5 metadata.",
      candidate.pointName,
    );
    return { point, runObjectGroups, changed: false };
  }

  if (runStandards[point.id]) {
    addProgressError(
      progress,
      "Point %s is already linked to a standard; it was not changed to an object analysis.",
      candidate.pointName,
    );
    return { point, runObjectGroups, changed: false };
  }

  const linkedObjectGroup = point.objectGroupId
    ? findRunObjectGroupById(runObjectGroups, point.objectGroupId)
    : null;
  if (linkedObjectGroup) {
    if (linkedObjectGroup.objectGroup.label === candidate.referenceLabel) {
      progress.objectsReused += 1;
    } else {
      addProgressError(
        progress,
        "Point %s is already linked to a different object; it was not overwritten.",
        candidate.pointName,
      );
    }
    return { point, runObjectGroups, changed: false };
  }

  const objectResolution = await resolveObjectGroup({
    runId,
    referenceLabel: candidate.referenceLabel,
    runObjectGroups,
    availableObjectGroups,
    services,
    progress,
  });

  await services.updateMeasuringPointObjectId(
    runId,
    point.id,
    objectResolution.objectGroup.id,
  );

  return {
    point: { ...point, objectGroupId: objectResolution.objectGroup.id },
    runObjectGroups: objectResolution.runObjectGroups,
    changed: true,
  };
}

async function resolveObjectGroup({
  runId,
  referenceLabel,
  runObjectGroups,
  availableObjectGroups,
  services,
  progress,
}: {
  runId: string;
  referenceLabel: string;
  runObjectGroups: RunObjectGroup[];
  availableObjectGroups: ObjectGroup[];
  services: HDF5NotebookGenerationServices;
  progress: HDF5NotebookGenerationProgress;
}): Promise<{ objectGroup: ObjectGroup; runObjectGroups: RunObjectGroup[] }> {
  const runObjectGroup = findRunObjectGroupByLabel(
    runObjectGroups,
    referenceLabel,
  );
  if (runObjectGroup) {
    progress.objectsReused += 1;
    return { objectGroup: runObjectGroup.objectGroup, runObjectGroups };
  }

  const availableObjectGroup = findAvailableObjectGroupByLabel(
    availableObjectGroups,
    referenceLabel,
  );
  if (availableObjectGroup) {
    await services.addObjectGroupToRun(runId, availableObjectGroup.id);
    progress.objectsReused += 1;
    return {
      objectGroup: availableObjectGroup,
      runObjectGroups: [
        ...runObjectGroups,
        { id: "", objectGroup: availableObjectGroup },
      ],
    };
  }

  const createdObjectGroup = await services.createObjectGroup({
    label: referenceLabel,
  });
  await services.addObjectGroupToRun(runId, createdObjectGroup.id.toString());
  progress.objectsCreated += 1;
  const objectGroup: ObjectGroup = {
    id: createdObjectGroup.id.toString(),
    label: createdObjectGroup.label,
    objectCount: 1,
    dating: "",
    materials: [],
    externalReference: null,
  };
  return {
    objectGroup,
    runObjectGroups: [...runObjectGroups, { id: "", objectGroup }],
  };
}

async function completeStandardAnalysis({
  candidate,
  point,
  standards,
  runStandards,
  services,
  progress,
}: {
  candidate: HDF5NotebookGenerationCandidate;
  point: IMeasuringPoint;
  standards: IStandard[];
  runStandards: RunMeasuringPointStandards;
  services: HDF5NotebookGenerationServices;
  progress: HDF5NotebookGenerationProgress;
}): Promise<{ runStandards: RunMeasuringPointStandards; changed: boolean }> {
  if (!candidate.referenceLabel) {
    addProgressError(
      progress,
      "Point %s has no standard reference in HDF5 metadata.",
      candidate.pointName,
    );
    return { runStandards, changed: false };
  }
  const referenceLabel = candidate.referenceLabel;

  if (point.objectGroupId) {
    addProgressError(
      progress,
      "Point %s is already linked to an object; it was not changed to a standard analysis.",
      candidate.pointName,
    );
    return { runStandards, changed: false };
  }

  const existingStandard = runStandards[point.id];
  if (existingStandard) {
    if (standardLabelsMatch(existingStandard.standard.label, referenceLabel)) {
      progress.standardsReused += 1;
    } else {
      addProgressError(
        progress,
        "Point %s is already linked to a different standard; it was not overwritten.",
        candidate.pointName,
      );
    }
    return { runStandards, changed: false };
  }

  const matchingStandard = findStandardByReferenceLabel(
    standards,
    referenceLabel,
  );

  if (!matchingStandard) {
    addProgressError(
      progress,
      "Standard %s does not exist yet; create it and retry generation.",
      referenceLabel,
    );
    return { runStandards, changed: false };
  }

  const measuringPointStandard =
    await services.addOrUpdateStandardToMeasuringPoint(
      matchingStandard.label,
      point.id,
      true,
    );
  progress.standardsReused += 1;

  return {
    runStandards: {
      ...runStandards,
      [point.id]: measuringPointStandard,
    },
    changed: true,
  };
}
