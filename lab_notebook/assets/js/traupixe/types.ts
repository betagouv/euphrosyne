import type { EChartsOption } from "echarts";

export interface TraupixeVisualization {
  title: string;
  option: EChartsOption;
}

export interface TraupixeVisualizationResponse {
  request_id: string;
  answer: string;
  visualizations: TraupixeVisualization[];
}
