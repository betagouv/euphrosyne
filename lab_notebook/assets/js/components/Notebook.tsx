import { useEffect, useState } from "react";
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

interface NotebookProps {
  runId: string;
  projectSlug: string;
}

export default function Notebook({ runId, projectSlug }: NotebookProps) {
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
        <div>
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
