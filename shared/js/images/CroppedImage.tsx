import { useEffect, useState } from "react";
import { Interpolation, Theme } from "@emotion/react";

import { IImageTransform } from "./types";

interface ICroppedImageProps extends React.HTMLProps<HTMLImageElement> {
  src: string;
  imageTransform?: IImageTransform | null;
  css?: Interpolation<Theme>;
  onImageLoaded?: (image: HTMLImageElement) => void;
  children?: React.ReactNode;
}

export default function CroppedImage({
  src,
  imageTransform,
  className,
  css,
  onImageLoaded,
  children,
}: ICroppedImageProps) {
  const [imageHeight, setImageHeight] = useState(imageTransform?.height || 100);
  const [imageWidth, setImageWidth] = useState(imageTransform?.width || 100);

  useEffect(() => {
    const image = new Image();
    image.addEventListener("load", () => {
      setImageWidth(image.naturalWidth);
      setImageHeight(image.naturalHeight);
      onImageLoaded?.(image);
    });
    image.src = src;
  }, [src]);

  const viewBox = imageTransform
    ? `${imageTransform.x} ${imageTransform.y} ${imageTransform.width} ${imageTransform.height}`
    : `0 0 ${imageWidth} ${imageHeight}`;

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={viewBox}
      className={className}
      css={css}
    >
      <image href={src} width={imageWidth} height={imageHeight} />
      {children}
    </svg>
  );
}
