import { act } from "react";
import type { Root } from "react-dom/client";
import { createRoot } from "react-dom/client";
import TraupixeChart, {
  withTraupixeChartDefaults,
} from "../assets/js/components/TraupixeChart";
import type { TraupixeVisualization } from "../assets/js/traupixe/types";

const echarts = vi.hoisted(() => ({
  setOption: vi.fn(),
  resize: vi.fn(),
  dispose: vi.fn(),
  init: vi.fn(),
}));

vi.mock("echarts", () => ({
  init: echarts.init,
}));

describe("TraupixeChart", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (
      globalThis as typeof globalThis & {
        IS_REACT_ACT_ENVIRONMENT: boolean;
      }
    ).IS_REACT_ACT_ENVIRONMENT = true;
    echarts.init.mockReturnValue({
      setOption: echarts.setOption,
      resize: echarts.resize,
      dispose: echarts.dispose,
    });
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(async () => {
    await act(async () => root.unmount());
    (
      globalThis as typeof globalThis & {
        IS_REACT_ACT_ENVIRONMENT: boolean;
      }
    ).IS_REACT_ACT_ENVIRONMENT = false;
    container.remove();
    vi.clearAllMocks();
  });

  it("passes the backend option to ECharts without interpreting its series", async () => {
    const option = {
      xAxis: { type: "category" as const, data: ["A"] },
      yAxis: { type: "value" as const },
      visualMap: { min: 0, max: 1 },
      series: [{ type: "heatmap" as const, data: [[0, 0, 1]] }],
    };
    const visualization: TraupixeVisualization = {
      title: "Matrice",
      option,
    };

    await act(async () => {
      root.render(<TraupixeChart visualization={visualization} />);
    });

    expect(echarts.setOption).toHaveBeenCalledWith(
      expect.objectContaining({
        grid: {
          bottom: 32,
          containLabel: true,
          left: 24,
          right: 24,
          top: 72,
        },
        series: option.series,
        tooltip: { confine: true },
        xAxis: expect.objectContaining({
          axisLabel: {
            hideOverlap: true,
            overflow: "truncate",
            width: 160,
          },
        }),
      }),
      { notMerge: true },
    );
    expect(option.xAxis).not.toHaveProperty("axisLabel");
  });

  it("preserves explicit presentation settings while containing labels", () => {
    const option = {
      grid: { left: 120, containLabel: false },
      xAxis: {
        type: "category" as const,
        axisLabel: { rotate: 45, width: 80 },
      },
      yAxis: { type: "value" as const },
    };

    expect(withTraupixeChartDefaults(option)).toEqual(
      expect.objectContaining({
        grid: expect.objectContaining({ left: 120, containLabel: true }),
        xAxis: expect.objectContaining({
          axisLabel: {
            hideOverlap: true,
            overflow: "truncate",
            rotate: 45,
            width: 80,
          },
        }),
        yAxis: { type: "value" },
      }),
    );
  });
});
