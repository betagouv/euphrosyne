import {
  buildScientificMetadataRows,
  HDF5DatasetEntry,
  ScientificMetadataRow,
} from "../../hdf5";

export function buildSpectrumMetadataRows(
  entry: HDF5DatasetEntry,
  attributeValues: Record<string, unknown>,
): ScientificMetadataRow[] {
  return [
    {
      key: "file",
      label: window.gettext("File"),
      value: entry.fileName,
    },
    {
      key: "entry",
      label: window.gettext("Entry"),
      value: entry.datasetPath,
    },
    {
      key: "group",
      label: window.gettext("Measurement group"),
      value: entry.groupName,
    },
    ...buildScientificMetadataRows(attributeValues),
  ];
}

export function buildMapMetadataRows(
  entry: HDF5DatasetEntry,
  attributeValues: Record<string, unknown>,
): ScientificMetadataRow[] {
  return [
    {
      key: "file",
      label: window.gettext("File"),
      value: entry.fileName,
    },
    {
      key: "detector",
      label: window.gettext("Detector"),
      value: entry.detectorName || entry.groupName,
    },
    {
      key: "entry",
      label: window.gettext("Entry"),
      value: entry.datasetPath,
    },
    {
      key: "shape",
      label: window.gettext("Shape"),
      value: entry.shape.join(" × "),
    },
    ...buildScientificMetadataRows(attributeValues),
  ];
}

export function getVisualizationModalTitle(entry: HDF5DatasetEntry): string {
  if (entry.dataKind === "map") {
    return window.interpolate(window.gettext("%s map — %s"), [
      entry.detectorName || entry.groupName,
      entry.fileName,
    ]);
  }
  return window.gettext("Data visualization");
}
