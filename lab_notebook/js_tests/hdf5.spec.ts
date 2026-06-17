import {
  buildScientificMetadataRows,
  calculateEnergy,
  computeGlobalSpectrum,
  computeIntegratedMap,
  createEnergyAbscissas,
  createDatasetEntriesFromGroup,
  createHDF5FileSummaries,
  createMapDatasetEntryFromDetectorDataset,
  createMapDatasetEntriesFromRoot,
  formatEnergy,
  fetchHDF5Metadata,
  filterHDF5Files,
  filterHDF5MapFiles,
  findHDF5GroupMatches,
  normalizeMeasuringPointName,
  parseSpectrumCalibration,
  validateChannelRange,
  type HDF5Attribute,
  type HDF5Group,
  type HDF5Type,
  type HDF5GroupMatch,
} from "../assets/js/hdf5";
import { EuphrosyneFile } from "../../lab/assets/js/file-service";

const integer32Type: HDF5Type = {
  class: 0,
  dtype: "<i4",
  size: 4,
  order: 0,
  sign: 1,
};

const float64Type: HDF5Type = {
  class: 1,
  dtype: "<f8",
  size: 8,
};

const stringType: HDF5Type = {
  class: 3,
  dtype: "|O",
  size: 8,
};

function file(name: string): EuphrosyneFile {
  return {
    name,
    path: `/run/HDF5/${name}`,
    lastModified: new Date("2026-05-18T10:04:00Z"),
    size: 1024,
    isDir: false,
  };
}

function group(
  name: string,
  children: HDF5Group["children"] = [],
  path = name === "/" ? "/" : `/${name}`,
): HDF5Group {
  return {
    name,
    kind: "group",
    path,
    attributes: [],
    children,
  };
}

function dataset({
  name,
  path,
  shape,
  type,
  attributes = [],
}: {
  name: string;
  path: string;
  shape: number[];
  type: HDF5Type;
  attributes?: HDF5Attribute[];
}) {
  return {
    name,
    kind: "dataset" as const,
    path,
    attributes,
    shape,
    type,
  };
}

function attribute(name: string): HDF5Attribute {
  return {
    name,
    shape: [],
    type: stringType,
  };
}

