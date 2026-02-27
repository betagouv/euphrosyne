import * as React from "react";
import { useContext } from "react";

interface IWorkplaceContext {
  project: {
    id: string;
  };
}

export const WorkplaceContext = React.createContext<IWorkplaceContext | null>(
  null,
);

export function WorkplaceProvider({
  children,
  value,
}: {
  children: React.ReactNode;
  value: IWorkplaceContext;
}) {
  return (
    <WorkplaceContext.Provider value={value}>
      {children}
    </WorkplaceContext.Provider>
  );
}

export const useWorkplaceContext = () => {
  const workplaceContext = useContext(WorkplaceContext);
  if (!workplaceContext)
    throw new Error(
      "No WorkplaceContext.Provider found when calling useWorkplaceContext.",
    );
  return workplaceContext;
};
