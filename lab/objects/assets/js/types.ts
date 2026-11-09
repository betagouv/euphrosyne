export type ExternalObjectProvider = "eros" | "pop";

export interface Run {
  label: string;
  id: number;
}

interface ExternalObjectReference {
  id: number;
  providerName: ExternalObjectProvider;
  providerObjectId: string;
}

export interface ObjectGroup {
  id: number;
  label: string;
  objectCount: number;
  dating: string;
  materials: string[];
  externalReference: ExternalObjectReference | null;
}

export interface RunObjectGroup {
  id: number;
  objectGroup: ObjectGroup;
}
