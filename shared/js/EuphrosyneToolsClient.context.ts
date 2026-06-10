import { createContext } from "react";
import toolsFetch, { ToolsFetch } from "./euphrosyne-tools-client";

export interface IEuphrosyneToolsClient {
  fetchFn: ToolsFetch;
}

export const EuphrosyneToolsClientContext =
  createContext<IEuphrosyneToolsClient>({
    fetchFn: toolsFetch,
  });

export function useClientContext(): IEuphrosyneToolsClient {
  return {
    fetchFn: toolsFetch,
  };
}
