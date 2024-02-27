export interface Run {
  label: string;
  id: string;
}

export interface ObjectGroup {
  id: string;
  label: string;
  objectCount: number;
  dating: string;
  materials: string[];
}

export interface RunObjectGroup {
  id: string;
  objectGroup: ObjectGroup;
}
