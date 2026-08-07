import type { EuphrosyneFile } from "../../lab/assets/js/file-service";
import type { ToolsFetch } from "../../shared/js/euphrosyne-tools-client";
import {
  createTraupixeVisualization,
  filterTraupixeFiles,
  TraupixeVisualizationError,
} from "../assets/js/traupixe/traupixe-service";
import type { TraupixeVisualization } from "../assets/js/traupixe/types";

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
  overrides: Partial<TraupixeVisualization> = {},
): TraupixeVisualization {
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

describe("TRAUPIXE file discovery", () => {
  it("keeps supported variants and orders the newest first", () => {
    const newer = file("CONSO_IV_TRAUPIXE-results.xlsx", {
      lastModified: new Date("2026-07-31T10:00:00Z"),
    });
    const older = file("TRAUPIXE-results.XLSX");

    expect(
      filterTraupixeFiles([
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

describe("TRAUPIXE visualization service", () => {
  it("posts the selected path and question to Tools API", async () => {
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

    const result = await createTraupixeVisualization({
      fetchFn,
      projectSlug: "project slug",
      path: "/run/raw_data/TRAUPIXE.xlsx",
      question: "Compare Fe et Cu",
    });

    expect(result).toEqual(payload);
    expect(fetchFn).toHaveBeenCalledWith(
      "/aglae/project%20slug/visualizations",
      {
        method: "POST",
        body: JSON.stringify({
          path: "/run/raw_data/TRAUPIXE.xlsx",
          question: "Compare Fe et Cu",
        }),
      },
    );
  });

  it("keeps the rejection reason and request id", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: {
            message: "The request could not be processed.",
            reason: "Invalid analysis plan.",
            request_id: "body-request-id",
          },
        }),
        {
          status: 422,
          headers: {
            "Content-Type": "application/json",
            "X-Request-ID": "header-request-id",
          },
        },
      ),
    ) as ToolsFetch;

    await expect(
      createTraupixeVisualization({
        fetchFn,
        projectSlug: "project",
        path: "/run/raw_data/TRAUPIXE.xlsx",
        question: "Question",
      }),
    ).rejects.toMatchObject({
      reason: "Invalid analysis plan.",
      requestId: "header-request-id",
    } satisfies Partial<TraupixeVisualizationError>);
  });

  it("uses a simple FastAPI detail as the rejection reason", async () => {
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Chemin de fichier invalide." }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      }),
    ) as ToolsFetch;

    await expect(
      createTraupixeVisualization({
        fetchFn,
        projectSlug: "project",
        path: "/run/raw_data/TRAUPIXE.xlsx",
        question: "Question",
      }),
    ).rejects.toMatchObject({
      reason: "Chemin de fichier invalide.",
      requestId: null,
    } satisfies Partial<TraupixeVisualizationError>);
  });
});
