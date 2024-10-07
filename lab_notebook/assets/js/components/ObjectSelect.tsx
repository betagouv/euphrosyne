import { ChangeEvent, useContext, useEffect, useId, useState } from "react";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import { updateMeasuringPointObjectId } from "../../../../lab/assets/js/measuring-point.service";
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

  const { runId } = useContext(NotebookContext);

  const selectId = useId();

  const objectGroup = runObjectGroups.find(
    (rog) => rog.objectGroup.id === measuringPoint.objectGroupId,
  )?.objectGroup;

  const [selectedObjectGroupId, setSelectedObjectGroupId] = useState<string>(
    objectGroup?.id || "",
  );

  const changeObjectGroup = async (event: ChangeEvent<HTMLSelectElement>) => {
    const objectGroupId = event.target.value;
    await updateMeasuringPointObjectId(runId, measuringPoint.id, objectGroupId);
    setSelectedObjectGroupId(objectGroupId);
  };

  useEffect(() => {
    setSelectedObjectGroupId(objectGroup?.id || "");
  }, [objectGroup]);

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
        value={selectedObjectGroupId}
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
