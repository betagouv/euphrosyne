import { useEffect, useRef } from "react";
import { IImageTransform } from "../IImageTransform";

import CropperCanvas from "@cropper/element-canvas";
import CropperImage from "@cropper/element-image";
import CropperHandle from "@cropper/element-handle";
import CropperShade from "@cropper/element-shade";
import CropperSelection from "@cropper/element-selection";
import CropperGrid from "@cropper/element-grid";
import CropperCrosshair from "@cropper/element-crosshair";
import { CopperSelectionChangeEvent } from "../../../../typescript/cropper";

CropperCanvas.$define();
CropperImage.$define();
CropperHandle.$define();
CropperShade.$define();
CropperSelection.$define();
CropperGrid.$define();
CropperCrosshair.$define();

interface IImageCropperProps extends React.HTMLProps<HTMLImageElement> {
  transform?: IImageTransform | null;
  readonly?: boolean;
  onCrop?: (event: CopperSelectionChangeEvent) => void;
  onReady?: () => void;
}

export default function ImageCropper({
  readonly = false,
  transform,
  onCrop,
  onReady,
  ...props
}: IImageCropperProps) {
  const cropperSelectionRef = useRef<CropperSelection>(null);
  const cropperImageRef = useRef<CropperImage>(null);

  useEffect(() => {
    if (cropperSelectionRef.current) {
      cropperSelectionRef.current.addEventListener(
        "change",
        (event: CopperSelectionChangeEvent) => {
          onCrop?.(event);
        },
      );
    }
  }, []);

  useEffect(() => {
    if (cropperImageRef.current) {
      cropperImageRef.current.$ready(() => {
        onReady?.();
      });
    }
  }, []);

  return (
    <cropper-canvas background style={{ width: "100%", height: "100%" }}>
      <cropper-image
        src={props.src}
        ref={cropperImageRef}
        rotatable={!readonly}
        scalable={!readonly}
        skewable={!readonly}
        translatable={!readonly}
        initial-center-size="cover"
        onLoad={() => {
          onReady?.();
        }}
        css={{ width: "100%" }}
      ></cropper-image>
      <cropper-shade hidden></cropper-shade>
      <cropper-handle action="move" plain></cropper-handle>
      <cropper-selection
        initial-coverage="0.5"
        movable
        resizable
        {...transform}
        ref={cropperSelectionRef}
      >
        <cropper-grid role="grid" covered></cropper-grid>
        <cropper-crosshair centered></cropper-crosshair>
        <cropper-handle
          action="move"
          theme-color="rgba(255, 255, 255, 0.35)"
        ></cropper-handle>
        <cropper-handle action="n-resize"></cropper-handle>
        <cropper-handle action="e-resize"></cropper-handle>
        <cropper-handle action="s-resize"></cropper-handle>
        <cropper-handle action="w-resize"></cropper-handle>
        <cropper-handle action="ne-resize"></cropper-handle>
        <cropper-handle action="nw-resize"></cropper-handle>
        <cropper-handle action="se-resize"></cropper-handle>
        <cropper-handle action="sw-resize"></cropper-handle>
      </cropper-selection>
    </cropper-canvas>
  );
}
