import { useEffect, useRef } from "react";
import Cropper from "cropperjs";

import "cropperjs/dist/cropper.css";
import { IImageTransform } from "../IImageTransform";

interface IImageCropperProps extends React.HTMLProps<HTMLImageElement> {
  transform?: IImageTransform | null;
  readonly?: boolean;
  onCrop?: (event: Cropper.CropEvent) => void;
  onReady?: (event: Cropper.ReadyEvent<HTMLImageElement>) => void;
}

export default function ImageCropper({
  readonly = false,
  transform,
  onCrop,
  onReady,
  ...props
}: IImageCropperProps) {
  const croppedImageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (croppedImageRef.current) {
      new Cropper(croppedImageRef.current, {
        checkCrossOrigin: false,
        data: transform || undefined,
        viewMode: 1,
        dragMode: readonly ? "none" : "move",
        guides: !readonly,
        rotatable: !readonly,
        scalable: !readonly,
        zoomable: readonly,
        zoomOnTouch: !readonly,
        zoomOnWheel: !readonly,
        cropBoxMovable: !readonly,
        cropBoxResizable: !readonly,
        minContainerWidth: 140,
        minContainerHeight: 140,
        crop: onCrop,
        ready: onReady,
      });
    }
  }, []);
  return (
    <img
      {...props}
      ref={croppedImageRef}
      css={{ maxWidth: "100%", display: "block" }}
      crossOrigin="anonymous"
    />
  );
}
