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
  createPreviewObjectGroup,
  createPreviewPoint,
  findAvailableObjectGroupByLabel,
  findPointByCandidate,
  findRunObjectGroupById,
  findRunObjectGroupByLabel,
  findStandardByReferenceLabel,
  standardLabelsMatch,
  upsertMeasuringPoint,
} from "./shared";
import type {
  HDF5NotebookGenerationPreview,
  HDF5NotebookGenerationPreviewWarning,
  PreviewNotebookGenerationFromHDF5Options,
} from "./types";
import type { HDF5NotebookGenerationCandidate } from "../types";

interface GenerationSnapshot {
  points: IMeasuringPoint[];
  runObjectGroups: RunObjectGroup[];
  runStandards: RunMeasuringPointStandards;
}

interface PreviewState {
  preview: HDF5NotebookGenerationPreview;
  snapshot: GenerationSnapshot;
  nextPointId: number;
  nextObjectId: number;
}

export function previewNotebookGenerationFromHDF5({
  candidates,
  measuringPoints,
  runObjectGroups,
  availableObjectGroups,
  standards,
  runMeasuringPointStandards,
  skippedCandidateCount = 0,
}: PreviewNotebookGenerationFromHDF5Options): HDF5NotebookGenerationPreview {
  const initialState: PreviewState = {
    preview: createNotebookGenerationPreview(candidates, skippedCandidateCount),
    snapshot: {
      points: [...measuringPoints],
      runObjectGroups: [...runObjectGroups],
      runStandards: { ...runMeasuringPointStandards },
    },
    nextPointId: 0,
    nextObjectId: 0,
  };

  return candidates.reduce(
    (state, candidate) =>
      previewCandidate({
        state,
        candidate,
        availableObjectGroups,
        standards,
      }),
    initialState,
  ).preview;
}

function createNotebookGenerationPreview(
  candidates: HDF5NotebookGenerationCandidate[],
  skippedCandidateCount: number,
): HDF5NotebookGenerationPreview {
  return {
    metadata: {
      detectedPoints: candidates.length,
      objectAnalysisPoints: candidates.filter(
        ({ analysisType }) => analysisType === "object",
      ).length,
      standardAnalysisPoints: candidates.filter(
        ({ analysisType }) => analysisType === "standard",
      ).length,
      skippedEntries: skippedCandidateCount,
    },
    changes: {
      pointsToCreate: 0,
      existingPointsToReuse: 0,
      commentsToFill: 0,
      commentsPreserved: 0,
      objectsToCreate: 0,
      objectsReusedOrLinked: 0,
      standardsToAttachOrReuse: 0,
      missingStandards: 0,
    },
    warnings: [],
  };
}

function previewCandidate({
  state,
  candidate,
  availableObjectGroups,
  standards,
}: {
  state: PreviewState;
  candidate: HDF5NotebookGenerationCandidate;
  availableObjectGroups: ObjectGroup[];
  standards: IStandard[];
}): PreviewState {
  let nextState = state;
  let point = findPointByCandidate(nextState.snapshot.points, candidate);

  if (point) {
    nextState = incrementPreviewChange(nextState, "existingPointsToReuse");
  } else {
    const nextPointId = nextState.nextPointId + 1;
    point = createPreviewPoint(candidate, nextPointId);
    nextState = incrementPreviewChange(
      {
        ...nextState,
        nextPointId,
        snapshot: {
          ...nextState.snapshot,
          points: [...nextState.snapshot.points, point],
        },
      },
      "pointsToCreate",
    );
  }

  const commentResult = previewCandidateComment(nextState, candidate, point);
  nextState = commentResult.state;
  point = commentResult.point;

  if (candidate.analysisType === "object") {
    return previewObjectCandidate({
      state: nextState,
      candidate,
      point,
      availableObjectGroups,
    });
  }

  return previewStandardCandidate({
    state: nextState,
    candidate,
    point,
    standards,
  });
}

function previewCandidateComment(
  state: PreviewState,
  candidate: HDF5NotebookGenerationCandidate,
  point: IMeasuringPoint,
): { state: PreviewState; point: IMeasuringPoint } {
  if (!candidate.comment) {
    return { state, point };
  }

  if (!point.comments?.trim()) {
    const updatedPoint = { ...point, comments: candidate.comment };
    return {
      state: incrementPreviewChange(
        updateSnapshotPoint(state, updatedPoint),
        "commentsToFill",
      ),
      point: updatedPoint,
    };
  }

  if (point.comments.trim() !== candidate.comment) {
    return {
      state: addPreviewWarning(
        incrementPreviewChange(state, "commentsPreserved"),
        {
          code: "different-comment",
          pointName: candidate.pointName,
        },
      ),
      point,
    };
  }

  return { state, point };
}

