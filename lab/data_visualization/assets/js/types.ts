import type { EChartsOption } from "echarts";
import type { EuphrosyneFile } from "../../../assets/js/file-service";

export interface DataVisualizationFormat {
  accepts(file: EuphrosyneFile): boolean;
}

export interface DataVisualization {
  title: string;
  option: EChartsOption;
}

export interface DataVisualizationResponse {
  request_id: string;
  answer: string;
  visualizations: DataVisualization[];
}

export const DATA_VISUALIZATION_ERROR_CODES = [
  "INVALID_FILE_PATH",
  "UNSUPPORTED_FILE_TYPE",
  "FILE_TOO_LARGE",
  "INVALID_DATA_FILE",
] as const;

export type DataVisualizationErrorCode =
  (typeof DATA_VISUALIZATION_ERROR_CODES)[number];
