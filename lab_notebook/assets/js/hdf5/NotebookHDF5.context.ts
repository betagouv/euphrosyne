import { createContext, useContext } from "react";
import { HDF5DatasetEntry } from "./types";

export interface NotebookHDF5ContextValue {
  entriesByPointId: Record<string, HDF5DatasetEntry[]>;
  hasMatchesByPointId: Record<string, boolean>;
  loadingEntriesByPointId: Record<string, boolean>;
  visualizationModalId: string;
  loadEntriesForPoint: (pointId: string) => Promise<void>;
  visualizeEntry: (entry: HDF5DatasetEntry) => void;
}

export const NotebookHDF5Context = createContext<NotebookHDF5ContextValue>({
  entriesByPointId: {},
  hasMatchesByPointId: {},
  loadingEntriesByPointId: {},
  visualizationModalId: "",
  loadEntriesForPoint: async () => {},
  visualizeEntry: () => {},
});

export function useNotebookHDF5Context(): NotebookHDF5ContextValue {
  return useContext(NotebookHDF5Context);
}
