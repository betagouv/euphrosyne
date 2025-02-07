import { useCallback, useEffect, useRef, useState } from "react";
import type { IMeasuringPoint } from "../IMeasuringPoint";
import MeasuringPoint from "./MeasuringPoint";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import { fetchRunObjectGroups } from "../../../../lab/objects/assets/js/services";
import AddObjectGroupModal from "./AddObjectGroupModal";
import AddImageToMeasuringModal from "./AddImageToMeasuringModal";
import { RunMeasuringPointStandards } from "../../../../standard/assets/js/IStandard";

export default function MeasuringPoints({
  runId,
  points,
  objectGroups,
  runMeasuringPointStandards,
  onAddObjectToPoint,
  setObjectGroups,
}: {
  points: IMeasuringPoint[];
  runId: string;
  runMeasuringPointStandards: RunMeasuringPointStandards;
  objectGroups: RunObjectGroup[];
  onAddObjectToPoint: () => void;
  setObjectGroups: (objectGroups: RunObjectGroup[]) => void;
}) {
  const t = {
    noPoint: window.gettext(
      "There are no notes in this notebook yet. Click the button to add the first one.",
    ),
    unfoldAll: window.gettext("Unfold all"),
    closeAll: window.gettext("Close all"),
  };

  // Selected measuring point for object group modal
  const [addObjectModalPointId, setAddObjectModalPointId] = useState<
    string | null
  >(null);

  // Selected measuring point for image localization modal
  const [addImageToMeasuringPoint, setAddImageToMeasuringPoint] =
    useState<IMeasuringPoint>();

  useEffect(() => {
    // Init object group selection & image location modal
    if (objectGroups.length > 0) {
      setAddObjectModalPointId(objectGroups[0].id);
    }
  }, []);

  useEffect(() => {
    // Reset if point changes
    if (addImageToMeasuringPoint)
      setAddImageToMeasuringPoint(
        points.find((p) => p.id === addImageToMeasuringPoint.id),
      );
  }, [points]);

  const onAddObjectSuccess = useCallback(() => {
    setAddObjectModalPointId(null);
    fetchRunObjectGroups(runId).then(setObjectGroups);
    onAddObjectToPoint();
  }, [runId]);

  // Accordion buttons management

  const [allExpanded, setAllExpanded] = useState(false);

  const accordionButtons = useRef<Array<HTMLButtonElement | null>>([]);

  useEffect(() => {
    accordionButtons.current = accordionButtons.current.slice(0, points.length);
  }, [points]);

  const onAccordionClick = () => {
    const expandedNum: number = (
      accordionButtons.current.map((b) =>
        b?.ariaExpanded === "true" ? 1 : 0,
      ) as number[]
    ).reduce((a, b) => a + b);
    setAllExpanded(expandedNum === points.length - 1); // points.length - 1 because ariaExpanded is not updated when event is fired
  };

  const toggleButtons = (action: "open" | "close") => {
    // Expand all accordions section. If all are already expanded, collaspe everything.
    const actionOnAriaExpanded = action === "open" ? "false" : "true";
    accordionButtons.current.forEach((b) => {
      if (b && b.ariaExpanded === actionOnAriaExpanded) b.click();
    });
    setAllExpanded(action === "open" ? true : false);
  };

  const getMeasuringPointLabel = useCallback(
    (point: IMeasuringPoint) => {
      let label: string | undefined = undefined;
      if (point.objectGroupId) {
        label = objectGroups.find(
          (rog) => rog.objectGroup.id === point.objectGroupId,
        )?.objectGroup.label;
      } else if (point.id in runMeasuringPointStandards) {
        label = "[STD] " + runMeasuringPointStandards[point.id].standard.label;
      }
      if (label) return `${point.name} - ${label}`;
      return point.name;
    },
    [objectGroups, runMeasuringPointStandards],
  );

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
      {points.length > 1 && (
        <div className="fr-my-1w">
          <button
            className={`fr-btn fr-btn--tertiary-no-outline fr-btn--icon-left fr-icon-arrow-${allExpanded ? "up" : "down"}-s-line`}
            onClick={() => toggleButtons(allExpanded ? "close" : "open")}
          >
            {allExpanded ? t.closeAll : t.unfoldAll}
          </button>
        </div>
      )}
      {points.length === 0 && <p>{t["noPoint"]}</p>}
      {points.map((point, index) => (
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
                ref={(el) => (accordionButtons.current[index] = el)}
                onClick={onAccordionClick}
              >
                {getMeasuringPointLabel(point)}
              </button>
            </h3>
            <div className="fr-collapse" id={`accordiong-${point.name}`}>
              <MeasuringPoint
                point={point}
                runObjectGroups={objectGroups}
                runId={runId}
                measuringPointStandard={runMeasuringPointStandards[point.id]}
                onAddObjectClicked={() => setAddObjectModalPointId(point.id)}
                onLocalizeImageClicked={() =>
                  setAddImageToMeasuringPoint(point)
                }
              />
            </div>
          </section>
        </div>
      ))}
    </div>
  );
}
