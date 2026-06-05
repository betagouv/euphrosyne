import { EuphrosyneFile } from "../../../../lab/assets/js/file-service";
import {
  formatAttributeValue,
  SCIENTIFIC_METADATA_FIELDS,
} from "./scientific-metadata";
import {
  HDF5Attribute,
  HDF5DatasetEntry,
  HDF5DatasetEntryKind,
  HDF5Entity,
  HDF5FileRoot,
  HDF5FileSummary,
  HDF5Group,
  HDF5GroupMatch,
  MeasuringPointLike,
} from "./types";

const HDF5_INTEGER_TYPE_CLASS = 0;
const HDF5_FLOAT_TYPE_CLASS = 1;
const HDF5_EXTENSIONS = [".h5", ".hdf5"];
const HDF5_SPECTRUM_NAME_PATTERNS = [/^X\d+$/, /^G\d+$/, /^R\d+$/];
const SUPPORTED_DATASET_ENTRY_KINDS: HDF5DatasetEntryKind[] = ["spectrum"];

interface PointGroupReference {
  name: string;
  path: string;
  pointNumber: string;
  analysisReference: string | null;
}

interface HDF5Point extends PointGroupReference {
  metadata: Record<string, string>;
  spectra: HDF5SpectrumDataset[];
  maps: HDF5MapDataset[];
  images: HDF5ImageDataset[];
  auxiliaryGroups: HDF5AuxiliaryGroup[];
}

interface HDF5NotebookDatasetBase {
  name: string;
  path: string;
  kind: "dataset";
  shape: number[];
  dtype: string;
  metadata: Record<string, string>;
}

interface HDF5SpectrumDataset extends HDF5NotebookDatasetBase {
  dataKind: "spectrum";
}

interface HDF5MapDataset extends HDF5NotebookDatasetBase {
  dataKind: "map";
}

type HDF5NotebookDataset = HDF5SpectrumDataset | HDF5MapDataset;

interface HDF5ImageDataset {
  name: string;
  path: string;
  kind: "dataset";
  dataKind: "image";
  shape: number[];
  metadata: Record<string, string>;
}

interface HDF5AuxiliaryGroup {
  name: string;
  path: string;
  kind: "group";
  dataKind: "auxiliary";
  metadata: Record<string, string>;
}

export function filterHDF5Files(files: EuphrosyneFile[]): EuphrosyneFile[] {
  return files.filter((file) => {
    if (file.isDir) {
      return false;
    }
    const lowerName = file.name.toLowerCase();
    return HDF5_EXTENSIONS.some((extension) => lowerName.endsWith(extension));
  });
}

export function normalizeMeasuringPointName(name: string): string | null {
  const trimmedName = name.trim();
  if (!/^\d+$/.test(trimmedName)) {
    return null;
  }
  return trimmedName.padStart(4, "0");
}

export function createHDF5FileSummaries(
  files: EuphrosyneFile[],
  roots: HDF5FileRoot[],
  pointKeys: string[],
): HDF5FileSummary[] {
  function toPointGroupReferences(groups: HDF5Group[]): PointGroupReference[] {
    return groups.flatMap((group) => {
      const pointGroup = toPointGroupReference(group);
      return pointGroup ? [pointGroup] : [];
    });
  }

  const rootByPath = new Map(roots.map(({ file, root }) => [file.path, root]));

  return files.map((file) => {
    const root = rootByPath.get(file.path) || null;
    const points = toPointGroupReferences(getChildGroups(root));
    const coveredPointKeys = points
      .map(({ pointNumber }) => pointNumber)
      .filter((pointNumber) => pointKeys.includes(pointNumber));

    return {
      file,
      entryCount: root ? points.length : null,
      coveredPointRange: getCoveredPointRange(coveredPointKeys),
    };
  });
}

export function findHDF5GroupMatches(
  roots: HDF5FileRoot[],
  points: MeasuringPointLike[],
): HDF5GroupMatch[] {
  const pointsByKey = indexMeasuringPointsByKey(points);

  return roots.flatMap(({ file, root }) =>
    getChildGroups(root).flatMap((group) => {
      const pointGroup = toPointGroupReference(group);
      if (!pointGroup) {
        return [];
      }

      const matchingPoint = pointsByKey.get(pointGroup.pointNumber);
      if (!matchingPoint) {
        return [];
      }

      return [
        {
          file,
          pointId: matchingPoint.id,
          pointKey: pointGroup.pointNumber,
          group,
          groupPath: group.path,
        },
      ];
    }),
  );
}

