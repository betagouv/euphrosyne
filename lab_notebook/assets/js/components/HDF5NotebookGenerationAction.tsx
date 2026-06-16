import { Dispatch, SetStateAction, useState } from "react";
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
import {
  ObjectGroup,
  RunObjectGroup,
} from "../../../../lab/objects/assets/js/types";
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
import type { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import {
  discoverHDF5NotebookGenerationCandidates,
  generateNotebookFromHDF5,
  previewNotebookGenerationFromHDF5,
  type HDF5NotebookGenerationCandidate,
  type HDF5NotebookGenerationPreview,
  type HDF5NotebookGenerationProgress,
  type HDF5NotebookGenerationSkippedCandidate,
} from "../hdf5";
import { createHDF5NotebookGenerationLabels } from "./HDF5NotebookGenerationLabels";
import HDF5NotebookGenerationModal from "./HDF5NotebookGenerationModal";
import type {
  CandidateDiscoveryStatus,
  GenerationStatus,
  PreflightStatus,
} from "./HDF5NotebookGenerationPanels";

interface HDF5NotebookGenerationActionProps {
  runId: string;
  projectSlug: string;
  runName: string;
  fetchFn: ToolsFetch;
  canGenerateNotebookFromHDF5: boolean;
  hasHDF5Files: boolean;
  setMeasuringPoints: Dispatch<SetStateAction<IMeasuringPoint[]>>;
  setObjectGroups: Dispatch<SetStateAction<RunObjectGroup[]>>;
  setStandards: Dispatch<SetStateAction<IStandard[]>>;
  setRunMeasuringPointStandards: Dispatch<
    SetStateAction<RunMeasuringPointStandards>
  >;
}

interface HDF5NotebookGenerationPreflightData {
  loadedAt: number;
  measuringPoints: IMeasuringPoint[];
  runObjectGroups: RunObjectGroup[];
  availableObjectGroups: ObjectGroup[];
  standards: IStandard[];
  runMeasuringPointStandards: RunMeasuringPointStandards;
}

const PREFLIGHT_STALE_MS = 2 * 60 * 1000;

export default function HDF5NotebookGenerationAction({
  runId,
  projectSlug,
  runName,
  fetchFn,
  canGenerateNotebookFromHDF5,
  hasHDF5Files,
  setMeasuringPoints,
  setObjectGroups,
  setStandards,
  setRunMeasuringPointStandards,
}: HDF5NotebookGenerationActionProps) {
  const labels = createHDF5NotebookGenerationLabels();
  const modalId = "hdf5-notebook-generation-modal";
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

  if (!canGenerateNotebookFromHDF5) {
    return null;
  }

  const isRunning = status === "running";
  const isDisabled = isRunning || !hasHDF5Files;
  const canConfirmGeneration =
    !isRunning &&
    candidateDiscoveryStatus === "loaded" &&
    preflightStatus === "loaded" &&
    generationCandidates.length > 0;
  const hasGenerationStarted = status !== "idle";
  const modalStep = hasGenerationStarted ? 2 : 1;

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
      setMeasuringPoints(latestPreflightData.measuringPoints);
      setObjectGroups(latestPreflightData.runObjectGroups);
      setStandards(latestPreflightData.standards);
      setRunMeasuringPointStandards(
        latestPreflightData.runMeasuringPointStandards,
      );
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

  const refreshNotebookState = async () => {
    const [latestPoints, latestObjectGroups, latestRunStandards] =
      await Promise.all([
        listMeasuringPoints(runId),
        fetchRunObjectGroups(runId),
        listRunMeasuringPointsStandard(runId),
      ]);
    setMeasuringPoints(latestPoints);
    setObjectGroups(latestObjectGroups);
    setRunMeasuringPointStandards(latestRunStandards);
  };

  const startGeneration = async () => {
    if (!canConfirmGeneration) {
      return;
    }

    setStatus("running");
    setFatalError(null);
    setProgress(null);

    try {
      const latestPreflightData =
        preflightData &&
        Date.now() - preflightData.loadedAt < PREFLIGHT_STALE_MS
          ? preflightData
          : await fetchGenerationPreflightData(runId);

      setMeasuringPoints(latestPreflightData.measuringPoints);
      setObjectGroups(latestPreflightData.runObjectGroups);
      setStandards(latestPreflightData.standards);
      setRunMeasuringPointStandards(
        latestPreflightData.runMeasuringPointStandards,
      );

      const result = await generateNotebookFromHDF5({
        runId,
        candidates: generationCandidates,
        measuringPoints: latestPreflightData.measuringPoints,
        runObjectGroups: latestPreflightData.runObjectGroups,
        availableObjectGroups: latestPreflightData.availableObjectGroups,
        standards: latestPreflightData.standards,
        runMeasuringPointStandards:
          latestPreflightData.runMeasuringPointStandards,
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

      setMeasuringPoints(result.measuringPoints);
      setObjectGroups(result.runObjectGroups);
      setRunMeasuringPointStandards(result.runMeasuringPointStandards);
      await refreshNotebookState();
      setStatus("success");
    } catch (error) {
      console.error(error);
      const message = (error as Error).message || labels.error;
      setFatalError(message);
      appendProgressError(message);
      try {
        await refreshNotebookState();
      } catch (refreshError) {
        console.error(refreshError);
      }
      setStatus("error");
    }
  };

  return (
    <div
      className="hdf5-generation"
      title={!hasHDF5Files ? labels.noFiles : undefined}
    >
      <button
        className="fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-magic-line"
        aria-controls={modalId}
        data-fr-opened={false}
        onClick={loadGenerationMetadata}
        disabled={isDisabled}
        title={!hasHDF5Files ? labels.noFiles : undefined}
      >
        {labels.button}
      </button>
      <HDF5NotebookGenerationModal
        modalId={modalId}
        modalStep={modalStep}
        status={status}
        candidateDiscoveryStatus={candidateDiscoveryStatus}
        preflightStatus={preflightStatus}
        preview={preview}
        skippedGenerationCandidates={skippedGenerationCandidates}
        progress={progress}
        fatalError={fatalError}
        canConfirmGeneration={canConfirmGeneration}
        isRunning={isRunning}
        labels={labels}
        onStartGeneration={startGeneration}
      />
    </div>
  );
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
    loadedAt: Date.now(),
    measuringPoints,
    runObjectGroups,
    availableObjectGroups,
    standards,
    runMeasuringPointStandards,
  };
}
