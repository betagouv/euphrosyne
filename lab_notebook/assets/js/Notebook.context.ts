import {
  createContext,
  Dispatch,
  SetStateAction,
  useCallback,
  useState,
} from "react";
import { listMeasuringPoints } from "../../../lab/assets/js/measuring-point.services";
import { fetchRunObjectGroups } from "../../../lab/objects/assets/js/services";
import { RunObjectGroup } from "../../../lab/objects/assets/js/types";
import {
  IMeasuringPoint,
  IMeasuringPointImage,
} from "../../../shared/js/images/types";
import {
  RunMeasuringPointStandards,
  IStandard,
  IMeasuringPointStandard,
} from "../../../standard/assets/js/IStandard";
import {
  listRunMeasuringPointsStandard,
  listStandards,
} from "../../../standard/assets/js/standard-services";
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
  runObjectGroups: RunObjectGroup[];
  setRunObjectGroups: Dispatch<SetStateAction<RunObjectGroup[]>>;
  runMeasuringPointStandards: RunMeasuringPointStandards;
  setRunMeasuringPointStandards: Dispatch<
    SetStateAction<RunMeasuringPointStandards>
  >;
  refreshNotebookState: () => Promise<void>;
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
  runObjectGroups: [],
  runMeasuringPointStandards: {},
  imageStorage: null,
  addObjectToMeasuringPoint: () => {},
  setMeasuringPoints: () => {},
  updateMeasuringPointImage: () => {},
  setStandards: () => {},
  setRunObjectGroups: () => {},
  setRunMeasuringPointStandards: () => {},
  refreshNotebookState: async () => {},
  updatedMeasuringPointStandard: () => {},
});

export function useNotebookContext(
  projectSlug: string,
  runId: string,
  imageStorage: ImageStorage | null,
): INotebookContext {
  const [measuringPoints, setMeasuringPoints] = useState<IMeasuringPoint[]>([]);
  const [standards, setStandards] = useState<IStandard[]>([]);
  const [runObjectGroups, setRunObjectGroups] = useState<RunObjectGroup[]>([]);
  const [runMeasuringPointStandards, setRunMeasuringPointStandards] =
    useState<RunMeasuringPointStandards>({});

  const refreshNotebookState = useCallback(async () => {
    const [
      latestPoints,
      latestObjectGroups,
      latestStandards,
      latestRunStandards,
    ] = await Promise.all([
      listMeasuringPoints(runId),
      fetchRunObjectGroups(runId),
      listStandards(),
      listRunMeasuringPointsStandard(runId),
    ]);
    setMeasuringPoints(latestPoints);
    setRunObjectGroups(latestObjectGroups);
    setStandards(latestStandards);
    setRunMeasuringPointStandards(latestRunStandards);
  }, [runId]);

  const addObjectToMeasuringPoint = (
    measuringPointId: string,
    objectGroupId: string,
  ) => {
    setMeasuringPoints((currentPoints) =>
      currentPoints.map((p) =>
        p.id === measuringPointId ? { ...p, objectGroupId } : p,
      ),
    );
  };

  const updateMeasuringPointImage = (
    measuringPointId: string,
    image?: IMeasuringPointImage,
  ) => {
    setMeasuringPoints((currentPoints) =>
      currentPoints.map((p) =>
        p.id === measuringPointId ? { ...p, image } : p,
      ),
    );
  };

  const updatedMeasuringPointStandard = (
    measuringPointId: string,
    standard?: IMeasuringPointStandard,
  ) => {
    setRunMeasuringPointStandards((currentStandards) => {
      if (!standard) {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { [measuringPointId]: _, ...rest } = currentStandards;
        return rest;
      }
      return {
        ...currentStandards,
        [measuringPointId]: standard,
      };
    });
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
    runObjectGroups,
    setRunObjectGroups,
    runMeasuringPointStandards,
    setRunMeasuringPointStandards,
    refreshNotebookState,
    updatedMeasuringPointStandard,
  };
}
