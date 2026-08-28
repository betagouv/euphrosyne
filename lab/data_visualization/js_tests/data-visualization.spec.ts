import type { EuphrosyneFile } from "../../assets/js/file-service";
import type { ToolsFetch } from "../../../shared/js/euphrosyne-tools-client";
import {
  createDataVisualization,
  DataVisualizationError,
  findVisualizableDataFiles,
} from "../assets/js/data-visualization-service";
import type { DataVisualization } from "../assets/js/types";

function file(
  name: string,
  overrides: Partial<EuphrosyneFile> = {},
): EuphrosyneFile {
  return {
    name,
    path: `/run/raw_data/${name}`,
    lastModified: new Date("2026-07-30T10:00:00Z"),
    size: 1024,
    isDir: false,
    ...overrides,
  };
}

function visualization(
  overrides: Partial<DataVisualization> = {},
): DataVisualization {
  return {
    title: "Concentrations",
    option: {
      title: { text: "Concentrations" },
      xAxis: { type: "category", data: ["Ligne Excel 3"] },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: [10] }],
    },
    ...overrides,
  };
}

beforeEach(() => {
  window.gettext = (text: string) => text;
});

describe("visualizable data file discovery", () => {
  it("keeps files accepted by the currently supported format and orders them newest first", () => {
    const newer = file("CONSO_IV_TRAUPIXE-results.xlsx", {
      lastModified: new Date("2026-07-31T10:00:00Z"),
    });
    const older = file("TRAUPIXE-results.XLSX");

    expect(
      findVisualizableDataFiles([
        older,
        file("results.xlsx"),
        file("TRAUPIXE-results.xls"),
        file("TRAUPIXE-directory.xlsx", { isDir: true }),
        file("TRAUPIXE-empty.xlsx", { size: 0 }),
        newer,
      ]),
    ).toEqual([newer, older]);
  });
});

describe("data visualization service", () => {
  it("posts the selected file path and question to the visualization endpoint", async () => {
    const payload = {
      request_id: "request-id",
      answer: "Answer",
      visualizations: [visualization()],
    };
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ) as ToolsFetch;
    const result = await createDataVisualization({
      fetchFn,
      projectSlug: "project",
      dataFile: file("TRAUPIXE.xlsx"),
      question: "Compare Fe et Cu",
    });

    expect(result).toEqual(payload);
    expect(fetchFn).toHaveBeenCalledWith("/data/project/visualizations", {
      method: "POST",
      body: JSON.stringify({
        path: "/run/raw_data/TRAUPIXE.xlsx",
        question: "Compare Fe et Cu",
      }),
    });
  });

  it("keeps the rejection code and request id", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: {
            code: "INVALID_DATA_FILE",
            request_id: "body-request-id",
          },
        }),
        {
          status: 422,
          headers: { "Content-Type": "application/json" },
        },
      ),
    ) as ToolsFetch;

    await expect(
      createDataVisualization({
        fetchFn,
        projectSlug: "project",
        dataFile: file("TRAUPIXE.xlsx"),
        question: "Question",
      }),
    ).rejects.toMatchObject({
      code: "INVALID_DATA_FILE",
      requestId: "body-request-id",
    } satisfies Partial<DataVisualizationError>);
  });

  it("uses a generic error for responses outside the visualization error contract", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Chemin de fichier invalide." }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      }),
    ) as ToolsFetch;

    await expect(
      createDataVisualization({
        fetchFn,
        projectSlug: "project",
        dataFile: file("TRAUPIXE.xlsx"),
        question: "Question",
      }),
    ).rejects.toMatchObject({
      code: null,
      requestId: null,
    } satisfies Partial<DataVisualizationError>);
  });
});
