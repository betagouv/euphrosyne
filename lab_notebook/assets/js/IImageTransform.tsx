import { ExternalObjectProvider } from "../../../lab/objects/assets/js/types";

export type ImageProvider = "euphrosyne" | ExternalObjectProvider;

export interface IImagewithUrl {
  url: string;
  provider: ImageProvider;
  transform?: IImageTransform | null;
}

export interface IRunObjectImage {
  id?: string;
  path: string;
  transform?: IImageTransform | null;
}

export interface IRunObjectImageWithUrl
  extends IImagewithUrl,
    IRunObjectImage {}

export interface IImageTransform {
  x: number;
  y: number;
  width: number;
  height: number;
  rotate: number;
  scaleX: number;
  scaleY: number;
}
