import { useEffect, useState } from "react";
import { IImageTransform } from "../IImageTransform";
import ImageLoading from "./ImageLoading";
import { css } from "@emotion/react";
import { IMeasuringPoint } from "../IMeasuringPoint";
import ImageWithMeasuringPoints from "./ImageWithMeasuringPoints";

const visiblePlaceholderStyle = css({
  position: "absolute",
  top: 0,
  left: 0,
  zIndex: 99,
});

export default function CroppedImageDisplay({
  src,
  transform,
  className,
  measuringPoints,
  showNames,
  ...props
}: {
  transform?: IImageTransform | null;
  measuringPoints: IMeasuringPoint[];
  showNames?: boolean;
} & Omit<React.HTMLProps<HTMLImageElement>, "src"> & { src: string }) {
  const [dataURL, setDataURL] = useState<string>();
  const [isReady, setIsReady] = useState(false);

  const handleImageLoaded = () => {
    setIsReady(true);
  };

  useEffect(() => {
    // Reset dataURL when src or transform changes
    if (dataURL) setDataURL(undefined);
  }, [src, transform]);

  return (
    <div className={className}>
      <ImageWithMeasuringPoints
        src={src}
        imageTransform={transform}
        measuringPoints={measuringPoints.map((p) => ({
          pointLocation: p.image?.pointLocation,
          name: p.name,
        }))}
        showNames={showNames}
        onImageLoaded={handleImageLoaded}
        css={{ visibility: isReady ? "visible" : "hidden" }}
        {...props}
      />
      {!isReady && <ImageLoading css={visiblePlaceholderStyle} />}
    </div>
  );
}
