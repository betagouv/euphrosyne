import { ChangeEvent, useContext, useId } from "react";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import { updateMeasuringPointObjectId } from "../../../../lab/assets/js/measuring-point.services";
import { IMeasuringPoint } from "../IMeasuringPoint";
import { NotebookContext } from "../Notebook.context";

export default function ObjectSelect({
  measuringPoint,
  runObjectGroups,
}: {
  runObjectGroups: RunObjectGroup[];
  measuringPoint: IMeasuringPoint;
}) {
  const t = {
    objectReference: window.gettext("Object reference"),
    emptyObject: window.gettext("No object group / object selected"),
  };

  const { runId, addObjectToMeasuringPoint } = useContext(NotebookContext);

  const selectId = useId();

  const changeObjectGroup = async (event: ChangeEvent<HTMLSelectElement>) => {
    const objectGroupId = event.target.value;
    await updateMeasuringPointObjectId(runId, measuringPoint.id, objectGroupId);
    addObjectToMeasuringPoint(measuringPoint.id, objectGroupId);
  };

  return (
    <div className="fr-select-group">
      <label className="fr-label" htmlFor={selectId}>
        {t.objectReference}
      </label>
      <select
        className="fr-select"
        id={selectId}
        name="select"
        onChange={changeObjectGroup}
        value={measuringPoint.objectGroupId || undefined}
      >
        <option value="">{t.emptyObject}</option>
        {runObjectGroups.map((og) => (
          <option key={`${selectId}-option-${og.id}`} value={og.objectGroup.id}>
            {og.objectGroup.label}
          </option>
        ))}
      </select>
    </div>
  );
}
