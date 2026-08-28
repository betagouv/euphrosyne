import { act } from "react";
import type { Root } from "react-dom/client";
import { createRoot } from "react-dom/client";
import type { EuphrosyneFile } from "../../assets/js/file-service";
import type { ProcessedDataFileService } from "../assets/js/processed-data/processed-data-file-service";
import type { RawDataFileService } from "../assets/js/raw-data/raw-data-file-service";
import WorkplaceRunTab from "../assets/js/components/WorkplaceRunTab";

vi.hoisted(() => {
  window.gettext = (text: string) => text;
  window.interpolate = (format: string, values: string[]) =>
    format.replace("%s", values[0]);
});

function dataFile(name: string): EuphrosyneFile {
  return {
    name,
    path: `/run/processed_data/${name}`,
    lastModified: new Date("2026-07-30T10:00:00Z"),
    size: 1024,
    isDir: false,
  };
}

describe("WorkplaceRunTab", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    (
      globalThis as typeof globalThis & {
        IS_REACT_ACT_ENVIRONMENT: boolean;
      }
    ).IS_REACT_ACT_ENVIRONMENT = true;
    window.gettext = (text: string) => text;
    window.interpolate = (format: string, values: string[]) =>
      format.replace("%s", values[0]);
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

  it("shows the visualization assistant below the lab notebook link", async () => {
    const fetchFn = vi.fn();
    const rawDataFileService = {
      fetchFn,
      listData: vi.fn().mockResolvedValue([dataFile("raw-data.xlsx")]),
    } as unknown as RawDataFileService;
    const processedDataFileService = {
      fetchFn,
      listData: vi.fn().mockResolvedValue([dataFile("TRAUPIXE-results.xlsx")]),
    } as unknown as ProcessedDataFileService;

    await act(async () => {
      root.render(
        <WorkplaceRunTab
          project={{ id: "project-id", name: "Project", slug: "project" }}
          run={{
            id: "run-id",
            label: "Run",
            rawDataTable: { canDelete: false },
            processedDataTable: { canDelete: false },
            rawDataFileService,
            processedDataFileService,
          }}
        />,
      );
      await Promise.resolve();
      await Promise.resolve();
    });

    const notebookLink = container.querySelector(
      'a[href="/lab/run/run-id/notebook"]',
    );
    const assistant = container.querySelector(".data-visualization-assistant");
    expect(assistant).not.toBeNull();
    expect(notebookLink?.parentElement?.nextElementSibling).toBe(
      assistant?.parentElement,
    );
    expect(assistant?.textContent).toContain("TRAUPIXE-results.xlsx");
    expect(rawDataFileService.listData).toHaveBeenCalledTimes(1);
    expect(processedDataFileService.listData).toHaveBeenCalledTimes(1);
  });
});
