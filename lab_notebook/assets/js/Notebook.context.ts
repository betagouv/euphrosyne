import { createContext, Dispatch, SetStateAction, useState } from "react";
import { IMeasuringPoint, IMeasuringPointImage } from "./IMeasuringPoint";
import { IStandard } from "../../../standard/assets/js/IStandard";

interface ImageStorage {
  baseUrl: string;
  token: string;
}

export interface INotebookContext {
  projectSlug: string;
  runId: string;
  imageStorage?: ImageStorage;
  setImageStorage: Dispatch<SetStateAction<ImageStorage | undefined>>;
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
  standards: IStandard[];
  setStandards: Dispatch<SetStateAction<IStandard[]>>;
}

export const NotebookContext = createContext<INotebookContext>({
  projectSlug: "",
  runId: "",
  measuringPoints: [],
  standards: [],
  addObjectToMeasuringPoint: () => {},
  setMeasuringPoints: () => {},
  setImageStorage: () => {},
  updateMeasuringPointImage: () => {},
  setStandards: () => {},
});

export function useNotebookContext(
  projectSlug: string,
  runId: string,
): INotebookContext {
  const [imageStorage, setImageStorage] = useState<ImageStorage>();
  const [measuringPoints, setMeasuringPoints] = useState<IMeasuringPoint[]>([]);
  const [standards, setStandards] = useState<IStandard[]>([]);

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
    standards,
    setStandards,
  };
}
