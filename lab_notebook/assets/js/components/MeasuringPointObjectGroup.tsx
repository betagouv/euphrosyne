import { css } from "@emotion/react";
import ObjectSelect from "./ObjectSelect";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import { HTMLProps } from "react";
import { IMeasuringPoint } from "../../../../shared/js/images/types";

const addButtonStyle = css({
  marginTop: "8px",
});

const containerStyle = css({
  display: "flex",
  alignItems: "center",
});

interface MeasuringPointObjectGroupProps {
  runObjectGroups: RunObjectGroup[];
  point: IMeasuringPoint;
  onAddObjectClicked: (event: React.MouseEvent<HTMLButtonElement>) => void;
}

export default function MeasuringPointObjectGroup({
  runObjectGroups,
  point,
  onAddObjectClicked,
  ...props
}: MeasuringPointObjectGroupProps & HTMLProps<HTMLDivElement>) {
  const t = {
    addObjectGroup: window.gettext("Add a new object group"),
  };
  return (
    <div {...props} css={containerStyle}>
      <ObjectSelect runObjectGroups={runObjectGroups} measuringPoint={point} />

      <button
        type="button"
        className="fr-btn fr-icon-add-line fr-btn--tertiary-no-outline fr-ml-2v"
        title={t.addObjectGroup}
        css={addButtonStyle}
        aria-controls="add-object-group-modal"
        data-fr-opened={false}
        onClick={onAddObjectClicked}
      >
        {t.addObjectGroup}
      </button>
    </div>
  );
}
