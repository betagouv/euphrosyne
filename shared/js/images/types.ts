import { ExternalObjectProvider } from "../../../lab/objects/assets/js/types";

export type ImageProvider = "euphrosyne" | ExternalObjectProvider;

export interface IImageTransform {
  x: number;
  y: number;
  width: number;
  height: number;
  rotate: number;
  scaleX: number;
  scaleY: number;
}

export interface IImagewithUrl {
  url: string;
  provider: ImageProvider;
  transform?: IImageTransform | null;
}

export interface IRunObjectImage {
  id?: number;
  path: string;
  transform?: IImageTransform | null;
}

export interface IRunObjectImageWithUrl
  extends IImagewithUrl, IRunObjectImage {}

export interface IPointLocation {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface IMeasuringPoint {
  id: number;
  name: string;
  objectGroupId: number | null;
  comments: string | null;
  image?: IMeasuringPointImage;
}

export interface IMeasuringPointImage {
  id: number;
  runObjectGroupImage: IRunObjectImage;
  pointLocation: IPointLocation;
}
