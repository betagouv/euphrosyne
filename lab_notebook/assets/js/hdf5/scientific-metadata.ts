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
    key: "dosePerColumn",
    labelText: "Dose per column",
    attributeName: "dose/column",
  },
  {
    key: "mapSizeX",
    labelText: "Map size X",
    attributeName: "map size x (um)",
  },
  {
    key: "mapSizeY",
    labelText: "Map size Y",
    attributeName: "map size y (um)",
  },
  {
    key: "pixelSizeX",
    labelText: "Pixel size X",
    attributeName: "pixel size x (um)",
  },
  {
    key: "pixelSizeY",
    labelText: "Pixel size Y",
    attributeName: "pixel size y (um)",
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
  {
    key: "username",
    labelText: "Username",
    attributeName: "username",
  },
  {
    key: "adcName",
    labelText: "ADC name",
    attributeName: "adc name",
  },
  {
    key: "calibration",
    labelText: "Calibration",
    attributeName: "calibration",
  },
  {
    key: "detectorType",
    labelText: "Detector type",
    attributeName: "det. type",
  },
  {
    key: "detectorSerialNumber",
    labelText: "Detector serial number",
    attributeName: "det. S/N",
  },
  {
    key: "detectorActiveArea",
    labelText: "Detector active area",
    attributeName: "det. active area",
  },
  {
    key: "detectorAngle",
    labelText: "Detector angle",
    attributeName: "det. angle",
  },
  {
    key: "detectorEntranceWindow",
    labelText: "Detector entrance window",
    attributeName: "det. entrance window",
  },
  {
    key: "detectorFilter",
    labelText: "Detector filter",
    attributeName: "det. filter",
  },
  {
    key: "detectorThickness",
    labelText: "Detector thickness",
    attributeName: "det. thickness",
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
