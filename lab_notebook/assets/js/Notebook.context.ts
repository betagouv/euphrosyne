import { createContext, Dispatch, SetStateAction, useState } from "react";
import { IMeasuringPoint, IMeasuringPointImage } from "./IMeasuringPoint";

interface ImageStorage {
  baseUrl: string;
  token: string;
}

export interface INotebookContext {
  projectSlug: string;
  runId: string;
  imageStorage?: ImageStorage;
  measuringPoints: IMeasuringPoint[];
  setMeasuringPoints: Dispatch<SetStateAction<IMeasuringPoint[]>>;
  addObjectToMeasuringPoint: (
    measuringPointId: string,
    objectGroupId: string,
  ) => void;
  updateMeasuringPointImage: (
    measuringPointId: string,
    image?: IMeasuringPointImage,
  ) => void;
  setImageStorage: Dispatch<SetStateAction<ImageStorage | undefined>>;
}

export const NotebookContext = createContext<INotebookContext>({
  projectSlug: "",
  runId: "",
  measuringPoints: [],
  addObjectToMeasuringPoint: () => {},
  setMeasuringPoints: () => {},
  setImageStorage: () => {},
  updateMeasuringPointImage: () => {},
});

export function useNotebookContext(
  projectSlug: string,
  runId: string,
): INotebookContext {
  const [imageStorage, setImageStorage] = useState<ImageStorage>();
  const [measuringPoints, setMeasuringPoints] = useState<IMeasuringPoint[]>([]);

  const addObjectToMeasuringPoint = (
    measuringPointId: string,
    objectGroupId: string,
  ) => {
    setMeasuringPoints(
      measuringPoints.map((p) =>
        p.id === measuringPointId ? { ...p, objectGroupId } : p,
      ),
    );
  };

  const updateMeasuringPointImage = (
    measuringPointId: string,
    image?: IMeasuringPointImage,
  ) => {
    setMeasuringPoints(
      measuringPoints.map((p) =>
        p.id === measuringPointId ? { ...p, image } : p,
      ),
    );
  };

  return {
    projectSlug,
    runId,
    imageStorage,
    setImageStorage,
    measuringPoints,
    setMeasuringPoints,
    addObjectToMeasuringPoint,
    updateMeasuringPointImage,
  };
}
