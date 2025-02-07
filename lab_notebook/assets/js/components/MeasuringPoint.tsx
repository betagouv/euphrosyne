import { css } from "@emotion/react";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import type { IMeasuringPoint } from "../IMeasuringPoint";
import MeasuringPointComments from "./MeasuringPointComments";
import { NotebookContext } from "../Notebook.context";
import { useContext, useEffect, useState } from "react";
import { constructImageStorageUrl } from "../utils";
import CroppedImageDisplay from "./CroppedImageDisplay";
import { getToken } from "../../../../shared/js/jwt";
import MeasuringPointObjectGroup from "./MeasuringPointObjectGroup";
import MeasuringPointSegmentedControl, {
  MeasuringPointType,
} from "./MeasuringPointSegmentedControl";
import MeasuringPointStandard from "./MeasuringPointStandard";
import {
  addOrUpdateStandardToMeasuringPoint,
  deleteMeasuringPointStandard,
} from "../../../../standard/assets/js/standard-services";
import { IMeasuringPointStandard } from "../../../../standard/assets/js/IStandard";

const buttonContainerStyle = css({
  border: "dashed var(--background-action-high-blue-france) 1px",
  width: "100%",
  height: "100%",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  padding: "1rem",
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
  measuringPointStandard,
}: {
  point: IMeasuringPoint;
  runObjectGroups: RunObjectGroup[];
  runId: string;
  measuringPointStandard?: IMeasuringPointStandard;
  onAddObjectClicked: (event: React.MouseEvent<HTMLButtonElement>) => void;
  onLocalizeImageClicked: (event: React.MouseEvent<HTMLButtonElement>) => void;
}) {
  const t = {
    disabledTooltip: window.gettext(
      "Unset the object group or standard to change the analysis type",
    ),
  };
  const { updatedMeasuringPointStandard } = useContext(NotebookContext);

  const [selectedMeasuringPointType, setSelectedMeasuringPointType] =
    useState<MeasuringPointType>("objectGroup");

  useEffect(() => {
    if (!point.objectGroupId && measuringPointStandard) {
      setSelectedMeasuringPointType("standard");
    }
  }, [point.objectGroupId, measuringPointStandard]);

  const onStandardChange = (selectedStandard: string | null) => {
    let promise: Promise<void | IMeasuringPointStandard> | null = null;
    if (selectedStandard) {
      promise = addOrUpdateStandardToMeasuringPoint(
        selectedStandard,
        point.id,
        !measuringPointStandard,
      );
    } else if (measuringPointStandard) {
      promise = deleteMeasuringPointStandard(point.id);
    }
    if (promise) {
      promise.then((result) =>
        updatedMeasuringPointStandard(point.id, result || undefined),
      );
    }
  };

  return (
    <div className="fr-container--fluid">
      <MeasuringPointSegmentedControl
        selectedType={selectedMeasuringPointType}
        onTypeSelect={(type) => setSelectedMeasuringPointType(type)}
        className="fr-mb-2w"
        disabled={!!point.objectGroupId || !!measuringPointStandard}
        aria-describedby="tooltip-2989"
      />
      {(!!point.objectGroupId || !!measuringPointStandard) && (
        <span
          className="fr-tooltip fr-placement"
          id="tooltip-2989"
          role="tooltip"
          aria-hidden="true"
        >
          {t.disabledTooltip}
        </span>
      )}
      <div className="fr-grid-row fr-grid-row--gutters">
        <div className="fr-col-12 fr-col-md-5">
          {selectedMeasuringPointType === "objectGroup" && (
            <MeasuringPointImageTile
              point={point}
              onLocalizeImageClicked={onLocalizeImageClicked}
            />
          )}
        </div>
        <div className="fr-col-12 fr-col-md-7">
          {selectedMeasuringPointType === "standard" ? (
            <MeasuringPointStandard
              standard={measuringPointStandard?.standard.label || null}
              onStandardChange={onStandardChange}
            />
          ) : (
            <MeasuringPointObjectGroup
              runObjectGroups={runObjectGroups}
              point={point}
              onAddObjectClicked={onAddObjectClicked}
            />
          )}
          <MeasuringPointComments pointId={point.id} value={point.comments} />
        </div>
      </div>
    </div>
  );
}

interface IMeasuringPointImageTileProps {
  point: IMeasuringPoint;
  onLocalizeImageClicked: (event: React.MouseEvent<HTMLButtonElement>) => void;
}
function MeasuringPointImageTile({
  point,
  onLocalizeImageClicked,
}: IMeasuringPointImageTileProps) {
  const t = {
    localizeOnObject: window.gettext("Locate point on image"),
    changeLocation: window.gettext("Edit point location on image"),
  };

  const image = point.image;

  const { imageStorage } = useContext(NotebookContext);

  const [imageUrl, setImageUrl] = useState<string | null>(null);

  useEffect(() => {
    if (image && imageStorage) {
      getToken(true).then((token) => {
        setImageUrl(
          constructImageStorageUrl(
            image.runObjectGroupImage.path,
            imageStorage.baseUrl,
            imageStorage.token,
            token,
          ),
        );
      });
    } else if (imageUrl) {
      setImageUrl(null);
    }
  }, [imageStorage, point.id, point.image]);

  return (
    <div css={imageContainerStyle}>
      {imageUrl ? (
        <div css={{ position: "relative" }}>
          <button
            className="fr-btn fr-icon-edit-line fr-btn--icon fr-btn--secondary fr-background-default--grey"
            aria-controls="add-measuring-point-image-modal"
            onClick={onLocalizeImageClicked}
            data-fr-opened={false}
            css={{ position: "absolute", top: 5, right: 5, zIndex: 2 }}
          >
            {t.changeLocation}
          </button>
          <CroppedImageDisplay
            css={{ maxWidth: "100%" }}
            src={imageUrl}
            transform={image?.runObjectGroupImage.transform}
            measuringPoints={[point]}
            showNames={false}
          />
        </div>
      ) : (
        <div css={buttonContainerStyle}>
          <button
            className="fr-btn fr-icon-image-add-line fr-btn--secondary fr-btn--icon-left"
            aria-controls="add-measuring-point-image-modal"
            data-fr-opened={false}
            onClick={onLocalizeImageClicked}
          >
            {t.localizeOnObject}
          </button>
        </div>
      )}
    </div>
  );
}
