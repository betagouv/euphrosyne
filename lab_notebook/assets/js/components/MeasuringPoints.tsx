import { useCallback, useContext, useEffect, useRef, useState } from "react";
import type { IMeasuringPoint } from "../../../../shared/js/images/types";
import MeasuringPoint from "./MeasuringPoint";
import AddObjectGroupModal from "./AddObjectGroupModal";
import AddImageToMeasuringModal from "./AddImageToMeasuringModal";
import { useNotebookHDF5Context } from "../hdf5";
import { NotebookContext } from "../Notebook.context";

export default function MeasuringPoints() {
  const t = {
    noPoint: window.gettext(
      "There are no notes in this notebook yet. Click the button to add the first one.",
    ),
    unfoldAll: window.gettext("Unfold all"),
    closeAll: window.gettext("Close all"),
  };
  const {
    runId,
    measuringPoints,
    runObjectGroups,
    runMeasuringPointStandards,
    refreshNotebookState,
  } = useContext(NotebookContext);
  const { hasViewableHDF5DataByPointId, loadEntriesForPoint } =
    useNotebookHDF5Context();

  // Selected measuring point for object group modal
  const [addObjectModalPointId, setAddObjectModalPointId] = useState<
    string | null
  >(null);

  // Selected measuring point for image localization modal
  const [addImageToMeasuringPoint, setAddImageToMeasuringPoint] =
    useState<IMeasuringPoint>();

  useEffect(() => {
    // Init object group selection & image location modal
    if (!addObjectModalPointId && runObjectGroups.length > 0) {
      setAddObjectModalPointId(runObjectGroups[0].id);
    }
  }, [addObjectModalPointId, runObjectGroups]);

  useEffect(() => {
    // Reset if point changes
    if (addImageToMeasuringPoint)
      setAddImageToMeasuringPoint(
        measuringPoints.find((p) => p.id === addImageToMeasuringPoint.id),
      );
  }, [measuringPoints]);

  const onAddObjectSuccess = useCallback(() => {
    setAddObjectModalPointId(null);
    void refreshNotebookState();
  }, [refreshNotebookState]);

  // Accordion buttons management

  const [allExpanded, setAllExpanded] = useState(false);

  const accordionButtons = useRef<Array<HTMLButtonElement | null>>([]);

  useEffect(() => {
    accordionButtons.current = accordionButtons.current.slice(
      0,
      measuringPoints.length,
    );
  }, [measuringPoints]);

  useEffect(() => {
    accordionButtons.current.forEach((button, index) => {
      const point = measuringPoints[index];
      if (
        button?.ariaExpanded === "true" &&
        point &&
        hasViewableHDF5DataByPointId[point.id]
      ) {
        void loadEntriesForPoint(point.id);
      }
    });
  }, [hasViewableHDF5DataByPointId, measuringPoints, loadEntriesForPoint]);

  const onAccordionClick = (
    point: IMeasuringPoint,
    event: React.MouseEvent<HTMLButtonElement>,
  ) => {
    if (
      // accordion is currently closed, and the user is clicking it to open it.
      event.currentTarget.ariaExpanded === "false" &&
      hasViewableHDF5DataByPointId[point.id]
    ) {
      void loadEntriesForPoint(point.id);
    }

    const expandedNum: number = (
      accordionButtons.current.map((b) =>
        b?.ariaExpanded === "true" ? 1 : 0,
      ) as number[]
    ).reduce((a, b) => a + b);
    setAllExpanded(expandedNum === measuringPoints.length - 1); // measuringPoints.length - 1 because ariaExpanded is not updated when event is fired
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
        label = runObjectGroups.find(
          (rog) => rog.objectGroup.id === point.objectGroupId,
        )?.objectGroup.label;
      } else if (point.id in runMeasuringPointStandards) {
        label = "[STD] " + runMeasuringPointStandards[point.id].standard.label;
      }
      if (label) return `${point.name} - ${label}`;
      return point.name;
    },
    [runObjectGroups, runMeasuringPointStandards],
  );

  return (
    <div>
      <AddObjectGroupModal
        runId={runId}
        runObjectGroupLabels={runObjectGroups.map((o) => o.objectGroup.label)}
        measuringPointId={addObjectModalPointId}
        onAddSuccess={onAddObjectSuccess}
      />
      <AddImageToMeasuringModal
        runObjectGroups={runObjectGroups}
        measuringPoint={addImageToMeasuringPoint}
      />
      {measuringPoints.length > 1 && (
        <div className="fr-my-1w">
          <button
            className={`fr-btn fr-btn--tertiary-no-outline fr-btn--icon-left fr-icon-arrow-${allExpanded ? "up" : "down"}-s-line`}
            onClick={() => toggleButtons(allExpanded ? "close" : "open")}
          >
            {allExpanded ? t.closeAll : t.unfoldAll}
          </button>
        </div>
      )}
      {measuringPoints.length === 0 && <p>{t["noPoint"]}</p>}
      {measuringPoints.map((point, index) => (
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
                ref={(el) => {
                  accordionButtons.current[index] = el;
                }}
                onClick={(event) => onAccordionClick(point, event)}
              >
                {getMeasuringPointLabel(point)}
              </button>
            </h3>
            <div className="fr-collapse" id={`accordiong-${point.name}`}>
              <MeasuringPoint
                point={point}
                runObjectGroups={runObjectGroups}
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