describe("notebook HDF5 data helpers", () => {
  beforeEach(() => {
    window.gettext = (text: string) => text;
    window.interpolate = (text: string, args: string[]) =>
      text.replace("%s", args[0]);
  });

  it("filters HDF5 files by supported extensions", () => {
    expect(
      filterHDF5Files([
        file("batch.hdf5"),
        file("standard.H5"),
        file("notes.txt"),
        { ...file("folder.h5"), isDir: true },
      ]).map(({ name }) => name),
    ).toEqual(["batch.hdf5", "standard.H5"]);
  });

  it("filters HDF5 map files to the cartography folder", () => {
    expect(
      filterHDF5MapFiles([
        {
          ...file("map-file.hdf5"),
          path: "/run/raw_data/HDF5_maps_files/map-file.hdf5",
        },
        {
          ...file("spectrum-file.hdf5"),
          path: "/run/raw_data/spectrum-file.hdf5",
        },
        {
          ...file("map-notes.txt"),
          path: "/run/raw_data/HDF5_maps_files/map-notes.txt",
        },
      ]).map(({ name }) => name),
    ).toEqual(["map-file.hdf5"]);
  });

  it("normalizes numeric measuring point names to four digits", () => {
    expect(normalizeMeasuringPointName("8")).toBe("0008");
    expect(normalizeMeasuringPointName("008")).toBe("0008");
    expect(normalizeMeasuringPointName("0012")).toBe("0012");
    expect(normalizeMeasuringPointName("008 - Bouddha")).toBeNull();
  });

  it("parses h5grove metadata into the locked notebook entity shape", async () => {
    const fetchFn = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        name: "20260224_0005_CRRMF48563",
        kind: "group",
        attributes: [attribute("particle")],
        children: [
          {
            name: "G20",
            kind: "dataset",
            attributes: [],
            shape: [2048],
            type: integer32Type,
          },
        ],
      }),
    });

    const metadata = await fetchHDF5Metadata(
      fetchFn as never,
      "projects/project/runs/run/raw_data/file.hdf5",
      "/20260224_0005_CRRMF48563",
    );

    expect(metadata).toMatchObject({
      kind: "group",
      path: "/20260224_0005_CRRMF48563",
      children: [
        {
          kind: "dataset",
          path: "/20260224_0005_CRRMF48563/G20",
          type: integer32Type,
        },
      ],
    });
  });

  it("matches groups containing normalized point keys", () => {
    const hdf5File = file("batch.hdf5");
    const matches = findHDF5GroupMatches(
      [
        {
          file: hdf5File,
          root: group("/", [
            group("20260224_0008_CRRMF48563"),
            group("20260224_0012_CRRMF48563"),
          ]),
        },
      ],
      [{ id: "point-8", name: "8" }],
    );

    expect(matches).toHaveLength(1);
    expect(matches[0]).toMatchObject({
      pointId: "point-8",
      pointKey: "0008",
      groupPath: "/20260224_0008_CRRMF48563",
    });
  });

  it("derives covered point ranges", () => {
    const emptyFile = file("empty.hdf5");
    const singlePointFile = file("single.hdf5");
    const rangeFile = file("range.hdf5");
    const summaries = createHDF5FileSummaries(
      [emptyFile, singlePointFile, rangeFile],
      [
        {
          file: emptyFile,
          root: group("/"),
        },
        {
          file: singlePointFile,
          root: group("/", [group("20260224_0008_CRRMF48563")]),
        },
        {
          file: rangeFile,
          root: group("/", [
            group("20260224_0012_CRRMF48563"),
            group("20260224_0008_CRRMF48563"),
            group("20260224_0008_DUPLICATE"),
          ]),
        },
      ],
      ["0008", "0012"],
    );

    expect(summaries.map(({ coveredPointRange }) => coveredPointRange)).toEqual(
      [null, "0008", "0008 - 0012"],
    );
  });

  it("creates file summaries from root groups and point keys", () => {
    const hdf5File = file("batch.hdf5");
    const summaries = createHDF5FileSummaries(
      [hdf5File],
      [
        {
          file: hdf5File,
          root: group("/", [
            group("20260224_0008_CRRMF48563"),
            group("20260224_0012_CRRMF48563"),
          ]),
        },
      ],
      ["0008", "0012"],
    );

    expect(summaries).toEqual([
      expect.objectContaining({
        entryCount: 2,
        coveredPointRange: "0008 - 0012",
      }),
    ]);
  });

  it("keeps only numeric one-dimensional datasets", () => {
    const hdf5File = file("batch.hdf5");
    const match: HDF5GroupMatch = {
      file: hdf5File,
      pointId: "point-8",
      pointKey: "0008",
      group: group("20260224_0008_CRRMF48563"),
      groupPath: "/20260224_0008_CRRMF48563",
    };

    const entries = createDatasetEntriesFromGroup(match, {
      ...match.group,
      children: [
        dataset({
          name: "X0",
          path: "/20260224_0008_CRRMF48563/X0",
          shape: [2048],
          type: float64Type,
        }),
        dataset({
          name: "map",
          path: "/20260224_0008_CRRMF48563/map",
          shape: [32, 32],
          type: float64Type,
        }),
        dataset({
          name: "label",
          path: "/20260224_0008_CRRMF48563/label",
          shape: [4],
          type: stringType,
        }),
      ],
    });

    expect(entries.map((entry) => entry.datasetName)).toEqual(["X0"]);
  });

  it("keeps h5grove numeric enum datasets", () => {
    const hdf5File = file("batch.hdf5");
    const match: HDF5GroupMatch = {
      file: hdf5File,
      pointId: "point-5",
      pointKey: "0005",
      group: group("20260224_0005_CRRMF48563"),
      groupPath: "/20260224_0005_CRRMF48563",
    };

    const entries = createDatasetEntriesFromGroup(match, {
      ...match.group,
      children: [
        dataset({
          name: "X0",
          path: "/20260224_0005_CRRMF48563/X0",
          shape: [2048],
          type: integer32Type,
        }),
        dataset({
          name: "20260224_0005_image_area",
          path: "/20260224_0005_CRRMF48563/20260224_0005_image_area",
          shape: [540, 960, 3],
          type: { class: 0, dtype: "|u1", size: 1, order: 0, sign: 0 },
        }),
        dataset({
          name: "metadata",
          path: "/20260224_0005_CRRMF48563/metadata",
          shape: [4],
          type: stringType,
        }),
      ],
    });

    expect(entries.map((entry) => entry.datasetName)).toEqual(["X0"]);
  });

  it("creates dataset entries from direct numeric 1D group children", () => {
    const hdf5File = file("batch.hdf5");
    const match: HDF5GroupMatch = {
      file: hdf5File,
      pointId: "point-8",
      pointKey: "0008",
      group: group("20260224_0008_CRRMF48563"),
      groupPath: "/20260224_0008_CRRMF48563",
    };

    const entries = createDatasetEntriesFromGroup(match, {
      ...match.group,
      children: [
        dataset({
          name: "X0",
          path: "/20260224_0008_CRRMF48563/X0",
          shape: [2048],
          type: integer32Type,
          attributes: [attribute("particle")],
        }),
        dataset({
          name: "cartography",
          path: "/20260224_0008_CRRMF48563/cartography",
          shape: [2, 2],
          type: integer32Type,
        }),
      ],
    });

    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      pointId: "point-8",
      dataKind: "spectrum",
      dataKindLabel: "Spectrum",
      datasetName: "X0",
      datasetPath: "/20260224_0008_CRRMF48563/X0",
      metadataSummary: "2048 channels · particle",
    });
  });

  it("creates dataset entries from pasted h5grove point group metadata", () => {
    const hdf5File = file("20260224_2026BOUDDHA_batch_IBA.hdf5");
    const match: HDF5GroupMatch = {
      file: hdf5File,
      pointId: "point-5",
      pointKey: "0005",
      group: group("20260224_0005_CRRMF48563"),
      groupPath: "/20260224_0005_CRRMF48563",
    };

    const entries = createDatasetEntriesFromGroup(match, {
      ...match.group,
      children: [
        dataset({
          name: "20260224_0005_image_area",
          path: "/20260224_0005_CRRMF48563/20260224_0005_image_area",
          shape: [540, 960, 3],
          type: { class: 0, dtype: "|u1", size: 1 },
        }),
        dataset({
          name: "G20",
          path: "/20260224_0005_CRRMF48563/G20",
          shape: [2048],
          type: integer32Type,
        }),
        dataset({
          name: "X0",
          path: "/20260224_0005_CRRMF48563/X0",
          shape: [2048],
          type: integer32Type,
          attributes: [attribute("gupix header"), attribute("spectra sum")],
        }),
        group("screen_capture"),
      ],
    });

    expect(entries.map((entry) => entry.datasetName)).toEqual(["G20", "X0"]);
    expect(entries[0]).toMatchObject({
      datasetPath: "/20260224_0005_CRRMF48563/G20",
      metadataSummary: "2048 channels",
    });
  });

  it("creates map entries from detector groups containing 3D maps datasets", () => {
    const hdf5File = {
      ...file("cartography.hdf5"),
      path: "/run/raw_data/HDF5_maps_files/cartography.hdf5",
    };
    const root = group(
      "/",
      [
        group(
          "X0",
          [
            dataset({
              name: "maps",
              path: "/X0/maps",
              shape: [20, 40, 2048],
              type: integer32Type,
              attributes: [attribute("adc name")],
            }),
          ],
          "/X0",
        ),
        group(
          "X1",
          [
            dataset({
              name: "maps",
              path: "/X1/maps",
              shape: [20, 40],
              type: integer32Type,
            }),
          ],
          "/X1",
        ),
      ],
      "/",
    );

    const entries = createMapDatasetEntriesFromRoot(hdf5File, root);

    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      pointId: "",
      dataKind: "map",
      dataKindLabel: "Map",
      fileName: "cartography.hdf5",
      detectorName: "X0",
      groupName: "X0",
      groupPath: "/X0",
      datasetName: "maps",
      datasetPath: "/X0/maps",
      shape: [20, 40, 2048],
      acquisitionPath: "/",
      metadataSummary: "20 × 40 × 2048 map",
    });
  });

  it("creates map entries from a fetched detector group containing a maps dataset", () => {
    const hdf5File = {
      ...file("cartography.hdf5"),
      path: "/run/raw_data/HDF5_maps_files/cartography.hdf5",
    };
    const detector = group(
      "X0",
      [
        dataset({
          name: "maps",
          path: "/X0/maps",
          shape: [20, 40, 2048],
          type: integer32Type,
        }),
      ],
      "/X0",
    );

    const entries = createMapDatasetEntriesFromRoot(hdf5File, detector);

    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      detectorName: "X0",
      groupName: "X0",
      groupPath: "/X0",
      datasetPath: "/X0/maps",
      shape: [20, 40, 2048],
    });
  });

  it("creates map entries from a directly fetched detector maps dataset", () => {
    const hdf5File = {
      ...file("cartography.hdf5"),
      path: "/run/raw_data/HDF5_maps_files/cartography.hdf5",
    };
    const acquisition = group("/", [], "/");
    const detector = group("X0", [], "/X0");
    const maps = dataset({
      name: "maps",
      path: "/X0/maps",
      shape: [20, 40, 2048],
      type: integer32Type,
    });

    const entries = createMapDatasetEntryFromDetectorDataset(
      hdf5File,
      acquisition,
      detector,
      maps,
    );

    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      detectorName: "X0",
      groupPath: "/X0",
      datasetPath: "/X0/maps",
      shape: [20, 40, 2048],
    });
  });

  it("creates map entries from acquisition-level groups", () => {
    const hdf5File = {
      ...file("cartography.hdf5"),
      path: "/run/raw_data/HDF5_maps_files/cartography.hdf5",
    };
    const acquisition = group(
      "scan-1",
      [
        group(
          "X13",
          [
            dataset({
              name: "maps",
              path: "/scan-1/X13/maps",
              shape: [4, 5, 1024],
              type: float64Type,
            }),
          ],
          "/scan-1/X13",
        ),
      ],
      "/scan-1",
    );

    const entries = createMapDatasetEntriesFromRoot(
      hdf5File,
      group("/", [acquisition], "/"),
    );

    expect(entries).toHaveLength(1);
    expect(entries[0]).toMatchObject({
      detectorName: "X13",
      acquisitionName: "scan-1",
      acquisitionPath: "/scan-1",
      datasetPath: "/scan-1/X13/maps",
      shape: [4, 5, 1024],
    });
  });

  it("includes metadata summaries in dataset entries", () => {
    const hdf5File = file("batch.hdf5");
    const match: HDF5GroupMatch = {
      file: hdf5File,
      pointId: "point-8",
      pointKey: "0008",
      group: group("20260224_0008_CRRMF48563"),
      groupPath: "/20260224_0008_CRRMF48563",
    };

    const entries = createDatasetEntriesFromGroup(match, {
      ...match.group,
      children: [
        dataset({
          name: "X1",
          path: "/20260224_0008_CRRMF48563/X1",
          shape: [1024],
          type: float64Type,
        }),
      ],
    });

    expect(entries[0]).toMatchObject({
      metadataSummary: "1024 channels",
    });
  });

  it("uses strict scientific metadata attribute names", () => {
    const rows = buildScientificMetadataRows({
      "beam energy": "3000 keV",
      beam_energy: "ignored",
      "obj euphrosyne": "Bouddha",
      object_reference: "ignored",
      "ref. analyse": "CRRMF48563",
      analysis_reference: "ignored",
    });

    expect(rows).toEqual([
      {
        key: "beamEnergy",
        label: "Beam energy",
        value: "3000 keV",
      },
      {
        key: "objectReference",
        label: "Object reference",
        value: "Bouddha",
      },
      {
        key: "analysisReference",
        label: "Analysis reference",
        value: "CRRMF48563",
      },
    ]);
  });

  it("computes a global spectrum by summing every spatial pixel", () => {
    const spectrum = computeGlobalSpectrum(
      new Float64Array([
        1, 2, 3, 4, 10, 20, 30, 40, 100, 200, 300, 400, 1000, 2000, 3000, 4000,
      ]),
      2,
      2,
      4,
    );

    expect(Array.from(spectrum)).toEqual([1111, 2222, 3333, 4444]);
  });

  it("parses spectrum calibration attributes", () => {
    expect(
      parseSpectrumCalibration("MCA a=0.0200832, MCA b=-0.018052, MCA c=0"),
    ).toEqual({
      a: 0.0200832,
      b: -0.018052,
      c: 0,
    });
    expect(
      parseSpectrumCalibration("MCA   c=1e-6, MCA b = -0.2, MCA a = 2.5"),
    ).toEqual({
      a: 2.5,
      b: -0.2,
      c: 0.000001,
    });
    expect(parseSpectrumCalibration("MCA a=0.02, MCA b=-0.01")).toBeNull();
    expect(
      parseSpectrumCalibration("MCA a=0.02, MCA b=bad, MCA c=0"),
    ).toBeNull();
  });

  it("computes calibrated energy abscissas", () => {
    const calibration = { a: 2, b: -1, c: 0.5 };

    expect(calculateEnergy(3, calibration)).toBe(9.5);
    expect(Array.from(createEnergyAbscissas(4, calibration))).toEqual([
      -1, 1.5, 5, 9.5,
    ]);
  });

  it("formats energy values for labels", () => {
    expect(formatEnergy(0.123456)).toBe("0.123");
    expect(formatEnergy(12.3456)).toBe("12.346");
    expect(formatEnergy(Number.NaN)).toBe("-");
  });

  it("computes integrated maps over the selected channel range", () => {
    const map = computeIntegratedMap(
      new Float64Array([
        1, 2, 3, 4, 10, 20, 30, 40, 100, 200, 300, 400, 1000, 2000, 3000, 4000,
      ]),
      2,
      2,
      4,
      1,
      3,
    );

    expect(Array.from(map)).toEqual([5, 50, 500, 5000]);
  });

  it("validates map channel ranges", () => {
    expect(validateChannelRange(0, 4, 4)).toEqual({
      isValid: true,
      message: null,
    });
    expect(validateChannelRange(2, 2, 4)).toMatchObject({
      isValid: false,
      message: "The lower channel must be smaller than the upper channel.",
    });
    expect(validateChannelRange(0, 5, 4)).toMatchObject({
      isValid: false,
      message: "The upper channel must not exceed the number of channels.",
    });
  });
});