export function createDatasetEntriesFromGroup(
  match: HDF5GroupMatch,
  groupMetadata: HDF5Entity,
): HDF5DatasetEntry[] {
  if (groupMetadata.kind !== "group") {
    return [];
  }

  const point = createHDF5Point(groupMetadata);
  if (!point) {
    return [];
  }

  return getSupportedDatasets(point).map((dataset) =>
    createDatasetEntry(match, dataset),
  );
}

function createDatasetEntry(
  match: HDF5GroupMatch,
  dataset: HDF5NotebookDataset,
): HDF5DatasetEntry {
  return {
    id: `${match.file.path}:${dataset.path}`,
    pointId: match.pointId,
    pointKey: match.pointKey,
    fileName: match.file.name,
    filePath: match.file.path,
    groupName: match.group.name,
    groupPath: match.groupPath,
    dataKind: dataset.dataKind,
    dataKindLabel: getDatasetKindLabel(dataset.dataKind),
    datasetName: dataset.name,
    datasetPath: dataset.path,
    shape: dataset.shape,
    metadataSummary: getMetadataSummary(dataset),
  };
}

function indexMeasuringPointsByKey(points: MeasuringPointLike[]) {
  return points.reduce<Map<string, MeasuringPointLike>>(
    (pointsByKey, point) => {
      const pointKey = normalizeMeasuringPointName(point.name);
      if (pointKey) {
        pointsByKey.set(pointKey, point);
      }
      return pointsByKey;
    },
    new Map(),
  );
}

function getSupportedDatasets(point: HDF5Point): HDF5NotebookDataset[] {
  return [...point.spectra, ...point.maps].filter((dataset) =>
    SUPPORTED_DATASET_ENTRY_KINDS.includes(dataset.dataKind),
  );
}

function getChildGroups(entity: HDF5Entity | null): HDF5Group[] {
  if (!entity || entity.kind !== "group") {
    return [];
  }
  return entity.children.filter(
    (child): child is HDF5Group => child.kind === "group",
  );
}

function createHDF5Point(group: HDF5Group): HDF5Point | null {
  const pointGroup = toPointGroupReference(group);
  if (!pointGroup) {
    return null;
  }

  const children = classifyPointChildren(group.children);
  return {
    ...pointGroup,
    metadata: createMetadataRecord(group.attributes),
    ...children,
  };
}

function toPointGroupReference(group: HDF5Group): PointGroupReference | null {
  const parsedName = parsePointGroupName(group.name);
  if (!parsedName) {
    return null;
  }

  return {
    name: group.name,
    path: group.path,
    pointNumber: parsedName.pointNumber,
    analysisReference: parsedName.analysisReference,
  };
}

function parsePointGroupName(
  name: string,
): { pointNumber: string; analysisReference: string | null } | null {
  const match = name.match(/^\d{8}_(\d{4})(?:_(.+))?$/);
  if (!match) {
    return null;
  }
  return {
    pointNumber: match[1],
    analysisReference: match[2] || null,
  };
}

function classifyPointChildren(children: HDF5Entity[]) {
  const spectra: HDF5SpectrumDataset[] = [];
  const maps: HDF5MapDataset[] = [];
  const images: HDF5ImageDataset[] = [];
  const auxiliaryGroups: HDF5AuxiliaryGroup[] = [];

  children.forEach((child) => {
    const spectrum = createHDF5SpectrumDataset(child);
    if (spectrum) {
      spectra.push(spectrum);
      return;
    }

    const image = createHDF5ImageDataset(child);
    if (image) {
      images.push(image);
      return;
    }

    const map = createHDF5MapDataset(child);
    if (map) {
      maps.push(map);
      return;
    }

    const auxiliaryGroup = createHDF5AuxiliaryGroup(child);
    if (auxiliaryGroup) {
      auxiliaryGroups.push(auxiliaryGroup);
    }
  });

  return { spectra, maps, images, auxiliaryGroups };
}

