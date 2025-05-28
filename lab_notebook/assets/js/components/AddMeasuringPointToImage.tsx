import { IPointLocation } from "../IImagePointLocation";
import type { IRunObjectImageWithUrl } from "../IImageTransform";
import { IMeasuringPoint } from "../IMeasuringPoint";
import ImageMeasuringPointer from "./ImageMeasuringPointer";

export default function AddMeasuringPointToImage({
  runObjectImage,
  onLocate,
  measuringPoint,
}: {
  runObjectImage: IRunObjectImageWithUrl;
  measuringPoint?: IMeasuringPoint;
  onLocate?: (data: IPointLocation) => void;
}) {
  const t = {
    helpText: window.gettext(
      "Move and zoom the image to select the measurement point or zone. Switch between point and area selection using the buttons located at the top left of the image.",
    ),
  };
  return (
    <div>
      <p className="fr-text--sm">{t.helpText}</p>
      <div style={{ width: "100%", aspectRatio: "16 / 9" }}>
        <ImageMeasuringPointer
          src={runObjectImage.url}
          transform={runObjectImage.transform}
          onLocate={onLocate}
          initialLocation={measuringPoint?.image?.pointLocation}
        />
      </div>
    </div>
  );
}
