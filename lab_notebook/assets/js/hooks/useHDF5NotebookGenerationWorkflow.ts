import { useState } from "react";
import {
  createMeasuringPoint,
  listMeasuringPoints,
  updateMeasuringPointComments,
  updateMeasuringPointObjectId,
} from "../../../../lab/assets/js/measuring-point.services";
import {
  addObjectGroupToRun,
  createObjectGroup,
  fetchAvailableObjectGroups,
  fetchRunObjectGroups,
} from "../../../../lab/objects/assets/js/services";
import type {
  ObjectGroup,
  RunObjectGroup,
} from "../../../../lab/objects/assets/js/types";
import type { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import type { IMeasuringPoint } from "../../../../shared/js/images/types";
import {
  addOrUpdateStandardToMeasuringPoint,
  listRunMeasuringPointsStandard,
  listStandards,
} from "../../../../standard/assets/js/standard-services";
import type {
  IStandard,
  RunMeasuringPointStandards,
} from "../../../../standard/assets/js/IStandard";
import {
  discoverHDF5NotebookGenerationCandidates,
  generateNotebookFromHDF5,
  previewNotebookGenerationFromHDF5,
  type HDF5NotebookGenerationCandidate,
  type HDF5NotebookGenerationPreview,
  type HDF5NotebookGenerationProgress,
  type HDF5NotebookGenerationSkippedCandidate,
} from "../hdf5";

export type GenerationStatus = "idle" | "running" | "success" | "error";
export type CandidateDiscoveryStatus = "idle" | "loading" | "loaded" | "error";
export type PreflightStatus = "idle" | "loading" | "loaded" | "error";

interface HDF5NotebookGenerationPreflightData {
  measuringPoints: IMeasuringPoint[];
  runObjectGroups: RunObjectGroup[];
  availableObjectGroups: ObjectGroup[];
  standards: IStandard[];
  runMeasuringPointStandards: RunMeasuringPointStandards;
}

export function createHDF5NotebookGenerationLabels() {
  return {
    button: window.gettext("Generate notebook"),
    cancel: window.gettext("Cancel"),
    close: window.gettext("Close"),
    confirm: window.gettext("Confirm generation"),
    title: window.gettext("Generate notebook from HDF5"),
    stepCount: window.gettext("Step %s of %s"),
    nextStep: window.gettext("Next step:"),
    metadataStep: window.gettext("Prepare generation"),
    generationStep: window.gettext("Generate notebook"),
    warning: window.gettext(
      "The measurement points in this notebook can be created or completed using the HDF5 data available for this run. Existing measurement points may be updated, but duplicate points and objects will not be created. Please review the notebook after generation.",
    ),
    keepOpen: window.gettext(
      "Keep this browser tab open while generation is running.",
    ),
    started: window.gettext("Generation started."),
    success: window.gettext("Notebook generation completed."),
    error: window.gettext(
      "Notebook generation stopped. You can retry after the issue is fixed.",
    ),
    detectedPoints: window.gettext("Detected points"),
    currentPoint: window.gettext("Current point"),
    pointsCreated: window.gettext("Points created"),
    pointsUpdated: window.gettext("Points updated/completed"),
    objectsCreated: window.gettext("Objects created"),
    objectsReused: window.gettext("Objects reused"),
    standardsReused: window.gettext("Standards reused"),
    errors: window.gettext("Errors"),
    skipped: window.gettext("Skipped HDF5 entries"),
    noData: window.gettext("No usable HDF5 metadata detected yet."),
    noFiles: window.gettext("No HDF5 files detected yet."),
    loadingMetadata: window.gettext("Loading HDF5 metadata for generation..."),
    loadingPreflight: window.gettext("Loading current notebook state..."),
    detectedMetadata: window.gettext("Detected HDF5 metadata"),
    expectedChanges: window.gettext("Expected changes"),
    rulesApplied: window.gettext("Rules applied"),
    warnings: window.gettext("Warnings"),
    hdf5Points: window.gettext("HDF5 points"),
    objectPoints: window.gettext("Object analyses"),
    standardPoints: window.gettext("Standard analyses"),
    skippedEntries: window.gettext("Skipped entries"),
    pointsToCreate: window.gettext("Points to create"),
    existingPointsToReuse: window.gettext("Existing points reused"),
    commentsToFill: window.gettext("Comments to fill"),
    commentsPreserved: window.gettext("Comments preserved"),
    objectsToCreate: window.gettext("Objects to create"),
    objectsReusedOrLinked: window.gettext("Objects reused/linked"),
    standardsToAttachOrReuse: window.gettext("Standards attached/reused"),
    missingStandards: window.gettext("Missing standards"),
    noPreviewWarnings: window.gettext("No blocking issue detected."),
    ruleComments: window.gettext("Existing comments are not overwritten."),
    ruleAssignments: window.gettext(
      "Existing object or standard assignments are not replaced if different.",
    ),
    ruleObjects: window.gettext("Existing objects are reused by label."),
    ruleStandards: window.gettext(
      "Standards are matched without case, spaces, hyphens, underscores, or other special characters.",
    ),
    ruleMissingStandards: window.gettext(
      "Missing standards are reported, not created.",
    ),
    ruleRetry: window.gettext("The operation can be retried safely."),
    warningMissingObjectReference: window.gettext(
      "Point %s has no object reference in HDF5 metadata.",
    ),
    warningPointLinkedToStandard: window.gettext(
      "Point %s is already linked to a standard; it will not be changed to an object analysis.",
    ),
    warningDifferentObject: window.gettext(
      "Point %s is already linked to a different object; it will not be overwritten.",
    ),
    warningDifferentComment: window.gettext(
      "Point %s already has a different comment; it will be preserved.",
    ),
    warningMissingStandardReference: window.gettext(
      "Point %s has no standard reference in HDF5 metadata.",
    ),
    warningPointLinkedToObject: window.gettext(
      "Point %s is already linked to an object; it will not be changed to a standard analysis.",
    ),
    warningDifferentStandard: window.gettext(
      "Point %s is already linked to a different standard; it will not be overwritten.",
    ),
    warningMissingStandard: window.gettext(
      "Standard %s does not exist yet; create it and retry generation to attach it.",
    ),
  };
}

export type HDF5NotebookGenerationLabels = ReturnType<
  typeof createHDF5NotebookGenerationLabels
>;

interface UseHDF5NotebookGenerationWorkflowOptions {
  runId: string;
  projectSlug: string;
  runName: string;
  fetchFn: ToolsFetch;
  hasHDF5Files: boolean;
  onGenerationComplete: () => Promise<void>;
}

export function useHDF5NotebookGenerationWorkflow({
  runId,
  projectSlug,
  runName,
  fetchFn,
  hasHDF5Files,
  onGenerationComplete,
}: UseHDF5NotebookGenerationWorkflowOptions) {
  const labels = createHDF5NotebookGenerationLabels();
  const [status, setStatus] = useState<GenerationStatus>("idle");
  const [candidateDiscoveryStatus, setCandidateDiscoveryStatus] =
    useState<CandidateDiscoveryStatus>("idle");
  const [generationCandidates, setGenerationCandidates] = useState<
    HDF5NotebookGenerationCandidate[]
  >([]);
  const [skippedGenerationCandidates, setSkippedGenerationCandidates] =
    useState<HDF5NotebookGenerationSkippedCandidate[]>([]);
  const [preflightStatus, setPreflightStatus] =
    useState<PreflightStatus>("idle");
  const [preflightData, setPreflightData] =
    useState<HDF5NotebookGenerationPreflightData | null>(null);
  const [preview, setPreview] = useState<HDF5NotebookGenerationPreview | null>(
    null,
  );
  const [fatalError, setFatalError] = useState<string | null>(null);
  const [progress, setProgress] =
    useState<HDF5NotebookGenerationProgress | null>(null);

  const isRunning = status === "running";
  const isDisabled = isRunning || !hasHDF5Files;
  const canConfirmGeneration =
    !isRunning &&
    candidateDiscoveryStatus === "loaded" &&
    preflightStatus === "loaded" &&
    generationCandidates.length > 0 &&
    preflightData !== null;
  const modalStep = status === "idle" ? 1 : 2;

  const appendProgressError = (message: string) => {
    setProgress((currentProgress) => {
      if (!currentProgress) {
        return currentProgress;
      }
      return {
        ...currentProgress,
        currentPointName: null,
        errors: [...currentProgress.errors, message],
      };
    });
  };

  const loadGenerationMetadata = async () => {
    if (isDisabled) {
      return;
    }

    setStatus("idle");
    setFatalError(null);
    setProgress(null);
    setCandidateDiscoveryStatus("loading");
    setPreflightStatus("idle");
    setGenerationCandidates([]);
    setSkippedGenerationCandidates([]);
    setPreflightData(null);
    setPreview(null);

    const result = await discoverHDF5NotebookGenerationCandidates({
      projectSlug,
      runName,
      fetchFn,
    }).catch((error) => {
      console.error(error);
      setFatalError((error as Error).message || labels.error);
      setCandidateDiscoveryStatus("error");
      return null;
    });

    if (!result) {
      return;
    }

    setGenerationCandidates(result.candidates);
    setSkippedGenerationCandidates(result.skippedCandidates);
    setCandidateDiscoveryStatus("loaded");

    if (result.candidates.length === 0) {
      setPreflightStatus("loaded");
      return;
    }

    setPreflightStatus("loading");
    try {
      const latestPreflightData = await fetchGenerationPreflightData(runId);
      setPreflightData(latestPreflightData);
      setPreview(
        previewNotebookGenerationFromHDF5({
          candidates: result.candidates,
          measuringPoints: latestPreflightData.measuringPoints,
          runObjectGroups: latestPreflightData.runObjectGroups,
          availableObjectGroups: latestPreflightData.availableObjectGroups,
          standards: latestPreflightData.standards,
          runMeasuringPointStandards:
            latestPreflightData.runMeasuringPointStandards,
          skippedCandidateCount: result.skippedCandidates.length,
        }),
      );
      setPreflightStatus("loaded");
    } catch (error) {
      console.error(error);
      setFatalError((error as Error).message || labels.error);
      setPreflightStatus("error");
    }
  };

  const startGeneration = async () => {
    if (!canConfirmGeneration || !preflightData) {
      return;
    }

    setStatus("running");
    setFatalError(null);
    setProgress(null);

    try {
      await generateNotebookFromHDF5({
        runId,
        candidates: generationCandidates,
        measuringPoints: preflightData.measuringPoints,
        runObjectGroups: preflightData.runObjectGroups,
        availableObjectGroups: preflightData.availableObjectGroups,
        standards: preflightData.standards,
        runMeasuringPointStandards: preflightData.runMeasuringPointStandards,
        services: {
          createMeasuringPoint,
          updateMeasuringPointComments,
          updateMeasuringPointObjectId,
          createObjectGroup,
          addObjectGroupToRun,
          addOrUpdateStandardToMeasuringPoint,
        },
        onProgress: setProgress,
      });

      await onGenerationComplete();
      setStatus("success");
    } catch (error) {
      console.error(error);
      const message = (error as Error).message || labels.error;
      setFatalError(message);
      appendProgressError(message);
      try {
        await onGenerationComplete();
      } catch (refreshError) {
        console.error(refreshError);
      }
      setStatus("error");
    }
  };

  return {
    labels,
    status,
    candidateDiscoveryStatus,
    preflightStatus,
    preview,
    skippedGenerationCandidates,
    progress,
    fatalError,
    isRunning,
    isDisabled,
    canConfirmGeneration,
    modalStep,
    loadGenerationMetadata,
    startGeneration,
  };
}

async function fetchGenerationPreflightData(
  runId: string,
): Promise<HDF5NotebookGenerationPreflightData> {
  const [
    measuringPoints,
    runObjectGroups,
    availableObjectGroups,
    standards,
    runMeasuringPointStandards,
  ] = await Promise.all([
    listMeasuringPoints(runId),
    fetchRunObjectGroups(runId),
    fetchAvailableObjectGroups(runId),
    listStandards(),
    listRunMeasuringPointsStandard(runId),
  ]);

  return {
    measuringPoints,
    runObjectGroups,
    availableObjectGroups,
    standards,
    runMeasuringPointStandards,
  };
}
