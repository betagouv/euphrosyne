import { Fragment, HTMLProps, useEffect, useId, useRef, useState } from "react";
import Cropper from "cropperjs";

import "cropperjs/dist/cropper.css";
import { IImageTransform } from "../IImageTransform";
import { css } from "@emotion/react";
import ImageLoading from "./ImageLoading";
import { IPointLocation } from "../IImagePointLocation";

const selectionModes = ["point", "area"] as const;
type SelectionMode = (typeof selectionModes)[number];

const onTopStyle = css({
  position: "absolute",
  top: "10px",
  right: "10px",
  zIndex: 1,
});

const visiblePlaceholderStyle = css({
  position: "absolute",
  top: 0,
  left: 0,
  zIndex: 2,
  backgroundColor: "white",
});

const hiddenPlaceholderStyle = css({
  display: "none",
});

interface IImageCropperProps extends React.HTMLProps<HTMLImageElement> {
  transform?: IImageTransform | null;
  initialLocation?: IPointLocation;
  isReadonly?: boolean;
  maxHeight?: string;
  onLocate?: (data: IPointLocation) => void;
  onReady?: (event: Cropper.ReadyEvent<HTMLImageElement>) => void;
}

export default function ImageMeasuringPointer({
  transform,
  onLocate,
  onReady,
  initialLocation,
  maxHeight,
  isReadonly = false,
  ...props
}: IImageCropperProps) {
  const [isReady, setIsReady] = useState(false);
  const originalImageRef = useRef<HTMLImageElement>(null);
  const croppedImageRef = useRef<HTMLImageElement>(null);

  const [croppedDataUrl, setCroppedDataUrl] = useState<string | null>();

  const initalSelectionMode: SelectionMode =
    initialLocation &&
    Math.min(initialLocation.width, initialLocation.height) !== 0
      ? "area"
      : "point";
  const [selectionMode, seSelectiontMode] =
    useState<SelectionMode>(initalSelectionMode);
  const selectionModeRef = useRef<SelectionMode>();
  selectionModeRef.current = selectionMode;

  const [cropper, setCropper] = useState<Cropper>();
  const cropperRef = useRef<Cropper>();
  cropperRef.current = cropper;

  const setCropperData = (_cropper: Cropper, _mode: SelectionMode) => {
    if (!cropperRef.current) return;
    if (_mode === "point") {
      const { naturalHeight, naturalWidth } = _cropper.getImageData();
      _cropper.setData({
        x: naturalWidth / 2,
        y: naturalHeight / 2,
        width: 0,
        height: 0,
      });
    } else _cropper.reset();
  };

  const initWithInitialLocation = (
    _cropper: Cropper,
    location: IPointLocation,
  ) => {
    _cropper.setData(location);
  };

  // INIT ORIGINAL (to crop image)
  useEffect(() => {
    if (originalImageRef.current) {
      const _cropper = new Cropper(originalImageRef.current, {
        viewMode: 1,
        ready: () => {
          if (transform) {
            _cropper.setData(transform);
          }
          setCroppedDataUrl(_cropper.getCroppedCanvas().toDataURL());
        },
      });
      _cropper.disable();
    }
  }, [props.src, JSON.stringify(transform)]);

  // INIT CROPPED
  useEffect(() => {
    if (croppedDataUrl && croppedImageRef.current) {
      const _cropper = new Cropper(croppedImageRef.current, {
        viewMode: 1,
        dragMode: "move",
        minContainerHeight: 300,
        autoCropArea: 0.5,
        cropBoxMovable: false,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
        crop: (event: Cropper.CropEvent<HTMLImageElement>) => {
          const { width, height, x, y } = event.detail;
          onLocate && onLocate({ width, height, x, y });
        },
        ready: (event: Cropper.ReadyEvent<HTMLImageElement>) => {
          initialLocation
            ? initWithInitialLocation(_cropper, initialLocation)
            : setCropperData(_cropper, selectionMode);
          if (isReadonly) _cropper.disable();
          setIsReady(true);
          onReady && onReady(event);
        },
      });
      setCropper(_cropper);
    }
  }, [croppedDataUrl]);

  useEffect(() => {
    if (cropperRef.current && initialLocation) {
      cropperRef.current.enable();
      initWithInitialLocation(cropperRef.current, initialLocation);
      cropperRef.current.disable();
    }
  }, [initialLocation]);

  // MODE SELECTION
  useEffect(() => {
    if (!cropperRef.current) return;
    setCropperData(cropperRef.current, selectionMode);
  }, [selectionMode]);

  return (
    <Fragment>
      <div css={{ position: "relative" }}>
        <ImageLoading
          css={isReady ? hiddenPlaceholderStyle : visiblePlaceholderStyle}
          spinningRadius={10}
        />
        {isReady && !isReadonly && (
          <SegmentedSelectMode
            selectedMode={selectionMode}
            onModeSelect={(mode) => seSelectiontMode(mode)}
            css={onTopStyle}
          />
        )}

        <img
          src={croppedDataUrl || ""}
          ref={croppedImageRef}
          css={{ maxWidth: "100%", maxHeight }}
        />
      </div>
      {!croppedDataUrl && (
        <div>
          <img {...props} ref={originalImageRef} css={{ maxWidth: "100%" }} />
        </div>
      )}
    </Fragment>
  );
}

interface ISgementedSelectModeProps {
  selectedMode: SelectionMode;
  onModeSelect: (mode: SelectionMode) => void;
}
function SegmentedSelectMode({
  selectedMode,
  onModeSelect,
  className,
  ...props
}: ISgementedSelectModeProps & HTMLProps<HTMLFieldSetElement>) {
  const t = {
    point: window.gettext("Point"),
    area: window.gettext("Area"),
    legend: window.gettext("Selection mode"),
  };
  const _id = useId();

  const modeDisplay = {
    point: {
      iconClass: "fr-icon-cursor-line",
    },
    area: {
      iconClass: "fr-icon-layout-grid-line",
    },
  };
  return (
    <fieldset
      className={`fr-segmented fr-segmented--no-legend ${className}`}
      {...props}
    >
      <legend className="fr-segmented__legend">{t.legend}</legend>
      <div className="fr-segmented__elements">
        {selectionModes.map((mode) => (
          <div
            className="fr-segmented__element fr-background-default--grey"
            key={`segmented-${mode}`}
          >
            <input
              checked={selectedMode === mode}
              type="radio"
              id={`segmented-${_id}-${mode}`}
              onClick={() => {
                onModeSelect(mode);
              }}
              readOnly={true}
            />
            <label
              className={`fr-label ${modeDisplay[mode].iconClass}`}
              htmlFor={`segmented-${_id}-${mode}`}
            >
              {t[mode]}
            </label>
          </div>
        ))}
      </div>
    </fieldset>
  );
}
