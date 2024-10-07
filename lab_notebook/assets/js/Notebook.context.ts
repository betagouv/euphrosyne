import { createContext } from "react";

export interface INotebookContext {
  projectSlug: string;
  runId: string;
}

export const NotebookContext = createContext<INotebookContext>({
  projectSlug: "",
  runId: "",
});
