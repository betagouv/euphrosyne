import { EuphrosyneFile } from "../../../../lab/assets/js/file-service";

type HDF5EntityKind = "group" | "dataset";

export interface HDF5Type {
  class: number;
  dtype: string;
  size: number;
  sign?: number;
  order?: number;
}

export interface HDF5Attribute {
  name: string;
  shape: number[];
  type: HDF5Type;
  value?: unknown;
}

interface HDF5BaseEntity {
  name: string;
  kind: HDF5EntityKind;
  path: string;
  attributes: HDF5Attribute[];
}

export interface HDF5Group extends HDF5BaseEntity {
  kind: "group";
  children: HDF5Entity[];
}

export interface HDF5Dataset extends HDF5BaseEntity {
  kind: "dataset";
  shape: number[];
  type: HDF5Type;
}

export type HDF5Entity = HDF5Group | HDF5Dataset;

export interface HDF5FileRoot {
  file: EuphrosyneFile;
  root: HDF5Entity | null;
}

export interface HDF5FileSummary {
  file: EuphrosyneFile;
  entryCount: number | null;
  coveredPointRange: string | null;
}

export interface MeasuringPointLike {
  id: string;
  name: string;
}

export interface HDF5GroupMatch {
  file: EuphrosyneFile;
  pointId: string;
  pointKey: string;
  group: HDF5Group;
  groupPath: string;
}

export type HDF5DatasetEntryKind = "spectrum" | "map";

export interface HDF5DatasetEntry {
  id: string;
  pointId: string;
  pointKey: string;
  fileName: string;
  filePath: string;
  groupName: string;
  groupPath: string;
  dataKind: HDF5DatasetEntryKind;
  dataKindLabel: string;
  datasetName: string;
  datasetPath: string;
  shape: number[];
  metadataSummary: string;
}

export interface ScientificMetadataRow {
  key: string;
  label: string;
  value: string;
}

export type ToolsFetch = (
  input: string | URL | globalThis.Request,
  init?: RequestInit,
) => Promise<Response>;
