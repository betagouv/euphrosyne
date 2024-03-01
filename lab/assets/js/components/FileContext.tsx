import * as React from "react";
import { EuphrosyneFile } from "../file-service";

export const FileContext = React.createContext<EuphrosyneFile | null>(null);

export function FileProvider({
  children,
  value,
}: {
  children: React.ReactNode;
  value: EuphrosyneFile;
}) {
  return <FileContext.Provider value={value}>{children}</FileContext.Provider>;
}
