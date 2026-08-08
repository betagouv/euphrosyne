import type { EChartsOption } from "echarts";
import type { EuphrosyneFile } from "../../../../lab/assets/js/file-service";

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
