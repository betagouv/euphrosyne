import { createContext, useContext } from "react";
import { HDF5DatasetEntry } from "./types";

export interface NotebookHDF5ContextValue {
  entriesByPointId: Record<string, HDF5DatasetEntry[]>;
  hasMatchesByPointId: Record<string, boolean>;
  loadingEntriesByPointId: Record<string, boolean>;
  loadEntriesForPoint: (pointId: string) => Promise<void>;
}

export const NotebookHDF5Context = createContext<NotebookHDF5ContextValue>({
  entriesByPointId: {},
  hasMatchesByPointId: {},
  loadingEntriesByPointId: {},
  loadEntriesForPoint: async () => {},
});

export function useNotebookHDF5Context(): NotebookHDF5ContextValue {
  return useContext(NotebookHDF5Context);
}
