export type ExternalObjectProvider = "eros" | "pop";

export interface Run {
  label: string;
  id: string;
}

interface ExternalObjectReference {
  id: string;
  providerName: ExternalObjectProvider;
  providerObjectId: string;
}

export interface ObjectGroup {
  id: string;
  label: string;
  objectCount: number;
  dating: string;
  materials: string[];
  externalReference: ExternalObjectReference | null;
}

export interface RunObjectGroup {
  id: string;
  objectGroup: ObjectGroup;
}
