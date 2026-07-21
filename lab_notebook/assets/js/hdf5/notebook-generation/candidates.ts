import {
  getHDF5ChildGroups,
  getHDF5PointGroupReference,
} from "../notebook-hdf5";
import { formatAttributeValue } from "../scientific-metadata";
import type {
  HDF5Attribute,
  HDF5Entity,
  HDF5FileRoot,
  HDF5Group,
  HDF5NotebookGenerationAnalysisType,
  HDF5NotebookGenerationCandidate,
  HDF5NotebookGenerationCandidates,
  HDF5NotebookGenerationSkippedCandidate,
} from "../types";

/**
 * Creates notebook-generation candidates from loaded HDF5 point-group roots.
 */
export function createHDF5NotebookGenerationCandidates(
  roots: HDF5FileRoot[],
): HDF5NotebookGenerationCandidates {
  const candidatesByPointKey = new Map<
    string,
    HDF5NotebookGenerationCandidate
  >();
  const skippedCandidates: HDF5NotebookGenerationSkippedCandidate[] = [];

  roots.forEach(({ file, root }) => {
    getHDF5ChildGroups(root).forEach((group) => {
      const pointGroup = getHDF5PointGroupReference(group);
      if (!pointGroup) {
        return;
      }

      const metadata = createGenerationMetadataRecord(group);
      const targetType = getGenerationTargetType(metadata);
      const analysisType = normalizeGenerationAnalysisType(targetType);
      const id = `${file.path}:${group.path}`;

      if (!analysisType) {
        skippedCandidates.push({
          id,
          fileName: file.name,
          filePath: file.path,
          groupName: group.name,
          groupPath: group.path,
          pointKey: pointGroup.pointNumber,
          reason: window.interpolate(
            window.gettext("Unsupported HDF5 target type: %s"),
            [targetType || window.gettext("missing")],
          ),
        });
        return;
      }

      if (candidatesByPointKey.has(pointGroup.pointNumber)) {
        return;
      }

      candidatesByPointKey.set(pointGroup.pointNumber, {
        id,
        fileName: file.name,
        filePath: file.path,
        groupName: group.name,
        groupPath: group.path,
        pointKey: pointGroup.pointNumber,
        pointName: pointGroup.pointNumber.replace(/^0(?=\d{3}$)/, ""),
        analysisType,
        comment: normalizeGenerationMetadataValue(
          metadata["analyse description"],
        ),
        referenceLabel: normalizeGenerationMetadataValue(
          metadata["ref. analyse"],
        ),
      });
    });
  });

  const candidates = Array.from(candidatesByPointKey.values()).sort(
    (left, right) => left.pointKey.localeCompare(right.pointKey),
  );
  const candidatePointKeys = new Set(
    candidates.map(({ pointKey }) => pointKey),
  );

  return {
    candidates,
    skippedCandidates: deduplicateSkippedGenerationCandidates(
      skippedCandidates.filter(
        ({ pointKey }) => !candidatePointKeys.has(pointKey),
      ),
    ),
  };
}

function createGenerationMetadataRecord(
  group: HDF5Group,
): Record<string, string> {
  const metadata = createMetadataRecord(group.attributes);

  function fillFromEntity(entity: HDF5Entity) {
    const entityMetadata = createMetadataRecord(entity.attributes);
    Object.entries(entityMetadata).forEach(([key, value]) => {
      if (metadata[key] === undefined || metadata[key] === "") {
        metadata[key] = value;
      }
    });

    if (entity.kind === "group") {
      entity.children.forEach(fillFromEntity);
    }
  }

  group.children.forEach(fillFromEntity);

  return metadata;
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

function getGenerationTargetType(metadata: Record<string, string>) {
  return metadata["target type"] || metadata["obj euphrosyne"];
}

function normalizeGenerationAnalysisType(
  value: string | undefined,
): HDF5NotebookGenerationAnalysisType | null {
  const normalizedValue = value?.trim().toLowerCase();
  if (normalizedValue === "object" || normalizedValue === "objet") {
    return "object";
  }
  if (normalizedValue === "standard" || normalizedValue === "std") {
    return "standard";
  }
  return null;
}

function normalizeGenerationMetadataValue(value: string | undefined) {
  const trimmedValue = value?.trim();
  return trimmedValue ? trimmedValue : null;
}

function deduplicateSkippedGenerationCandidates(
  candidates: HDF5NotebookGenerationSkippedCandidate[],
) {
  return Array.from(
    new Map(
      candidates.map((candidate) => [
        `${candidate.filePath}:${candidate.groupPath}`,
        candidate,
      ]),
    ).values(),
  );
}
