import type {
  RunObjectGroup,
  ObjectGroup,
} from "../../../../../lab/objects/assets/js/types";
import type { ToolsFetch } from "../../../../../shared/js/euphrosyne-tools-client";
import type { IMeasuringPoint } from "../../../../../shared/js/images/types";
import type {
  IMeasuringPointStandard,
  IStandard,
  RunMeasuringPointStandards,
} from "../../../../../standard/assets/js/IStandard";
import type {
  HDF5NotebookGenerationCandidate,
  HDF5NotebookGenerationSkippedCandidate,
} from "../types";

export interface HDF5NotebookGenerationProgress {
  detectedPoints: number;
  processedPoints: number;
  currentPointName: string | null;
  pointsCreated: number;
  pointsUpdated: number;
  objectsCreated: number;
  objectsReused: number;
  standardsReused: number;
  errors: string[];
}

export interface HDF5NotebookGenerationResult {
  measuringPoints: IMeasuringPoint[];
  runObjectGroups: RunObjectGroup[];
  runMeasuringPointStandards: RunMeasuringPointStandards;
  progress: HDF5NotebookGenerationProgress;
}

export interface HDF5NotebookGenerationDiscoveryResult {
  candidates: HDF5NotebookGenerationCandidate[];
  skippedCandidates: HDF5NotebookGenerationSkippedCandidate[];
}

export interface DiscoverHDF5NotebookGenerationCandidatesOptions {
  projectSlug: string;
  runName: string;
  fetchFn: ToolsFetch;
}

export interface HDF5NotebookGenerationServices {
  createMeasuringPoint: (
    runId: string,
    body: { name: string; comments?: string; object_group?: string },
  ) => Promise<IMeasuringPoint>;
  updateMeasuringPointComments: (
    runId: string,
    pointId: string,
    comments: string,
  ) => Promise<void>;
  updateMeasuringPointObjectId: (
    runId: string,
    pointId: string,
    objectGroupId: string,
  ) => Promise<void>;
  createObjectGroup: (body: { label: string }) => Promise<{
    id: number;
    label: string;
  }>;
  addObjectGroupToRun: (
    runId: string,
    objectGroupId: string,
  ) => Promise<unknown>;
  addOrUpdateStandardToMeasuringPoint: (
    standard: string,
    pointId: string,
    create?: boolean,
  ) => Promise<IMeasuringPointStandard>;
}

export interface GenerateNotebookFromHDF5Options {
  runId: string;
  candidates: HDF5NotebookGenerationCandidate[];
  measuringPoints: IMeasuringPoint[];
  runObjectGroups: RunObjectGroup[];
  availableObjectGroups: ObjectGroup[];
  standards: IStandard[];
  runMeasuringPointStandards: RunMeasuringPointStandards;
  services: HDF5NotebookGenerationServices;
  onProgress?: (progress: HDF5NotebookGenerationProgress) => void;
}

export type HDF5NotebookGenerationPreviewWarningCode =
  | "missing-object-reference"
  | "point-linked-to-standard"
  | "different-object"
  | "different-comment"
  | "missing-standard-reference"
  | "point-linked-to-object"
  | "different-standard"
  | "missing-standard";

export interface HDF5NotebookGenerationPreviewWarning {
  code: HDF5NotebookGenerationPreviewWarningCode;
  pointName: string;
  label?: string;
}

export interface HDF5NotebookGenerationPreview {
  metadata: {
    detectedPoints: number;
    objectAnalysisPoints: number;
    standardAnalysisPoints: number;
    skippedEntries: number;
  };
  changes: {
    pointsToCreate: number;
    existingPointsToReuse: number;
    commentsToFill: number;
    commentsPreserved: number;
    objectsToCreate: number;
    objectsReusedOrLinked: number;
    standardsToAttachOrReuse: number;
    missingStandards: number;
  };
  warnings: HDF5NotebookGenerationPreviewWarning[];
}

export interface PreviewNotebookGenerationFromHDF5Options {
  candidates: HDF5NotebookGenerationCandidate[];
  measuringPoints: IMeasuringPoint[];
  runObjectGroups: RunObjectGroup[];
  availableObjectGroups: ObjectGroup[];
  standards: IStandard[];
  runMeasuringPointStandards: RunMeasuringPointStandards;
  skippedCandidateCount?: number;
}
