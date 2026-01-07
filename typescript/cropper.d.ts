// TypeScript declaration file for custom elements used in a cropper component
// Thanks https://github.com/INFCode/cropper-v2-test/blob/5f81c2010fe258c4eb46aa66e9927306b7d30048/src/types/cropper.d.ts

import React, { RefObject } from "react";

import { IImageTransform } from "../shared/js/images/types";
import CropperSelection from "@cropper/element-selection";
import CropperImage from "@cropper/element-image";

type CopperSelectionChangeEvent = CustomEventInit<
  IImageTransform & { matrix: string }
>;

// Export the types so they can be imported
export interface CropperCanvas extends HTMLElement {
  getBoundingClientRect(): DOMRect;
  appendChild<T extends Node>(node: T): T;
  removeChild<T extends Node>(node: T): T;
}

export interface CropperCanvasAttributes {
  background?: boolean;
  key?: string | number;
  ref?: RefObject<CropperCanvas>;
  // Add children support
  children?: React.ReactNode;
  // Add all the common HTML attributes that might be used
  class?: string;
  style?: React.CSSProperties;
  id?: string;
}

export interface CropperImageAttributes {
  src?: string;
  alt?: string;
  rotatable?: boolean;
  scalable?: boolean;
  skewable?: boolean;
  translatable?: boolean;
  onTransform?: (event: CustomEvent) => void;
  ref?: RefObject<CropperImage | null>;
  // Add children support
  children?: React.ReactNode | string | number | boolean | null;
  // Add all the common HTML attributes that might be used
  class?: string;
  style?: React.CSSProperties;
  id?: string;
  onLoad?: React.ReactEventHandler<HTMLImageElement>;
}

export interface CropperHandleAttributes {
  action?: string;
  plain?: boolean;
  "theme-color"?: string;
  // Add children support
  children?: React.ReactNode | string | number | boolean | null;
  // Add all the common HTML attributes that might be used
  class?: string;
  style?: React.CSSProperties;
  id?: string;
}

export interface CropperShadeAttributes {
  hidden?: boolean;
  // Add children support
  children?: React.ReactNode | string | number | boolean | null;
  // Add all the common HTML attributes that might be used
  class?: string;
  style?: React.CSSProperties;
  id?: string;
}

export interface CropperSelectionAttributes {
  "initial-coverage"?: string;
  dynamic?: boolean;
  movable?: boolean;
  resizable?: boolean;
  zoomable?: boolean;
  precise?: boolean;
  // Add children support
  children?: React.ReactNode | string | number | boolean | null;
  // Add all the common HTML attributes that might be used
  class?: string;
  style?: React.CSSProperties;
  id?: string;
  ref?: RefObject<CropperSelection | null>;
}

export interface CropperGridAttributes {
  role?: string;
  covered?: boolean;
  // Add children support
  children?: React.ReactNode | string | number | boolean | null;
  // Add all the common HTML attributes that might be used
  class?: string;
  style?: React.CSSProperties;
  id?: string;
}

export interface CropperCrosshairAttributes {
  centered?: boolean;
  // Add children support
  children?: React.ReactNode | string | number | boolean | null;
  // Add all the common HTML attributes that might be used
  class?: string;
  style?: React.CSSProperties;
  id?: string;
}