function previewObjectCandidate({
  state,
  candidate,
  point,
  availableObjectGroups,
}: {
  state: PreviewState;
  candidate: HDF5NotebookGenerationCandidate;
  point: IMeasuringPoint;
  availableObjectGroups: ObjectGroup[];
}): PreviewState {
  if (!candidate.referenceLabel) {
    return addPreviewWarning(state, {
      code: "missing-object-reference",
      pointName: candidate.pointName,
    });
  }

  if (state.snapshot.runStandards[point.id]) {
    return addPreviewWarning(state, {
      code: "point-linked-to-standard",
      pointName: candidate.pointName,
    });
  }

  const linkedObjectGroup = point.objectGroupId
    ? findRunObjectGroupById(
        state.snapshot.runObjectGroups,
        point.objectGroupId,
      )
    : null;
  if (linkedObjectGroup) {
    if (linkedObjectGroup.objectGroup.label === candidate.referenceLabel) {
      return incrementPreviewChange(state, "objectsReusedOrLinked");
    }
    return addPreviewWarning(state, {
      code: "different-object",
      pointName: candidate.pointName,
      label: candidate.referenceLabel,
    });
  }

  const runObjectGroup = findRunObjectGroupByLabel(
    state.snapshot.runObjectGroups,
    candidate.referenceLabel,
  );
  if (runObjectGroup) {
    return linkPreviewObjectGroup(
      incrementPreviewChange(state, "objectsReusedOrLinked"),
      point,
      runObjectGroup.objectGroup,
    );
  }

  const availableObjectGroup = findAvailableObjectGroupByLabel(
    availableObjectGroups,
    candidate.referenceLabel,
  );
  if (availableObjectGroup) {
    return linkPreviewObjectGroup(
      incrementPreviewChange(
        addPreviewRunObjectGroup(state, availableObjectGroup),
        "objectsReusedOrLinked",
      ),
      point,
      availableObjectGroup,
    );
  }

  const nextObjectId = state.nextObjectId + 1;
  const objectGroup = createPreviewObjectGroup(
    candidate.referenceLabel,
    nextObjectId,
  );
  return linkPreviewObjectGroup(
    incrementPreviewChange(
      addPreviewRunObjectGroup({ ...state, nextObjectId }, objectGroup),
      "objectsToCreate",
    ),
    point,
    objectGroup,
  );
}

function previewStandardCandidate({
  state,
  candidate,
  point,
  standards,
}: {
  state: PreviewState;
  candidate: HDF5NotebookGenerationCandidate;
  point: IMeasuringPoint;
  standards: IStandard[];
}): PreviewState {
  if (!candidate.referenceLabel) {
    return addPreviewWarning(state, {
      code: "missing-standard-reference",
      pointName: candidate.pointName,
    });
  }

  if (point.objectGroupId) {
    return addPreviewWarning(state, {
      code: "point-linked-to-object",
      pointName: candidate.pointName,
    });
  }

  const existingStandard = state.snapshot.runStandards[point.id];
  if (existingStandard) {
    if (
      standardLabelsMatch(
        existingStandard.standard.label,
        candidate.referenceLabel,
      )
    ) {
      return incrementPreviewChange(state, "standardsToAttachOrReuse");
    }
    return addPreviewWarning(state, {
      code: "different-standard",
      pointName: candidate.pointName,
      label: candidate.referenceLabel,
    });
  }

  const matchingStandard = findStandardByReferenceLabel(
    standards,
    candidate.referenceLabel,
  );
  if (!matchingStandard) {
    return addPreviewWarning(
      incrementPreviewChange(state, "missingStandards"),
      {
        code: "missing-standard",
        pointName: candidate.pointName,
        label: candidate.referenceLabel,
      },
    );
  }

  return incrementPreviewChange(
    {
      ...state,
      snapshot: {
        ...state.snapshot,
        runStandards: {
          ...state.snapshot.runStandards,
          [point.id]: {
            id: `__preview_standard_${point.id}`,
            standard: matchingStandard,
          },
        },
      },
    },
    "standardsToAttachOrReuse",
  );
}

function linkPreviewObjectGroup(
  state: PreviewState,
  point: IMeasuringPoint,
  objectGroup: ObjectGroup,
): PreviewState {
  return updateSnapshotPoint(state, {
    ...point,
    objectGroupId: objectGroup.id,
  });
}

function addPreviewRunObjectGroup(
  state: PreviewState,
  objectGroup: ObjectGroup,
): PreviewState {
  return {
    ...state,
    snapshot: {
      ...state.snapshot,
      runObjectGroups: [
        ...state.snapshot.runObjectGroups,
        { id: "", objectGroup },
      ],
    },
  };
}

function updateSnapshotPoint(
  state: PreviewState,
  point: IMeasuringPoint,
): PreviewState {
  return {
    ...state,
    snapshot: {
      ...state.snapshot,
      points: upsertMeasuringPoint(state.snapshot.points, point),
    },
  };
}

function incrementPreviewChange(
  state: PreviewState,
  change: keyof HDF5NotebookGenerationPreview["changes"],
): PreviewState {
  return {
    ...state,
    preview: {
      ...state.preview,
      changes: {
        ...state.preview.changes,
        [change]: state.preview.changes[change] + 1,
      },
    },
  };
}

function addPreviewWarning(
  state: PreviewState,
  warning: HDF5NotebookGenerationPreviewWarning,
): PreviewState {
  return {
    ...state,
    preview: {
      ...state.preview,
      warnings: [...state.preview.warnings, warning],
    },
  };
}
