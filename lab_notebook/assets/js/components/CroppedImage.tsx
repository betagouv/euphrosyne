import { useEffect, useState } from "react";
import { IImageTransform } from "../IImageTransform";
import { Interpolation, Theme } from "@emotion/react";

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
    const i = new Image();
    i.addEventListener("load", () => {
      setImageWidth(i.naturalWidth);
      setImageHeight(i.naturalHeight);
      onImageLoaded?.(i);
    });
    i.src = src;
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
