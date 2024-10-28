import { createContext } from "react";
import toolsFetch from "./euphrosyne-tools-client";

export interface IEuphrosyneToolsClient {
  fetchFn: typeof toolsFetch;
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
