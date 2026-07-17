import {
  discoverHDF5NotebookGenerationCandidates,
  generateNotebookFromHDF5,
  previewNotebookGenerationFromHDF5,
  type HDF5NotebookGenerationCandidate,
} from "../assets/js/hdf5";
import type { RunObjectGroup } from "../../lab/objects/assets/js/types";
import type { IMeasuringPoint } from "../../shared/js/images/types";

const integer32Type = {
  class: 0,
  dtype: "<i4",
  size: 4,
  sign: 1,
};
const stringType = {
  class: 3,
  dtype: "|O",
  size: 8,
};

function candidate(
  overrides: Partial<HDF5NotebookGenerationCandidate> = {},
): HDF5NotebookGenerationCandidate {
  return {
    id: "file.hdf5:/20260224_0006_CRRMF48563",
    fileName: "file.hdf5",
    filePath: "/run/file.hdf5",
    groupName: "20260224_0006_CRRMF48563",
    groupPath: "/20260224_0006_CRRMF48563",
    pointKey: "0006",
    pointName: "006",
    analysisType: "object",
    comment: "Face avant base zone rouge",
    referenceLabel: "CRRMF48563",
    ...overrides,
  };
}

function point(overrides: Partial<IMeasuringPoint> = {}): IMeasuringPoint {
  return {
    id: "point-6",
    name: "006",
    objectGroupId: null,
    comments: null,
    ...overrides,
  };
}

function runObjectGroup(label: string, id = "object-1"): RunObjectGroup {
  return {
    id: `run-${id}`,
    objectGroup: {
      id,
      label,
      objectCount: 1,
      dating: "",
      materials: [],
      externalReference: null,
    },
  };
}

function services() {
  return {
    createMeasuringPoint: vi.fn(async () => point()),
    updateMeasuringPointComments: vi.fn(async () => undefined),
    updateMeasuringPointObjectId: vi.fn(async () => undefined),
    createObjectGroup: vi.fn(async ({ label }: { label: string }) => ({
      id: 10,
      label,
    })),
    addObjectGroupToRun: vi.fn(async () => undefined),
    addOrUpdateStandardToMeasuringPoint: vi.fn(async (standard: string) => ({
      id: "standard-link-1",
      standard: { label: standard },
    })),
  };
}

function jsonResponse(data: unknown) {
  return {
    ok: true,
    status: 200,
    json: async () => data,
  };
}

