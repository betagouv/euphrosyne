import { IPointLocation } from "./IImagePointLocation";
import { IRunObjectImage } from "./IImageTransform";

export interface IMeasuringPoint {
  id: string;
  name: string;
  objectGroupId: string | null;
  comments: string | null;
  image?: IMeasuringPointImage;
}

export interface IMeasuringPointImage {
  id: string;
  runObjectGroupImage: IRunObjectImage;
  pointLocation: IPointLocation;
}
