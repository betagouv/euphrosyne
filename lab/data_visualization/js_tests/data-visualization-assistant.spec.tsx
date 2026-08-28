import { act, createElement } from "react";
import type { Root } from "react-dom/client";
import { createRoot } from "react-dom/client";
import type { EuphrosyneFile } from "../../assets/js/file-service";
import type { ToolsFetch } from "../../../shared/js/euphrosyne-tools-client";
import DataVisualizationAssistant from "../assets/js/components/DataVisualizationAssistant";

vi.mock("../assets/js/components/DataVisualizationChart", () => ({
  default: ({ visualization }: { visualization: { title: string } }) =>
    createElement("div", { "data-testid": "chart" }, visualization.title),
}));

function dataFile(name: string): EuphrosyneFile {
  return {
    name,
    path: `/run/raw_data/${name}`,
    lastModified: new Date("2026-07-30T10:00:00Z"),
    size: 1024,
    isDir: false,
  };
}

describe("DataVisualizationAssistant", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (
      globalThis as typeof globalThis & {
        IS_REACT_ACT_ENVIRONMENT: boolean;
      }
    ).IS_REACT_ACT_ENVIRONMENT = true;
    window.gettext = (text: string) => text;
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
    vi.restoreAllMocks();
  });

  it("lets the user select a data file and replaces the result with the response", async () => {
    const first = dataFile("TRAUPIXE-first.xlsx");
    const second = dataFile("TRAUPIXE-second.xlsx");
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          request_id: "request-id",
          answer: "Feuille : Elemental Conc.\nP: X0 / Fe : 2 points",
          visualizations: [
            {
              title: "Fer et cuivre",
              option: { series: [{ type: "bar", data: [10] }] },
            },
            {
              title: "Cuivre et plomb",
              option: { series: [{ type: "scatter", data: [[1, 2]] }] },
            },
          ],
        }),
        { status: 200 },
      ),
    ) as ToolsFetch;

    await act(async () => {
      root.render(
        <DataVisualizationAssistant
          projectSlug="project"
          files={[first, second]}
          fetchFn={fetchFn}
        />,
      );
    });

    expect(container.textContent).toContain(
      "Generate a visualization from a TRAUPIXE file in this run.",
    );
    expect(container.textContent).toContain("Powered by Albert");
    expect(container.textContent).toContain(
      "Select the file to use to generate the visualization.",
    );

    const select = container.querySelector("select");
    const input = container.querySelector("input");
    const form = container.querySelector("form");
    expect(select).not.toBeNull();
    expect(input).not.toBeNull();
    expect(form).not.toBeNull();

    await act(async () => {
      if (select) {
        Object.getOwnPropertyDescriptor(
          HTMLSelectElement.prototype,
          "value",
        )?.set?.call(select, second.path);
        select.dispatchEvent(new Event("change", { bubbles: true }));
      }
      if (input) {
        Object.getOwnPropertyDescriptor(
          HTMLInputElement.prototype,
          "value",
        )?.set?.call(input, "  Compare Fe et Cu  ");
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });
    await act(async () => {
      form?.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true }),
      );
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(fetchFn).toHaveBeenCalledWith(
      "/data/project/visualizations",
      expect.objectContaining({
        body: JSON.stringify({
          path: second.path,
          question: "Compare Fe et Cu",
        }),
      }),
    );
    expect(
      Array.from(container.querySelectorAll('[data-testid="chart"]')).map(
        (chart) => chart.textContent,
      ),
    ).toEqual(["Fer et cuivre", "Cuivre et plomb"]);
    expect(
      container.querySelector(".data-visualization-assistant__answer")
        ?.textContent,
    ).toContain("P: X0 / Fe : 2 points");
  });

  it("shows the localized rejection code and request reference", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: {
            code: "INVALID_DATA_FILE",
            request_id: "request-id",
          },
        }),
        {
          status: 422,
          headers: {
            "Content-Type": "application/json",
            "X-Request-ID": "request-id",
          },
        },
      ),
    ) as ToolsFetch;
    vi.spyOn(console, "error").mockImplementation(() => undefined);

    await act(async () => {
      root.render(
        <DataVisualizationAssistant
          projectSlug="project"
          files={[dataFile("TRAUPIXE.xlsx")]}
          fetchFn={fetchFn}
        />,
      );
    });

    const input = container.querySelector("input");
    const form = container.querySelector("form");
    await act(async () => {
      if (input) {
        Object.getOwnPropertyDescriptor(
          HTMLInputElement.prototype,
          "value",
        )?.set?.call(input, "Compare Fe et Cu");
        input.dispatchEvent(new Event("input", { bubbles: true }));
      }
    });
    await act(async () => {
      form?.dispatchEvent(
        new Event("submit", { bubbles: true, cancelable: true }),
      );
      await Promise.resolve();
      await Promise.resolve();
    });

    const alert = container.querySelector(".fr-alert--error");
    expect(alert?.textContent).toContain("The selected data file is invalid.");
    expect(alert?.textContent).toContain("request-id");
  });
});