function createHDF5SpectrumDataset(
  entity: HDF5Entity,
): HDF5SpectrumDataset | null {
  const isNumericType =
    entity.kind === "dataset" &&
    (entity.type.class === HDF5_INTEGER_TYPE_CLASS ||
      entity.type.class === HDF5_FLOAT_TYPE_CLASS);

  if (
    entity.kind !== "dataset" ||
    entity.shape.length !== 1 ||
    entity.shape[0] <= 0 ||
    !isNumericType ||
    !HDF5_SPECTRUM_NAME_PATTERNS.some((pattern) => pattern.test(entity.name))
  ) {
    return null;
  }

  return {
    name: entity.name,
    path: entity.path,
    kind: "dataset",
    dataKind: "spectrum",
    shape: entity.shape,
    dtype: entity.type.dtype,
    metadata: createMetadataRecord(entity.attributes),
  };
}

function createHDF5MapDataset(entity: HDF5Entity): HDF5MapDataset | null {
  const isNumericType =
    entity.kind === "dataset" &&
    (entity.type.class === HDF5_INTEGER_TYPE_CLASS ||
      entity.type.class === HDF5_FLOAT_TYPE_CLASS);

  if (
    entity.kind !== "dataset" ||
    entity.shape.length !== 2 ||
    entity.shape.some((dimension) => dimension <= 0) ||
    !isNumericType
  ) {
    return null;
  }

  return {
    name: entity.name,
    path: entity.path,
    kind: "dataset",
    dataKind: "map",
    shape: entity.shape,
    dtype: entity.type.dtype,
    metadata: createMetadataRecord(entity.attributes),
  };
}

function createHDF5ImageDataset(entity: HDF5Entity): HDF5ImageDataset | null {
  if (
    entity.kind !== "dataset" ||
    (entity.shape.length !== 2 && entity.shape.length !== 3)
  ) {
    return null;
  }

  const attributeNames = entity.attributes.map(({ name }) => name);
  const isImage =
    entity.name.includes("image") ||
    attributeNames.includes("CLASS") ||
    attributeNames.includes("IMAGE_SUBCLASS") ||
    attributeNames.includes("IMAGE_VERSION");

  if (!isImage) {
    return null;
  }

  return {
    name: entity.name,
    path: entity.path,
    kind: "dataset",
    dataKind: "image",
    shape: entity.shape,
    metadata: createMetadataRecord(entity.attributes),
  };
}

function createHDF5AuxiliaryGroup(
  entity: HDF5Entity,
): HDF5AuxiliaryGroup | null {
  if (entity.kind !== "group") {
    return null;
  }

  return {
    name: entity.name,
    path: entity.path,
    kind: "group",
    dataKind: "auxiliary",
    metadata: createMetadataRecord(entity.attributes),
  };
}

function createMetadataRecord(
  attributes: HDF5Attribute[],
): Record<string, string> {
  return Object.fromEntries(
    attributes.map(({ name, value }) => [
      name,
      value === undefined ? "" : formatAttributeValue(value),
    ]),
  );
}

function getCoveredPointRange(coveredPointKeys: string[]): string | null {
  const uniqueKeys = Array.from(new Set(coveredPointKeys)).sort();
  if (uniqueKeys.length === 0) {
    return null;
  }
  if (uniqueKeys.length === 1) {
    return uniqueKeys[0];
  }
  return `${uniqueKeys[0]} - ${uniqueKeys[uniqueKeys.length - 1]}`;
}

function getDatasetKindLabel(dataKind: HDF5DatasetEntryKind): string {
  if (dataKind === "map") {
    return window.gettext("Map");
  }
  return window.gettext("Spectrum");
}

function getMetadataSummary(entity: HDF5NotebookDataset): string {
  if (entity.dataKind === "map") {
    return getMapMetadataSummary(entity);
  }
  return getSpectrumMetadataSummary(entity);
}

function getSpectrumMetadataSummary(entity: HDF5SpectrumDataset): string {
  const parts = [
    window.interpolate(window.gettext("%s channels"), [
      entity.shape[0].toString(),
    ]),
  ];

  const attributeNames = Object.keys(entity.metadata).filter((name) =>
    SCIENTIFIC_METADATA_FIELDS.some(
      ({ attributeName }) => attributeName === name,
    ),
  );
  if (attributeNames.length > 0) {
    parts.push(attributeNames.slice(0, 3).join(", "));
  }

  return parts.join(" · ");
}

function getMapMetadataSummary(entity: HDF5MapDataset): string {
  return window.interpolate(window.gettext("%s map"), [
    entity.shape.join(" x "),
  ]);
}
