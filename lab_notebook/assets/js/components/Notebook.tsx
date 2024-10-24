import { useEffect } from "react";
import {
  createMeasuringPoint,
  listMeasuringPoints,
} from "../../../../lab/assets/js/measuring-point.services";
import MeasuringPoints from "./MeasuringPoints";
import { NotebookContext, useNotebookContext } from "../Notebook.context";
import { StorageImageServices } from "../notebook-image.services";
import MeasuringPointImageGallery from "./MeasuringPointImageGallery";

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

  const notebookContext = useNotebookContext(projectSlug, runId);
  const { setImageStorage, measuringPoints, setMeasuringPoints } =
    notebookContext;

  const getNextMeasuringPointName = () => {
    const n = measuringPoints.length + 1;
    return n > 9 ? "0" + n : "00" + n;
  };

  const onAddPointClick = async () => {
    await createMeasuringPoint(runId, {
      name: getNextMeasuringPointName(),
    });
    setMeasuringPoints(await listMeasuringPoints(runId));
  };

  // useEffect

  useEffect(() => {
    listMeasuringPoints(runId).then(setMeasuringPoints);
    new StorageImageServices(notebookContext.projectSlug)
      .getImagesUrlAndToken()
      .then(setImageStorage);
  }, []);

  return (
    <NotebookContext.Provider value={notebookContext}>
      <div>
        <div className="flex-container fr-mt-3w">
          <h4>{t.gallery}</h4>
        </div>
        <MeasuringPointImageGallery />

        <div className="fr-mt-4w">
          <div className="flex-container">
            <h4>{t["Measuring points"]}</h4>
            <div>
              <button
                className="fr-btn fr-btn--secondary"
                onClick={onAddPointClick}
              >
                {t["Add point"]}
              </button>
            </div>
          </div>
          <MeasuringPoints
            points={measuringPoints}
            runId={runId}
            onAddObjectToPoint={() =>
              listMeasuringPoints(runId).then(setMeasuringPoints)
            }
          />
        </div>
      </div>
    </NotebookContext.Provider>
  );
}
