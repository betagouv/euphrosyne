import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import type { EChartsOption } from "echarts";
import type { DataVisualization } from "../types";

type OptionObject = Record<string, unknown>;

function isOptionObject(value: unknown): value is OptionObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function mapOptionObjects(
  value: unknown,
  defaults: (option: OptionObject) => OptionObject,
): unknown {
  if (Array.isArray(value)) {
    return value.map((option) =>
      isOptionObject(option) ? defaults(option) : option,
    );
  }
  return isOptionObject(value) ? defaults(value) : value;
}

function withAxisLabelDefaults(axis: OptionObject): OptionObject {
  const isCategoryAxis = axis.type === "category" || Array.isArray(axis.data);
  if (!isCategoryAxis) {
    return axis;
  }
  const axisLabel = isOptionObject(axis.axisLabel) ? axis.axisLabel : {};
  return {
    ...axis,
    axisLabel: {
      hideOverlap: true,
      overflow: "truncate",
      width: 160,
      ...axisLabel,
    },
  };
}

export function withDataVisualizationDefaults(
  option: EChartsOption,
): EChartsOption {
  const normalized: OptionObject = { ...(option as OptionObject) };
  const gridDefaults = (grid: OptionObject): OptionObject => ({
    left: 24,
    right: 24,
    top: 72,
    bottom: 32,
    ...grid,
    containLabel: true,
  });

  normalized.grid =
    option.grid === undefined
      ? gridDefaults({})
      : mapOptionObjects(option.grid, gridDefaults);
  if (option.xAxis !== undefined) {
    normalized.xAxis = mapOptionObjects(option.xAxis, withAxisLabelDefaults);
  }
  if (option.yAxis !== undefined) {
    normalized.yAxis = mapOptionObjects(option.yAxis, withAxisLabelDefaults);
  }
  const tooltip = isOptionObject(option.tooltip) ? option.tooltip : {};
  normalized.tooltip = { confine: true, ...tooltip };

  return normalized as EChartsOption;
}

export default function DataVisualizationChart({
  visualization,
}: {
  visualization: DataVisualization;
}) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current) {
      return;
    }
    const chart = echarts.init(container.current, undefined, {
      renderer: "svg",
    });
    chart.setOption(withDataVisualizationDefaults(visualization.option), {
      notMerge: true,
    });
    const resize = () => chart.resize();
    const resizeObserver =
      typeof ResizeObserver === "undefined" ? null : new ResizeObserver(resize);
    resizeObserver?.observe(container.current);
    window.addEventListener("resize", resize);
    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [visualization]);

  return (
    <div
      ref={container}
      className="data-visualization-assistant__chart"
      role="img"
      aria-label={visualization.title}
    />
  );
}
