import { useEffect, useState } from "react";
import { IImageTransform } from "../IImageTransform";
import { IPointLocation } from "../IImagePointLocation";
import { Interpolation, Theme } from "@emotion/react";

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
}

export default function ImageWithMeasuringPoints({
  src,
  imageTransform,
  className,
  measuringPoints,
  showNames = true,
  css,
}: IImageWithMeasuringPointsProps & React.HTMLProps<HTMLElement>) {
  const [height, setHeight] = useState(imageTransform?.height || 100);
  const [width, setWidth] = useState(imageTransform?.width || 100);
  const aspectRatio = width / height;

  useEffect(() => {
    if (!imageTransform) {
      const i = new Image();
      i.addEventListener("load", () => {
        setWidth(i.naturalWidth);
        setHeight(i.naturalHeight);
      });
      i.src = src;
    }
  }, [src, imageTransform]);

  const widthRatio = width / 100;
  const heightRatio = height / 100;

  const locationToRelativeLocation = ({
    x,
    y,
    width,
    height,
  }: IPointLocation) => ({
    rlvX: x / widthRatio,
    rlvY: y / heightRatio / aspectRatio,
    rlvWidth: width / widthRatio,
    rlvHeight: height / heightRatio,
  });

  const rectProps = {
    fill: "none",
    strokeWidth: "0.3px",
    stroke: "red",
  };

  const circleRadius = 0.7;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 100 100`}
      className={className}
      css={css}
    >
      <image href={src} width={100} />
      {measuringPoints.map(({ pointLocation, name }) => {
        const id = `${pointLocation?.x}-${pointLocation?.y}`;
        const relativeLocation = pointLocation
          ? locationToRelativeLocation(pointLocation)
          : null;
        return (
          relativeLocation && (
            <g key={`point-${id}`}>
              {showNames && (
                <svg
                  x={relativeLocation.rlvX + 1.8}
                  y={relativeLocation.rlvY - 5}
                >
                  <g>
                    <rect
                      x={0}
                      y={0}
                      width={name.length * 2}
                      height={3.7}
                      fill="white"
                    ></rect>
                    <text x={0.3} y={2.9} css={{ fontSize: "3px" }}>
                      {name}
                    </text>
                  </g>
                </svg>
              )}
              {relativeLocation.rlvWidth && relativeLocation.rlvHeight ? (
                <rect
                  x={relativeLocation.rlvX}
                  y={relativeLocation.rlvY}
                  width={relativeLocation.rlvWidth}
                  height={relativeLocation.rlvHeight / aspectRatio}
                  {...rectProps}
                />
              ) : (
                <circle
                  cx={relativeLocation.rlvX - circleRadius / 2}
                  cy={relativeLocation.rlvY - circleRadius / 2}
                  r={`${circleRadius}px`}
                  fill="red"
                />
              )}
              ,
            </g>
          )
        );
      })}
    </svg>
  );
}
