import { ScientificMetadataRow } from "./types";

type ScientificMetadataField = {
  key: string;
  labelText: string;
  attributeName: string;
};

export function getScientificMetadataFields(): ScientificMetadataField[] {
  return [
    {
      key: "particle",
      labelText: window.gettext("Particle"),
      attributeName: "particle",
    },
    {
      key: "beamEnergy",
      labelText: window.gettext("Beam energy"),
      attributeName: "beam energy",
    },
    {
      key: "targetType",
      labelText: window.gettext("Target type"),
      attributeName: "target type",
    },
    {
      key: "acquisitionTime",
      labelText: window.gettext("Acquisition time"),
      attributeName: "acquisition time (sec.)",
    },
    {
      key: "dose",
      labelText: window.gettext("Dose"),
      attributeName: "dose",
    },
    {
      key: "dosePerColumn",
      labelText: window.gettext("Dose per column"),
      attributeName: "dose/column",
    },
    {
      key: "mapSizeX",
      labelText: window.gettext("Map size X"),
      attributeName: "map size x (um)",
    },
    {
      key: "mapSizeY",
      labelText: window.gettext("Map size Y"),
      attributeName: "map size y (um)",
    },
    {
      key: "pixelSizeX",
      labelText: window.gettext("Pixel size X"),
      attributeName: "pixel size x (um)",
    },
    {
      key: "pixelSizeY",
      labelText: window.gettext("Pixel size Y"),
      attributeName: "pixel size y (um)",
    },
    {
      key: "objectReference",
      labelText: window.gettext("Object reference"),
      attributeName: "obj euphrosyne",
    },
    {
      key: "analysisReference",
      labelText: window.gettext("Analysis reference"),
      attributeName: "ref. analyse",
    },
    {
      key: "timestamp",
      labelText: window.gettext("Timestamp"),
      attributeName: "timestamp",
    },
    {
      key: "institution",
      labelText: window.gettext("Institution"),
      attributeName: "institution",
    },
    {
      key: "username",
      labelText: window.gettext("Username"),
      attributeName: "username",
    },
    {
      key: "adcName",
      labelText: window.gettext("ADC name"),
      attributeName: "adc name",
    },
    {
      key: "calibration",
      labelText: window.gettext("Calibration"),
      attributeName: "calibration",
    },
    {
      key: "detectorType",
      labelText: window.gettext("Detector type"),
      attributeName: "det. type",
    },
    {
      key: "detectorSerialNumber",
      labelText: window.gettext("Detector serial number"),
      attributeName: "det. S/N",
    },
    {
      key: "detectorActiveArea",
      labelText: window.gettext("Detector active area"),
      attributeName: "det. active area",
    },
    {
      key: "detectorAngle",
      labelText: window.gettext("Detector angle"),
      attributeName: "det. angle",
    },
    {
      key: "detectorEntranceWindow",
      labelText: window.gettext("Detector entrance window"),
      attributeName: "det. entrance window",
    },
    {
      key: "detectorFilter",
      labelText: window.gettext("Detector filter"),
      attributeName: "det. filter",
    },
    {
      key: "detectorThickness",
      labelText: window.gettext("Detector thickness"),
      attributeName: "det. thickness",
    },
  ];
}

export function buildScientificMetadataRows(
  attributeValues: Record<string, unknown>,
): ScientificMetadataRow[] {
  return getScientificMetadataFields().flatMap(
    ({ key, labelText, attributeName }) => {
      const value = attributeValues[attributeName];
      if (value === undefined || value === null) {
        return [];
      }
      return [
        {
          key,
          label: labelText,
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
