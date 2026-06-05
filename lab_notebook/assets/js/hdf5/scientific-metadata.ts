import { ScientificMetadataRow } from "./types";

export const SCIENTIFIC_METADATA_FIELDS: Array<{
  key: string;
  labelText: string;
  attributeName: string;
}> = [
  {
    key: "particle",
    labelText: "Particle",
    attributeName: "particle",
  },
  {
    key: "beamEnergy",
    labelText: "Beam energy",
    attributeName: "beam energy",
  },
  {
    key: "targetType",
    labelText: "Target type",
    attributeName: "target type",
  },
  {
    key: "acquisitionTime",
    labelText: "Acquisition time",
    attributeName: "acquisition time (sec.)",
  },
  {
    key: "dose",
    labelText: "Dose",
    attributeName: "dose",
  },
  {
    key: "objectReference",
    labelText: "Object reference",
    attributeName: "obj euphrosyne",
  },
  {
    key: "analysisReference",
    labelText: "Analysis reference",
    attributeName: "ref. analyse",
  },
  {
    key: "timestamp",
    labelText: "Timestamp",
    attributeName: "timestamp",
  },
  {
    key: "institution",
    labelText: "Institution",
    attributeName: "institution",
  },
];

export function buildScientificMetadataRows(
  attributeValues: Record<string, unknown>,
): ScientificMetadataRow[] {
  return SCIENTIFIC_METADATA_FIELDS.flatMap(
    ({ key, labelText, attributeName }) => {
      const value = attributeValues[attributeName];
      if (value === undefined || value === null) {
        return [];
      }
      return [
        {
          key,
          label: window.gettext(labelText),
          value: formatAttributeValue(value),
        },
      ];
    },
  );
}

export function formatAttributeValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.map(formatAttributeValue).join(", ");
  }
  if (ArrayBuffer.isView(value) && !(value instanceof DataView)) {
    return Array.from(value as unknown as ArrayLike<unknown>)
      .map(formatAttributeValue)
      .join(", ");
  }
  if (typeof value === "object" && value !== null) {
    return JSON.stringify(value);
  }
  return String(value);
}
