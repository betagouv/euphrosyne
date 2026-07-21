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

interface UseHDF5NotebookGenerationWorkflowOptions {
  runId: string;
  projectSlug: string;
  runName: string;
  fetchFn: ToolsFetch;
  hasHDF5Files: boolean;
  errorMessage: string;
  onGenerationComplete: () => Promise<void>;
}

export function useHDF5NotebookGenerationWorkflow({
  runId,
  projectSlug,
  runName,
  fetchFn,
  hasHDF5Files,
  errorMessage,
  onGenerationComplete,
}: UseHDF5NotebookGenerationWorkflowOptions) {
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
      setFatalError((error as Error).message || errorMessage);
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
      setFatalError((error as Error).message || errorMessage);
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
      const message = (error as Error).message || errorMessage;
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
