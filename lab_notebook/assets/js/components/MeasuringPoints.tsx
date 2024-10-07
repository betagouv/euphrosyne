import { useEffect, useState } from "react";
import type { IMeasuringPoint } from "../IMeasuringPoint";
import MeasuringPoint from "./MeasuringPoint";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import { fetchRunObjectGroups } from "../../../../lab/objects/assets/js/services";
import AddObjectGroupModal from "./AddObjectGroupModal";
import AddImageToMeasuringModal from "./AddImageToMeasuringModal";

export default function MeasuringPoints({
  runId,
  points,
  onAddObjectToPoint,
}: {
  points: IMeasuringPoint[];
  runId: string;
  onAddObjectToPoint: () => void;
}) {
  const t = {
    noPoint: window.gettext(
      "There are no notes in this notebook yet. Click the button to add the first one.",
    ),
  };

  const [objectGroups, setObjectGroups] = useState<RunObjectGroup[]>([]);

  const [addObjectModalPointId, setAddObjectModalPointId] = useState<
    string | null
  >(null);

  const [addImageToMeasuringPointId, setAddImageToMeasuringPointId] = useState<
    string | null
  >(null);

  const addImageToMeasuringPoint = points.find(
    (p) => p.id === addImageToMeasuringPointId,
  );

  useEffect(() => {
    fetchRunObjectGroups(runId).then(setObjectGroups);
    if (objectGroups.length > 0) {
      setAddObjectModalPointId(objectGroups[0].id);
    }
  }, []);

  const onAddObjectSuccess = () => {
    setAddObjectModalPointId(null);
    fetchRunObjectGroups(runId).then(setObjectGroups);
    onAddObjectToPoint();
  };

  return (
    <div>
      <AddObjectGroupModal
        runId={runId}
        runObjectGroupLabels={objectGroups.map((o) => o.objectGroup.label)}
        measuringPointId={addObjectModalPointId}
        onAddSuccess={onAddObjectSuccess}
      />
      <AddImageToMeasuringModal
        runObjectGroups={objectGroups}
        measuringPoint={addImageToMeasuringPoint}
      />
      {points.length === 0 && <p>{t["noPoint"]}</p>}
      {points.map((point) => (
        <div
          className="fr-accordions-group"
          key={`accordiong-section-${point.name}`}
        >
          <section className="fr-accordion">
            <h3 className="fr-accordion__title">
              <button
                className="fr-accordion__btn"
                aria-expanded="false"
                aria-controls={`accordiong-${point.name}`}
              >
                {point.name}
              </button>
            </h3>
            <div className="fr-collapse" id={`accordiong-${point.name}`}>
              <MeasuringPoint
                point={point}
                runObjectGroups={objectGroups}
                runId={runId}
                onAddObjectClicked={() => setAddObjectModalPointId(point.id)}
                onLocalizeImageClicked={() =>
                  setAddImageToMeasuringPointId(point.id)
                }
              />
            </div>
          </section>
        </div>
      ))}
    </div>
  );
}
