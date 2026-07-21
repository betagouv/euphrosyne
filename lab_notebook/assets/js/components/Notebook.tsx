import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { createMeasuringPoint } from "../../../../lab/assets/js/measuring-point.services";
import MeasuringPoints from "./MeasuringPoints";
import { NotebookContext, useNotebookContext } from "../Notebook.context";
import MeasuringPointImageGallery from "./MeasuringPointImageGallery";
import {
  EuphrosyneToolsClientContext,
  useClientContext,
} from "../../../../shared/js/EuphrosyneToolsClient.context";
import { useImageStorage } from "../hooks/useImageStorage";
import useNotebookHDF5Data from "../hooks/useNotebookHDF5Data";
import HDF5RunDataSection from "./HDF5RunDataSection";
import { NotebookHDF5Context } from "../hdf5";
import HDF5NotebookGenerationModal from "./HDF5NotebookGenerationModal";

interface NotebookProps {
  runId: string;
  projectSlug: string;
  projectId: string;
  runName: string;
  isLabAdmin: boolean;
  canWriteNotebook: boolean;
}

export default function Notebook({
  runId,
  projectSlug,
  projectId,
  runName,
  isLabAdmin,
  canWriteNotebook,
}: NotebookProps) {
  const t = {
    gallery: window.gettext("Run images with point locations"),
    "Add image": window.gettext("Add image"),
    "Measuring points": window.gettext("Measuring points"),
    "Add point": window.gettext("Add point"),
  };

  const imageStorage = useImageStorage(projectSlug);

  const notebookContext = useNotebookContext(projectSlug, runId, imageStorage);
  const { measuringPoints, refreshNotebookState } = notebookContext;

  const toolsClient = useClientContext();

  const [isAddingPoint, setIsAddingPoint] = useState(false);

  const hdf5Data = useNotebookHDF5Data({
    projectSlug,
    runName,
    measuringPoints,
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
    await refreshNotebookState();
    window.scrollTo(0, document.body.scrollHeight);
  };

  // useEffect

  useEffect(() => {
    void refreshNotebookState();
  }, [refreshNotebookState]);

  const AddButton = () => (
    <button
      className="fr-btn fr-btn--secondary fr-mt-2w"
      onClick={onAddPointClick}
      disabled={isAddingPoint}
    >
      {t["Add point"]}
    </button>
  );

  const generationActionContainer = document.getElementById(
    "notebook-generation-action",
  );

  const generationAction = (
    <HDF5NotebookGenerationModal
      runId={runId}
      projectSlug={projectSlug}
      runName={runName}
      fetchFn={toolsClient.fetchFn}
      isLabAdmin={isLabAdmin}
      canWriteNotebook={canWriteNotebook}
      hasHDF5Files={hdf5Data.fileSummaries.length > 0}
      onGenerationComplete={refreshNotebookState}
    />
  );

  return (
    <EuphrosyneToolsClientContext.Provider value={toolsClient}>
      <NotebookContext.Provider value={notebookContext}>
        <NotebookHDF5Context.Provider value={hdf5Data.contextValue}>
          {generationActionContainer &&
            createPortal(generationAction, generationActionContainer)}
          <div>
            <div className="flex-container fr-mt-3w">
              <h4>{t.gallery}</h4>
            </div>
            <MeasuringPointImageGallery />

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
              <MeasuringPoints />
              {measuringPoints.length > 20 && (
                <div className="flex-container">
                  <div></div>
                  <AddButton />
                </div>
              )}
            </div>
          </div>
        </NotebookHDF5Context.Provider>
      </NotebookContext.Provider>
    </EuphrosyneToolsClientContext.Provider>
  );
}
