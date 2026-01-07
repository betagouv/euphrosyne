import {
  IImageTransform,
  IPointLocation,
} from "../../../../shared/js/images/types";
import { useEffect, useRef, useState, useCallback } from "react";
import SegmentedSelectMode, { SelectionMode } from "./SegmentedSelectMode";
import { css } from "@emotion/react";
import CropperCanvas from "@cropper/element-canvas";
import CropperImage from "@cropper/element-image";
import CropperHandle from "@cropper/element-handle";
import CropperShade from "@cropper/element-shade";
import CropperSelection from "@cropper/element-selection";
import CropperGrid from "@cropper/element-grid";
import CropperCrosshair from "@cropper/element-crosshair";
import { cropImage } from "../crop";

CropperCanvas.$define();
CropperImage.$define();
CropperHandle.$define();
CropperShade.$define();
CropperSelection.$define();
CropperGrid.$define();
CropperCrosshair.$define();

interface IImageCropperProps
  extends Omit<React.HTMLProps<HTMLImageElement>, "src"> {
  src: string;
  transform?: IImageTransform | null;
  initialLocation?: IPointLocation;
  maxHeight?: string;
  onLocate?: (data: IPointLocation) => void;
}

const onTopStyle = css({
  position: "absolute",
  top: "10px",
  right: "10px",
  zIndex: 1,
});

// Calculate the selection coordinates based on the cropper image and selection
const getSelectionCoordinates = (
  cropperImage: CropperImage,
  cropperSelection: CropperSelection,
): IPointLocation => {
  // convert image matrix to image crop data (x,y,scale,rotate)
  const matrix = cropperImage.$getTransform();
  const imageActualWidth = cropperImage.$image.width * matrix[0];
  const imageActualHeight = cropperImage.$image.height * matrix[3];
  const imageActualX =
    matrix[4] + (cropperImage.$image.width - imageActualWidth) / 2;
  const imageActualY =
    matrix[5] + (cropperImage.$image.height - imageActualHeight) / 2;

  // convert selection to actual image dimensions
  const scaleX = imageActualWidth / cropperImage.$image.width;
  const scaleY = imageActualHeight / cropperImage.$image.height;
  const x = (cropperSelection.x - imageActualX) / scaleX;
  const y = (cropperSelection.y - imageActualY) / scaleY;
  const width = Math.ceil(cropperSelection.width / scaleX);
  const height = Math.ceil(cropperSelection.height / scaleY);

  return { x, y, width, height };
};

export default function ImageMeasuringPointer({
  src,
  transform,
  initialLocation,
  onLocate,
}: IImageCropperProps) {
  const [croppedSrc, setCroppedSrc] = useState<string | null>(null);

  const cropperSelectionRef = useRef<CropperSelection>(null);
  const cropperImageRef = useRef<CropperImage>(null);

  const initalSelectionMode: SelectionMode =
    initialLocation &&
    Math.min(initialLocation.width, initialLocation.height) !== 0
      ? "area"
      : "point";
  const [selectionMode, seSelectionMode] =
    useState<SelectionMode>(initalSelectionMode);

  const changeSelectionForMode = (mode: SelectionMode) => {
    if (mode === "point") {
      cropperSelectionRef.current?.$change(0, 0, 0, 0);
      cropperSelectionRef.current?.$center();
    } else {
      cropperSelectionRef.current?.$reset();
    }
  };

  const handleSelectionChange = useCallback(() => {
    const imageRef = cropperImageRef.current,
      selectionRef = cropperSelectionRef.current;
    if (!imageRef || !selectionRef) {
      console.warn("Image or selection reference is not available.");
      return;
    }
    const coordinates = getSelectionCoordinates(imageRef, selectionRef);
    onLocate?.(coordinates);
  }, [onLocate]);

  const handleSelectionModeChange = (mode: SelectionMode) => {
    seSelectionMode(mode);
    changeSelectionForMode(mode);
  };

  useEffect(() => {
    // Initialize the image by cropping it if necessary.
    cropImage(src, transform || null).then(setCroppedSrc);
  }, []);

  useEffect(() => {
    // Initialize the cropper selection on the UI.
    if (croppedSrc && cropperSelectionRef.current) {
      changeSelectionForMode(selectionMode);
    }
  }, [croppedSrc, cropperSelectionRef.current]);

  useEffect(() => {
    // Add an event listener to the cropper selection for changes.
    const ref = cropperSelectionRef.current;
    if (!ref) return;
    ref.addEventListener("change", handleSelectionChange);
    return () => {
      ref.removeEventListener("change", handleSelectionChange);
    };
  }, []);

  useEffect(() => {
    // Add an event listener to the image to recalculate the selection coordinates.
    const imageRef = cropperImageRef.current;
    if (!imageRef) return;
    imageRef.addEventListener("transform", handleSelectionChange);
    return () => {
      imageRef.removeEventListener("transform", handleSelectionChange);
    };
  }, [cropperImageRef, croppedSrc, handleSelectionChange]);

  return (
    <div css={{ position: "relative", height: "100%" }}>
      <SegmentedSelectMode
        selectedMode={selectionMode}
        onModeSelect={handleSelectionModeChange}
        css={onTopStyle}
      />
      <cropper-canvas background style={{ width: "100%", height: "100%" }}>
        {croppedSrc && (
          <cropper-image
            src={croppedSrc}
            ref={cropperImageRef}
            scalable
            translatable
            initial-center-size="cover"
          ></cropper-image>
        )}
        <cropper-shade hidden></cropper-shade>
        <cropper-handle action="move" plain></cropper-handle>
        <cropper-selection
          ref={cropperSelectionRef}
          initial-coverage="0.5"
          movable
          resizable={selectionMode !== "point"}
          precise={true}
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
    </div>
  );
}
