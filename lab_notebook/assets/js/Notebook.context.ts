import { createContext, Dispatch, SetStateAction, useState } from "react";
import { IMeasuringPoint, IMeasuringPointImage } from "./IMeasuringPoint";
import {
  RunMeasuringPointStandards,
  IStandard,
  IMeasuringPointStandard,
} from "../../../standard/assets/js/IStandard";
import { ImageStorage } from "./hooks/useImageStorage";

export interface INotebookContext {
  projectSlug: string;
  runId: string;
  imageStorage: ImageStorage | null;
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
  runMeasuringPointStandards: RunMeasuringPointStandards;
  setRunMeasuringPointStandards: Dispatch<
    SetStateAction<RunMeasuringPointStandards>
  >;
  updatedMeasuringPointStandard: (
    measuringPointId: string,
    standard?: IMeasuringPointStandard,
  ) => void;
}

export const NotebookContext = createContext<INotebookContext>({
  projectSlug: "",
  runId: "",
  measuringPoints: [],
  standards: [],
  runMeasuringPointStandards: {},
  imageStorage: null,
  addObjectToMeasuringPoint: () => {},
  setMeasuringPoints: () => {},
  updateMeasuringPointImage: () => {},
  setStandards: () => {},
  setRunMeasuringPointStandards: () => {},
  updatedMeasuringPointStandard: () => {},
});

export function useNotebookContext(
  projectSlug: string,
  runId: string,
  imageStorage: ImageStorage | null,
): INotebookContext {
  const [measuringPoints, setMeasuringPoints] = useState<IMeasuringPoint[]>([]);
  const [standards, setStandards] = useState<IStandard[]>([]);
  const [runMeasuringPointStandards, setRunMeasuringPointStandards] =
    useState<RunMeasuringPointStandards>({});

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

  const updatedMeasuringPointStandard = (
    measuringPointId: string,
    standard?: IMeasuringPointStandard,
  ) => {
    if (!standard) {
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { [measuringPointId]: _, ...rest } = runMeasuringPointStandards;
      setRunMeasuringPointStandards(rest);
    } else {
      setRunMeasuringPointStandards({
        ...runMeasuringPointStandards,
        [measuringPointId]: standard,
      });
    }
  };

  return {
    projectSlug,
    runId,
    imageStorage,
    measuringPoints,
    setMeasuringPoints,
    addObjectToMeasuringPoint,
    updateMeasuringPointImage,
    standards,
    setStandards,
    runMeasuringPointStandards,
    setRunMeasuringPointStandards,
    updatedMeasuringPointStandard,
  };
}