describe("HDF5 notebook generation workflow", () => {
  beforeEach(() => {
    window.gettext = (text: string) => text;
    window.interpolate = (text: string, args: string[]) =>
      args.reduce((result, arg) => result.replace("%s", arg), text);
  });

  it("discovers generation candidates from detailed child dataset attributes", async () => {
    const fetchFn = vi.fn(async (url: string) => {
      if (url.includes("/raw_data")) {
        return jsonResponse([
          {
            name: "file.hdf5",
            path: "/run/raw_data/file.hdf5",
            last_modified: "2026-06-16T10:00:00Z",
            size: 100,
            type: "file",
          },
        ]);
      }
      if (url.includes("/processed_data")) {
        throw new Error("Processed data should not be listed for generation");
      }
      if (
        url.includes("/hdf5/meta/") &&
        url.includes("path=%2F") &&
        !url.includes("20260224_0006_CRRMF48563")
      ) {
        return jsonResponse({
          name: "/",
          kind: "group",
          attributes: [],
          children: [
            {
              name: "20260224_0006_CRRMF48563",
              kind: "group",
              attributes: [],
              children: [
                {
                  name: "G20",
                  kind: "dataset",
                  attributes: [
                    { name: "target type", shape: [], type: stringType },
                    {
                      name: "analyse description",
                      shape: [],
                      type: stringType,
                    },
                    { name: "ref. analyse", shape: [], type: stringType },
                  ],
                  shape: [2048],
                  type: integer32Type,
                },
              ],
            },
          ],
        });
      }
      if (
        url.includes("/hdf5/meta/") &&
        url.includes("path=%2F20260224_0006_CRRMF48563")
      ) {
        return jsonResponse({
          name: "20260224_0006_CRRMF48563",
          kind: "group",
          attributes: [],
          children: [
            {
              name: "G20",
              kind: "dataset",
              attributes: [
                { name: "target type", shape: [], type: stringType },
                { name: "analyse description", shape: [], type: stringType },
                { name: "ref. analyse", shape: [], type: stringType },
              ],
              shape: [2048],
              type: integer32Type,
            },
          ],
        });
      }
      if (
        url.includes("/hdf5/attr/") &&
        url.includes("path=%2F20260224_0006_CRRMF48563%2FG20")
      ) {
        return jsonResponse({
          "target type": "object",
          "analyse description": "Face avant base zone rouge",
          "ref. analyse": "CRRMF48563",
        });
      }
      if (
        url.includes("/hdf5/attr/") &&
        url.includes("path=%2F20260224_0006_CRRMF48563")
      ) {
        return jsonResponse({});
      }
      throw new Error(`Unexpected request: ${url}`);
    });

    const result = await discoverHDF5NotebookGenerationCandidates({
      projectSlug: "project",
      runName: "run",
      fetchFn: fetchFn as never,
    });

    expect(result.skippedCandidates).toEqual([]);
    expect(result.candidates).toEqual([
      expect.objectContaining({
        pointKey: "0006",
        analysisType: "object",
        comment: "Face avant base zone rouge",
        referenceLabel: "CRRMF48563",
      }),
    ]);
  });

  it("creates missing points and objects from HDF5 metadata", async () => {
    const mockedServices = services();

    const result = await generateNotebookFromHDF5({
      runId: "run-1",
      candidates: [candidate()],
      measuringPoints: [],
      runObjectGroups: [],
      availableObjectGroups: [],
      standards: [],
      runMeasuringPointStandards: {},
      services: mockedServices,
    });

    expect(mockedServices.createMeasuringPoint).toHaveBeenCalledWith("run-1", {
      name: "006",
    });
    expect(mockedServices.updateMeasuringPointComments).toHaveBeenCalledWith(
      "run-1",
      "point-6",
      "Face avant base zone rouge",
    );
    expect(mockedServices.createObjectGroup).toHaveBeenCalledWith({
      label: "CRRMF48563",
    });
    expect(mockedServices.addObjectGroupToRun).toHaveBeenCalledWith(
      "run-1",
      "10",
    );
    expect(mockedServices.updateMeasuringPointObjectId).toHaveBeenCalledWith(
      "run-1",
      "point-6",
      "10",
    );
    expect(result.progress.pointsCreated).toBe(1);
    expect(result.progress.objectsCreated).toBe(1);
  });

  it("previews missing points, comment fills, and object creation without services", () => {
    const preview = previewNotebookGenerationFromHDF5({
      candidates: [candidate()],
      measuringPoints: [],
      runObjectGroups: [],
      availableObjectGroups: [],
      standards: [],
      runMeasuringPointStandards: {},
      skippedCandidateCount: 2,
    });

    expect(preview.metadata).toEqual({
      detectedPoints: 1,
      objectAnalysisPoints: 1,
      standardAnalysisPoints: 0,
      skippedEntries: 2,
    });
    expect(preview.changes.pointsToCreate).toBe(1);
    expect(preview.changes.commentsToFill).toBe(1);
    expect(preview.changes.objectsToCreate).toBe(1);
    expect(preview.warnings).toEqual([]);
  });

  it("previews existing point reuse and preserves conflicting comments", () => {
    const preview = previewNotebookGenerationFromHDF5({
      candidates: [candidate()],
      measuringPoints: [
        point({
          comments: "Manual comment",
          objectGroupId: "object-1",
        }),
      ],
      runObjectGroups: [runObjectGroup("CRRMF48563", "object-1")],
      availableObjectGroups: [],
      standards: [],
      runMeasuringPointStandards: {},
    });

    expect(preview.changes.existingPointsToReuse).toBe(1);
    expect(preview.changes.commentsPreserved).toBe(1);
    expect(preview.changes.objectsReusedOrLinked).toBe(1);
    expect(preview.warnings).toContainEqual({
      code: "different-comment",
      pointName: "006",
    });
  });

  it("previews project object reuse before object creation", () => {
    const preview = previewNotebookGenerationFromHDF5({
      candidates: [candidate()],
      measuringPoints: [point()],
      runObjectGroups: [],
      availableObjectGroups: [
        {
          id: "available-1",
          label: "CRRMF48563",
          objectCount: 1,
          dating: "",
          materials: [],
          externalReference: null,
        },
      ],
      standards: [],
      runMeasuringPointStandards: {},
    });

    expect(preview.changes.objectsReusedOrLinked).toBe(1);
    expect(preview.changes.objectsToCreate).toBe(0);
  });

  it("previews standard normalized label matches", () => {
    const preview = previewNotebookGenerationFromHDF5({
      candidates: [
        candidate({
          analysisType: "standard",
          referenceLabel: "std aso_bells",
        }),
      ],
      measuringPoints: [point()],
      runObjectGroups: [],
      availableObjectGroups: [],
      standards: [{ label: "STD-ASOBELLS" }],
      runMeasuringPointStandards: {},
    });

    expect(preview.metadata.standardAnalysisPoints).toBe(1);
    expect(preview.changes.standardsToAttachOrReuse).toBe(1);
    expect(preview.changes.missingStandards).toBe(0);
    expect(preview.warnings).toEqual([]);
  });

  it("previews missing standards and conflicting assignments as warnings", () => {
    const missingStandardPreview = previewNotebookGenerationFromHDF5({
      candidates: [
        candidate({
          analysisType: "standard",
          referenceLabel: "STD-A",
        }),
      ],
      measuringPoints: [point()],
      runObjectGroups: [],
      availableObjectGroups: [],
      standards: [],
      runMeasuringPointStandards: {},
    });

    expect(missingStandardPreview.changes.missingStandards).toBe(1);
    expect(missingStandardPreview.warnings).toContainEqual({
      code: "missing-standard",
      pointName: "006",
      label: "STD-A",
    });

    const conflictingObjectPreview = previewNotebookGenerationFromHDF5({
      candidates: [candidate()],
      measuringPoints: [
        point({
          objectGroupId: "object-2",
        }),
      ],
      runObjectGroups: [runObjectGroup("OTHER", "object-2")],
      availableObjectGroups: [],
      standards: [],
      runMeasuringPointStandards: {},
    });

    expect(conflictingObjectPreview.warnings).toContainEqual({
      code: "different-object",
      pointName: "006",
      label: "CRRMF48563",
    });

    const conflictingStandardPreview = previewNotebookGenerationFromHDF5({
      candidates: [
        candidate({
          analysisType: "standard",
          referenceLabel: "STD-A",
        }),
      ],
      measuringPoints: [point()],
      runObjectGroups: [],
      availableObjectGroups: [],
      standards: [{ label: "STD-A" }],
      runMeasuringPointStandards: {
        "point-6": {
          id: "standard-link-1",
          standard: { label: "STD-B" },
        },
      },
    });

    expect(conflictingStandardPreview.warnings).toContainEqual({
      code: "different-standard",
      pointName: "006",
      label: "STD-A",
    });
  });

  it("reuses existing run objects and does not overwrite conflicting comments", async () => {
    const mockedServices = services();
    const existingObject = runObjectGroup("CRRMF48563", "object-1");

    const result = await generateNotebookFromHDF5({
      runId: "run-1",
      candidates: [candidate()],
      measuringPoints: [
        point({
          objectGroupId: "object-1",
          comments: "Manual comment",
        }),
      ],
      runObjectGroups: [existingObject],
      availableObjectGroups: [],
      standards: [],
      runMeasuringPointStandards: {},
      services: mockedServices,
    });

    expect(mockedServices.createMeasuringPoint).not.toHaveBeenCalled();
    expect(mockedServices.updateMeasuringPointComments).not.toHaveBeenCalled();
    expect(mockedServices.updateMeasuringPointObjectId).not.toHaveBeenCalled();
    expect(result.progress.objectsReused).toBe(1);
    expect(result.progress.errors[0]).toContain("different comment");
  });

  it("reuses available project objects before creating new objects", async () => {
    const mockedServices = services();

    await generateNotebookFromHDF5({
      runId: "run-1",
      candidates: [candidate()],
      measuringPoints: [point()],
      runObjectGroups: [],
      availableObjectGroups: [
        {
          id: "available-1",
          label: "CRRMF48563",
          objectCount: 1,
          dating: "",
          materials: [],
          externalReference: null,
        },
      ],
      standards: [],
      runMeasuringPointStandards: {},
      services: mockedServices,
    });

    expect(mockedServices.createObjectGroup).not.toHaveBeenCalled();
    expect(mockedServices.addObjectGroupToRun).toHaveBeenCalledWith(
      "run-1",
      "available-1",
    );
    expect(mockedServices.updateMeasuringPointObjectId).toHaveBeenCalledWith(
      "run-1",
      "point-6",
      "available-1",
    );
  });

  it("matches standard labels without case or special characters", async () => {
    const mockedServices = services();

    const result = await generateNotebookFromHDF5({
      runId: "run-1",
      candidates: [
        candidate({
          analysisType: "standard",
          referenceLabel: "std aso_bells",
        }),
      ],
      measuringPoints: [point()],
      runObjectGroups: [],
      availableObjectGroups: [],
      standards: [{ label: "STD-ASOBELLS" }],
      runMeasuringPointStandards: {},
      services: mockedServices,
    });

    expect(
      mockedServices.addOrUpdateStandardToMeasuringPoint,
    ).toHaveBeenCalledWith("STD-ASOBELLS", "point-6", true);
    expect(result.progress.standardsReused).toBe(1);
    expect(result.progress.errors).toHaveLength(0);
  });

  it("reports missing standards without creating them", async () => {
    const mockedServices = services();

    const result = await generateNotebookFromHDF5({
      runId: "run-1",
      candidates: [
        candidate({
          analysisType: "standard",
          referenceLabel: "STD-A",
        }),
      ],
      measuringPoints: [point()],
      runObjectGroups: [],
      availableObjectGroups: [],
      standards: [],
      runMeasuringPointStandards: {},
      services: mockedServices,
    });

    expect(
      mockedServices.addOrUpdateStandardToMeasuringPoint,
    ).not.toHaveBeenCalled();
    expect(result.progress.errors[0]).toContain(
      "Standard STD-A does not exist",
    );
  });

  it("can be run again without creating duplicate points or objects", async () => {
    const mockedServices = services();

    const result = await generateNotebookFromHDF5({
      runId: "run-1",
      candidates: [candidate()],
      measuringPoints: [
        point({
          objectGroupId: "object-1",
          comments: "Face avant base zone rouge",
        }),
      ],
      runObjectGroups: [runObjectGroup("CRRMF48563", "object-1")],
      availableObjectGroups: [],
      standards: [],
      runMeasuringPointStandards: {},
      services: mockedServices,
    });

    expect(mockedServices.createMeasuringPoint).not.toHaveBeenCalled();
    expect(mockedServices.createObjectGroup).not.toHaveBeenCalled();
    expect(mockedServices.updateMeasuringPointObjectId).not.toHaveBeenCalled();
    expect(result.progress.pointsCreated).toBe(0);
    expect(result.progress.objectsCreated).toBe(0);
    expect(result.progress.objectsReused).toBe(1);
  });
});
