import { useEffect, useState } from "react";
import CroppedImage from "./CroppedImage";
import { IImageTransform } from "../IImageTransform";
import ImageLoading from "./ImageLoading";
import { css } from "@emotion/react";
import { IMeasuringPoint } from "../IMeasuringPoint";
import ImageWithMeasuringPoints from "./ImageWithMeasuringPoints";

const visiblePlaceholderStyle = css({
  position: "absolute",
  top: 0,
  left: 0,
});

const hiddenPlaceholderStyle = css({
  display: "none",
});

export default function CroppedImageDisplay({
  transform,
  className,
  measuringPoints,
  showNames,
  ...props
}: {
  transform?: IImageTransform | null;
  measuringPoints: IMeasuringPoint[];
  showNames?: boolean;
} & React.HTMLProps<HTMLImageElement>) {
  const [dataURL, setDataURL] = useState<string>();

  useEffect(() => {
    // Reset dataURL when src or transform changes
    if (dataURL) setDataURL(undefined);
  }, [props.src, transform]);

  return dataURL ? (
    <ImageWithMeasuringPoints
      {...props}
      className={className}
      src={dataURL}
      imageTransform={transform}
      measuringPoints={measuringPoints.map((p) => ({
        pointLocation: p.image?.pointLocation,
        name: p.name,
      }))}
      showNames={showNames}
    />
  ) : (
    <div className={className}>
      <ImageLoading
        css={dataURL ? hiddenPlaceholderStyle : visiblePlaceholderStyle}
      />

      <CroppedImage
        css={{ display: "none" }}
        transform={transform}
        onReady={(url) => {
          setDataURL(url);
        }}
        {...props}
      />
    </div>
  );
}
