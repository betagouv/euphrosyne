import { useEffect, useMemo, useState } from "react";
import {
  createMeasuringPoint,
  listMeasuringPoints,
} from "../../../../lab/assets/js/measuring-point.services";
import MeasuringPoints from "./MeasuringPoints";
import { NotebookContext, useNotebookContext } from "../Notebook.context";
import MeasuringPointImageGallery from "./MeasuringPointImageGallery";
import {
  EuphrosyneToolsClientContext,
  useClientContext,
} from "../../../../shared/js/EuphrosyneToolsClient.context";
import {
  listRunMeasuringPointsStandard,
  listStandards,
} from "../../../../standard/assets/js/standard-services";
import { fetchRunObjectGroups } from "../../../../lab/objects/assets/js/services";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import { useImageStorage } from "../hooks/useImageStorage";
import { useRunDataFiles } from "../data-files";
import NotebookDataFilesSection from "./NotebookDataFilesSection";

interface NotebookProps {
  runId: string;
  projectId: string;
  projectSlug: string;
  runLabel: string;
  isDataAvailable: boolean;
}

export default function Notebook({
  runId,
  projectId,
  projectSlug,
  runLabel,
  isDataAvailable,
}: NotebookProps) {
  const t = {
    gallery: window.gettext("Run images with point locations"),
    "Add image": window.gettext("Add image"),
    "Measuring points": window.gettext("Measuring points"),
    "Add point": window.gettext("Add point"),
    "Global run files": window.gettext("Global run files"),
  };

  const imageStorage = useImageStorage(projectSlug);

  const notebookContext = useNotebookContext(projectSlug, runId, imageStorage);
  const {
    measuringPoints,
    runMeasuringPointStandards,
    setMeasuringPoints,
    setStandards,
    setRunMeasuringPointStandards,
  } = notebookContext;

  const toolsClient = useClientContext();

  const [isAddingPoint, setIsAddingPoint] = useState(false);
  const [hasLoadedMeasuringPoints, setHasLoadedMeasuringPoints] =
    useState(false);

  const [objectGroups, setObjectGroups] = useState<RunObjectGroup[]>([]);

  const measuringPointNames = useMemo(
    () => measuringPoints.map((point) => point.name),
    [measuringPoints],
  );

  const { dataFiles, isLoading: isLoadingDataFiles, error: dataFilesError } =
    useRunDataFiles({
      projectSlug,
      runLabel,
      isDataAvailable,
      measuringPointNames,
      fetchFn: toolsClient.fetchFn,
    });

  const getNextMeasuringPointName = () => {
    const n = measuringPoints.length + 1;
    return n.toString().padStart(3, "0");
  };

  const onAddPointClick = async () => {
    setIsAddingPoint(true);
    await createMeasuringPoint(runId, {
      name: getNextMeasuringPointName(),
    }).finally(() => setIsAddingPoint(false));
    setMeasuringPoints(await listMeasuringPoints(runId));
    setHasLoadedMeasuringPoints(true);
    window.scrollTo(0, document.body.scrollHeight);
  };

  // useEffect

  useEffect(() => {
    listMeasuringPoints(runId).then((points) => {
      setMeasuringPoints(points);
      setHasLoadedMeasuringPoints(true);
    });
  }, []);

  useEffect(() => {
    listStandards().then(setStandards);
  }, []);

  useEffect(() => {
    listRunMeasuringPointsStandard(runId).then((data) => {
      setRunMeasuringPointStandards(data);
    });
  }, []);

  useEffect(() => {
    fetchRunObjectGroups(runId).then(setObjectGroups);
  }, []);

  const AddButton = () => (
    <button
      className="fr-btn fr-btn--secondary fr-mt-2w"
      onClick={onAddPointClick}
      disabled={isAddingPoint}
    >
      {t["Add point"]}
    </button>
  );

  return (
    <EuphrosyneToolsClientContext.Provider value={toolsClient}>
      <NotebookContext.Provider value={notebookContext}>
        <div>
          {isDataAvailable && hasLoadedMeasuringPoints && (
            <NotebookDataFilesSection
              title={t["Global run files"]}
              rawFiles={dataFiles.raw.global}
              processedFiles={dataFiles.processed.global}
              projectId={projectId}
              projectSlug={projectSlug}
              runLabel={runLabel}
              fetchFn={toolsClient.fetchFn}
              isLoading={isLoadingDataFiles}
              error={dataFilesError}
            />
          )}

          <div className="flex-container fr-mt-3w">
            <h4>{t.gallery}</h4>
          </div>
          <MeasuringPointImageGallery runObjectGroups={objectGroups} />

          <div className="fr-mt-4w">
            <div className="flex-container">
              <h4>{t["Measuring points"]}</h4>
              <div>
                <AddButton />
              </div>
            </div>
            <MeasuringPoints
              points={measuringPoints}
              runId={runId}
              dataFiles={dataFiles}
              projectId={projectId}
              projectSlug={projectSlug}
              runLabel={runLabel}
              fetchFn={toolsClient.fetchFn}
              runMeasuringPointStandards={runMeasuringPointStandards}
              objectGroups={objectGroups}
              onAddObjectToPoint={() =>
                listMeasuringPoints(runId).then(setMeasuringPoints)
              }
              setObjectGroups={(objectGroups) => setObjectGroups(objectGroups)}
            />
            {measuringPoints.length > 20 && (
              <div className="flex-container">
                <div></div>
                <AddButton />
              </div>
            )}
          </div>
        </div>
      </NotebookContext.Provider>
    </EuphrosyneToolsClientContext.Provider>
  );
}
