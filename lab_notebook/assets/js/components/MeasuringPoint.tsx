import { css } from "@emotion/react";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import type { IMeasuringPoint } from "../IMeasuringPoint";
import MeasuringPointComments from "./MeasuringPointComments";
import ObjectSelect from "./ObjectSelect";

const buttonContainerStyle = css({
  border: "dashed var(--background-action-high-blue-france) 1px",
  width: "100%",
  height: "100%",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
});

const containerStyle = css({
  display: "flex",
  alignItems: "center",
});

const addButtonStyle = css({
  marginTop: "8px",
});

const imageContainerStyle = css({
  width: "100%",
  height: "auto",
  aspectRatio: "1/1",
});

export default function MeasuringPoint({
  point,
  runObjectGroups,
  onAddObjectClicked,
  onLocalizeImageClicked,
}: {
  point: IMeasuringPoint;
  runObjectGroups: RunObjectGroup[];
  runId: string;
  onAddObjectClicked: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onLocalizeImageClicked: (event: React.MouseEvent<HTMLButtonElement>) => void;
}) {
  const t = {
    addObjectGroup: window.gettext("Add a new object group"),
    localizeOnObject: window.gettext("Localize on object image"),
  };
  return (
    <div className="fr-container--fluid">
      <div className="fr-grid-row fr-grid-row--gutters">
        <div className="fr-col-12 fr-col-md-5">
          <div css={imageContainerStyle}>
            <div css={buttonContainerStyle}>
              <button
                className="fr-btn fr-icon-add-line fr-btn--secondary fr-btn--icon-left"
                aria-controls="add-measuring-point-image-modal"
                data-fr-opened={false}
                onClick={onLocalizeImageClicked}
              >
                {t.localizeOnObject}
              </button>
            </div>
          </div>
        </div>
        <div className="fr-col-12 fr-col-md-7">
          <div css={containerStyle}>
            <ObjectSelect
              runObjectGroups={runObjectGroups}
              measuringPoint={point}
            />

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
          <MeasuringPointComments pointId={point.id} />
        </div>
      </div>
    </div>
  );
}
