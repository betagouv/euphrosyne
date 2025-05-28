import { useCallback, useState } from "react";
import { IImageTransform } from "../IImageTransform";
import { IPointLocation } from "../IImagePointLocation";
import { Interpolation, Theme } from "@emotion/react";
import CroppedImage from "./CroppedImage";

interface IMeasuringPoint {
  name: string;
  pointLocation?: IPointLocation;
}

interface IImageWithMeasuringPointsProps {
  src: string;
  imageTransform?: IImageTransform | null;
  measuringPoints: IMeasuringPoint[];
  showNames?: boolean;
  css?: Interpolation<Theme>;
  onImageLoaded?: () => void;
}

export default function ImageWithMeasuringPoints({
  src,
  imageTransform,
  className,
  measuringPoints,
  showNames = true,
  onImageLoaded,
}: IImageWithMeasuringPointsProps & React.HTMLProps<HTMLElement>) {
  const [imageHeight, setImageHeight] = useState(imageTransform?.height || 100);
  const [imageWidth, setImageWidth] = useState(imageTransform?.width || 100);
  const aspectRatio = imageWidth / imageHeight;

  const handleImageLoaded = useCallback(
    (image: HTMLImageElement) => {
      setImageWidth(image.naturalWidth);
      setImageHeight(image.naturalHeight);
      onImageLoaded?.();
    },
    [onImageLoaded],
  );

  const relativeRadius = 0.01; // 1% of image width
  const imageWidthRatio =
    (imageTransform?.width || imageWidth) * relativeRadius;

  return (
    <CroppedImage
      src={src}
      imageTransform={imageTransform}
      className={className}
      onImageLoaded={handleImageLoaded}
    >
      <g
        transform={`translate(${imageTransform?.x || 0}, ${imageTransform?.y || 0})`}
      >
        {measuringPoints.map(({ pointLocation, name }) => {
          const id = `${pointLocation?.x}-${pointLocation?.y}`;
          return (
            pointLocation && (
              <g
                key={`point-${id}`}
                transform={`translate(${pointLocation.x}, ${pointLocation.y})`}
              >
                {showNames && (
                  <g transform={`translate(${pointLocation.width || 0}, 0)`}>
                    <rect
                      x={0.8 * imageWidthRatio}
                      y={0.8 * imageWidthRatio}
                      width={name.length * 3.2 * imageWidthRatio}
                      height={4.7 * imageWidthRatio}
                      fill="#fff"
                      stroke="#222"
                      strokeWidth={0.3 * imageWidthRatio}
                      rx={1.5 * imageWidthRatio}
                      opacity={0.85}
                    ></rect>
                    <text
                      x={2 * imageWidthRatio}
                      y={4.6 * imageWidthRatio}
                      css={{
                        fontSize: 4 * imageWidthRatio + "px",
                        fontWeight: 700,
                        fill: "#222",
                      }}
                      style={{ fontFamily: "monospace", fill: "#222" }}
                    >
                      {name}
                    </text>
                  </g>
                )}
                {pointLocation.width && pointLocation.height ? (
                  <rect
                    x={0}
                    y={0}
                    width={pointLocation.width}
                    height={pointLocation.height / aspectRatio}
                    fill="rgba(255,0,0,0.15)"
                    stroke="#ff3b3b"
                    strokeWidth={0.3 * imageWidthRatio}
                    rx={1.5 * imageWidthRatio}
                    style={{ filter: "drop-shadow(0 0 2px #ff3b3b)" }}
                  />
                ) : (
                  <circle
                    cx={0}
                    cy={0}
                    r={imageWidthRatio * 1.2}
                    fill="#ff3b3b"
                    stroke="#fff"
                    strokeWidth={0.5 * imageWidthRatio}
                    style={{ filter: "drop-shadow(0 0 4px #ff3b3b)" }}
                  />
                )}
              </g>
            )
          );
        })}
      </g>
    </CroppedImage>
  );
}
