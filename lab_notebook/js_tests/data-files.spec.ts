import { act, createElement } from "react";
import type { ReactElement } from "react";
import { createRoot } from "react-dom/client";
import type { Root } from "react-dom/client";
import FileTable from "../../lab/assets/js/components/FileTable";
import {
  EuphrosyneFile,
  FileService,
} from "../../lab/assets/js/file-service";
import {
  groupRunDataFiles,
  normalizeMeasuringPointName,
  parseMeasuringPointSegment,
  sortRunDataFiles,
  useRunDataFiles,
} from "../assets/js/data-files";
import NotebookDataFilesActionCell from "../assets/js/components/NotebookDataFilesActionCell";

function file(name: string, isDir = false): EuphrosyneFile {
  return {
    name,
    path: name,
    lastModified: new Date("2026-05-18T10:04:00Z"),
    size: isDir ? null : 1000,
    isDir,
  };
}

function createJSONResponse<T>(payload: T): Response {
  return {
    ok: true,
    status: 200,
    json: vi.fn().mockResolvedValue(payload),
  } as unknown as Response;
}

async function flushAsyncWork(iterations = 4): Promise<void> {
  for (let index = 0; index < iterations; index += 1) {
    await act(async () => {
      await Promise.resolve();
    });
  }
}

function RunDataFilesHarness({
  isDataAvailable,
  fetchFn,
}: {
  isDataAvailable: boolean;
  fetchFn: typeof fetch;
}) {
  useRunDataFiles({
    projectSlug: "2026-bouddha",
    runLabel: "20260224_Protons3MeV",
    isDataAvailable,
    measuringPointNames: ["008"],
    fetchFn,
  });

  return null;
}

describe("notebook data files", () => {
  let container: HTMLDivElement;
  let root: Root;

  beforeEach(() => {
    Object.defineProperty(window, "gettext", {
      configurable: true,
      value: (str: string) => str,
    });
    Object.defineProperty(window, "interpolate", {
      configurable: true,
      value: (str: string) => str,
    });
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    vi.restoreAllMocks();
  });

  it("normalizes measuring point names for four-digit file matching", () => {
    expect(normalizeMeasuringPointName("8")).toBe("0008");
    expect(normalizeMeasuringPointName("008")).toBe("0008");
    expect(normalizeMeasuringPointName("12")).toBe("0012");
    expect(normalizeMeasuringPointName("[STD] 008")).toBeNull();
  });

  it("parses the four-digit measuring point segment after the run date", () => {
    expect(
      parseMeasuringPointSegment(
        "20260224_0008_CRRMF48563_2026BOUDDHA_IBA.g20",
      ),
    ).toBe("0008");
    expect(parseMeasuringPointSegment("20260224_008_file.g20")).toBeNull();
    expect(parseMeasuringPointSegment("report_0008_file.xlsx")).toBeNull();
  });

  it("sorts directories, spreadsheets, hdf5 files, then other files", () => {
    const sorted = sortRunDataFiles([
      file("zeta.g20"),
      file("batch.hdf5"),
      file("report.xlsx"),
      file("maps", true),
      file("data.csv"),
      file("standard.h5"),
      file("photos", true),
    ]);

    expect(sorted.map(({ name }) => name)).toEqual([
      "maps",
      "photos",
      "data.csv",
      "report.xlsx",
      "batch.hdf5",
      "standard.h5",
      "zeta.g20",
    ]);
  });

  it("groups point files and keeps non-matching files global", () => {
    const grouped = groupRunDataFiles(
      [
        file("maps_20260224", true),
        file("20260224_0008_CRRMF48563_2026BOUDDHA_IBA.g20"),
        file("20260224_0008_CRRMF48563_2026BOUDDHA_IBA.x0"),
        file("20260224_0009_CRRMF48563_2026BOUDDHA_IBA.g70"),
        file("20260224_0012_CRRMF48563_2026BOUDDHA_IBA.g70"),
        file("20260224_2026BOUDDHA_batch_IBA.hdf5"),
        file("Rapport_1_20260224_PRJ_IBA.xls"),
      ],
      ["008", "009"],
    );

    expect(grouped.byMeasuringPoint["0008"].map(({ name }) => name)).toEqual([
      "20260224_0008_CRRMF48563_2026BOUDDHA_IBA.g20",
      "20260224_0008_CRRMF48563_2026BOUDDHA_IBA.x0",
    ]);
    expect(grouped.byMeasuringPoint["0009"].map(({ name }) => name)).toEqual([
      "20260224_0009_CRRMF48563_2026BOUDDHA_IBA.g70",
    ]);
    expect(grouped.byMeasuringPoint["0012"]).toBeUndefined();
    expect(grouped.global.map(({ name }) => name)).toEqual([
      "maps_20260224",
      "Rapport_1_20260224_PRJ_IBA.xls",
      "20260224_2026BOUDDHA_batch_IBA.hdf5",
      "20260224_0012_CRRMF48563_2026BOUDDHA_IBA.g70",
    ]);
  });

  it("does not fetch run data files when project data is unavailable", async () => {
    const fetchMock = vi.fn();

    await act(async () => {
      root.render(
        createElement(RunDataFilesHarness, {
          isDataAvailable: false,
          fetchFn: fetchMock as typeof fetch,
        }),
      );
    });
    await flushAsyncWork();

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("fetches raw and processed data once when project data is available", async () => {
    const fetchMock = vi.fn().mockResolvedValue(createJSONResponse([]));

    await act(async () => {
      root.render(
        createElement(RunDataFilesHarness, {
          isDataAvailable: true,
          fetchFn: fetchMock as typeof fetch,
        }),
      );
    });
    await flushAsyncWork();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock).toHaveBeenCalledWith(
      "/data/2026-bouddha/runs/20260224_Protons3MeV/raw_data",
      { method: "GET" },
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/data/2026-bouddha/runs/20260224_Protons3MeV/processed_data",
      { method: "GET" },
    );
  });

  it("renders directory rows without a folder navigation action", async () => {
    const fileService = new FileService("/data", "/sas", vi.fn());

    await act(async () => {
      root.render(
        createElement(FileTable, {
          rows: [file("maps_20260224", true)],
          cols: [{ label: "File", key: "name" }],
          actionCell: createElement(NotebookDataFilesActionCell, {
            projectId: "42",
            fileService,
          }) as unknown as ReactElement<"td">,
        }),
      );
    });

    expect(document.body.textContent).toContain("maps_20260224");
    expect(document.body.querySelectorAll("button")).toHaveLength(0);
  });
});
