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
import useNotebookHDF5Data from "../hooks/useNotebookHDF5Data";
import HDF5MapModal from "./HDF5MapModal";
import HDF5RunDataSection from "./HDF5RunDataSection";
import HDF5SpectrumModal from "./HDF5SpectrumModal";
import {
  HDF5DatasetEntry,
  NotebookHDF5Context,
  NotebookHDF5ContextValue,
} from "../hdf5";

interface NotebookProps {
  runId: string;
  projectSlug: string;
  projectId: string;
  runName: string;
}

const hdf5SpectrumModalId = "hdf5-spectrum-modal";
const hdf5MapModalId = "hdf5-map-modal";

export default function Notebook({
  runId,
  projectSlug,
  projectId,
  runName,
}: NotebookProps) {
  const t = {
    gallery: window.gettext("Run images with point locations"),
    "Add image": window.gettext("Add image"),
    "Measuring points": window.gettext("Measuring points"),
    "Add point": window.gettext("Add point"),
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

  const [objectGroups, setObjectGroups] = useState<RunObjectGroup[]>([]);
  const [selectedHDF5Entry, setSelectedHDF5Entry] =
    useState<HDF5DatasetEntry | null>(null);
  const hdf5Data = useNotebookHDF5Data({
    projectSlug,
    runName,
    measuringPoints,
    fetchFn: toolsClient.fetchFn,
  });
  const hdf5Context: NotebookHDF5ContextValue = useMemo(
    () => ({
      entriesByPointId: hdf5Data.entriesByPointId,
      hasMatchesByPointId: hdf5Data.hasMatchesByPointId,
      loadingEntriesByPointId: hdf5Data.loadingEntriesByPointId,
      spectrumModalId: hdf5SpectrumModalId,
      mapModalId: hdf5MapModalId,
      loadEntriesForPoint: hdf5Data.loadEntriesForPoint,
      visualizeEntry: setSelectedHDF5Entry,
    }),
    [
      hdf5Data.entriesByPointId,
      hdf5Data.hasMatchesByPointId,
      hdf5Data.loadingEntriesByPointId,
      hdf5Data.loadEntriesForPoint,
    ],
  );

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
    window.scrollTo(0, document.body.scrollHeight);
  };

  // useEffect

  useEffect(() => {
    listMeasuringPoints(runId).then(setMeasuringPoints);
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
        <NotebookHDF5Context.Provider value={hdf5Context}>
          <div>
            <div className="flex-container fr-mt-3w">
              <h4>{t.gallery}</h4>
            </div>
            <MeasuringPointImageGallery runObjectGroups={objectGroups} />

            <div>
              <section className="fr-mt-4w">
                <HDF5RunDataSection
                  projectId={projectId}
                  fileSummaries={hdf5Data.fileSummaries}
                  isLoading={hdf5Data.isLoading}
                  error={hdf5Data.error}
                />
              </section>
              <div className="flex-container fr-mt-4w">
                <h4>{t["Measuring points"]}</h4>
                <div>
                  <AddButton />
                </div>
              </div>
              <MeasuringPoints
                points={measuringPoints}
                runId={runId}
                runMeasuringPointStandards={runMeasuringPointStandards}
                objectGroups={objectGroups}
                onAddObjectToPoint={() =>
                  listMeasuringPoints(runId).then(setMeasuringPoints)
                }
                setObjectGroups={(objectGroups) =>
                  setObjectGroups(objectGroups)
                }
              />
              {measuringPoints.length > 20 && (
                <div className="flex-container">
                  <div></div>
                  <AddButton />
                </div>
              )}
            </div>
            <HDF5SpectrumModal
              modalId={hdf5SpectrumModalId}
              entry={
                selectedHDF5Entry?.dataKind === "spectrum"
                  ? selectedHDF5Entry
                  : null
              }
              fetchFn={toolsClient.fetchFn}
              onClose={() => setSelectedHDF5Entry(null)}
            />
            <HDF5MapModal
              modalId={hdf5MapModalId}
              entry={
                selectedHDF5Entry?.dataKind === "map" ? selectedHDF5Entry : null
              }
              fetchFn={toolsClient.fetchFn}
              onClose={() => setSelectedHDF5Entry(null)}
            />
          </div>
        </NotebookHDF5Context.Provider>
      </NotebookContext.Provider>
    </EuphrosyneToolsClientContext.Provider>
  );
}
