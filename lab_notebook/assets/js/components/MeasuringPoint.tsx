import { css } from "@emotion/react";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import type { IMeasuringPoint, IMeasuringPointImage } from "../IMeasuringPoint";
import MeasuringPointComments from "./MeasuringPointComments";
import ObjectSelect from "./ObjectSelect";
import ImageMeasuringPointer from "./ImageMeasuringPointer";
import { NotebookContext } from "../Notebook.context";
import { useContext } from "react";
import { constructImageStorageUrl } from "../utils";

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
  };
  return (
    <div className="fr-container--fluid">
      <div className="fr-grid-row fr-grid-row--gutters">
        <div className="fr-col-12 fr-col-md-5">
          <MeasuringPointImageTile
            image={point.image}
            onLocalizeImageClicked={onLocalizeImageClicked}
          />
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
          <MeasuringPointComments pointId={point.id} value={point.comments} />
        </div>
      </div>
    </div>
  );
}

interface IMeasuringPointImageTileProps {
  image?: IMeasuringPointImage;
  onLocalizeImageClicked: (event: React.MouseEvent<HTMLButtonElement>) => void;
}
function MeasuringPointImageTile({
  image,
  onLocalizeImageClicked,
}: IMeasuringPointImageTileProps) {
  const t = {
    localizeOnObject: window.gettext("Locate point on image"),
    changeLocation: window.gettext("Edit point location on image"),
  };

  const { imageStorage } = useContext(NotebookContext);

  let imageUrl: string | null = null;

  if (image && imageStorage) {
    imageUrl = constructImageStorageUrl(
      image.runObjectGroupImage.path,
      imageStorage.baseUrl,
      imageStorage.token,
    );
  }
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
          <ImageMeasuringPointer
            src={imageUrl}
            transform={image?.runObjectGroupImage.transform}
            initialLocation={image?.pointLocation}
            isReadonly={true}
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
