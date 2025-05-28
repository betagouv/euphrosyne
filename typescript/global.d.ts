import {
  CropperCanvasAttributes,
  CropperCrosshairAttributes,
  CropperGridAttributes,
  CropperHandleAttributes,
  CropperImageAttributes,
  CropperSelectionAttributes,
  CropperShadeAttributes,
} from "./cropper";

declare global {
  interface Window {
    gettext: (text: string) => string;
    interpolate: (text: string, args: string[]) => string;
    dismissAddRelatedObjectGroupPopup?: (win: Window) => void;
  }
}

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      "cropper-canvas": CropperCanvasAttributes;
      "cropper-image": CropperImageAttributes;
      "cropper-handle": CropperHandleAttributes;
      "cropper-shade": CropperShadeAttributes;
      "cropper-selection": CropperSelectionAttributes;
      "cropper-grid": CropperGridAttributes;
      "cropper-crosshair": CropperCrosshairAttributes;
    }
  }
}

export {};
