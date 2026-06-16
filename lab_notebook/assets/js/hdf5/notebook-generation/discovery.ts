import type { EuphrosyneFile } from "../../../../../lab/assets/js/file-service";
import { ProcessedDataFileService } from "../../../../../lab/workplace/assets/js/processed-data/processed-data-file-service";
import { RawDataFileService } from "../../../../../lab/workplace/assets/js/raw-data/raw-data-file-service";
import type { ToolsFetch } from "../../../../../shared/js/euphrosyne-tools-client";
import { fetchHDF5AttributeValues, fetchHDF5Metadata } from "../hdf5-service";
import {
  createHDF5NotebookGenerationCandidates,
  filterHDF5Files,
} from "../notebook-hdf5";
import type {
  HDF5Attribute,
  HDF5Entity,
  HDF5FileRoot,
  HDF5Group,
} from "../types";
import type {
  DiscoverHDF5NotebookGenerationCandidatesOptions,
  HDF5NotebookGenerationDiscoveryResult,
} from "./types";

export async function discoverHDF5NotebookGenerationCandidates({
  projectSlug,
  runName,
  fetchFn,
}: DiscoverHDF5NotebookGenerationCandidatesOptions): Promise<HDF5NotebookGenerationDiscoveryResult> {
  const rawDataFileService = new RawDataFileService(
    projectSlug,
    runName,
    fetchFn,
  );
  const processedDataFileService = new ProcessedDataFileService(
    projectSlug,
    runName,
    fetchFn,
  );

  const [rawDataFiles, processedDataFiles] = await Promise.all([
    rawDataFileService.listData(),
    processedDataFileService.listData(),
  ]);
  const metadataFiles = deduplicateFilesByPath(
    filterHDF5Files([...rawDataFiles, ...processedDataFiles]),
  );
  const rootMetadataResults = await Promise.allSettled(
    metadataFiles.map(async (file) => ({
      file,
      root: await fetchHDF5Metadata(fetchFn, file.path, "/"),
    })),
  );
  const loadedRoots = rootMetadataResults.flatMap((result) =>
    result.status === "fulfilled" ? [result.value] : [],
  );
  const detailedRoots = await loadDetailedGenerationRoots(fetchFn, loadedRoots);

  return createHDF5NotebookGenerationCandidates([
    ...loadedRoots,
    ...detailedRoots,
  ]);
}

async function loadDetailedGenerationRoots(
  fetchFn: ToolsFetch,
  roots: HDF5FileRoot[],
): Promise<HDF5FileRoot[]> {
  const skippedCandidates =
    createHDF5NotebookGenerationCandidates(roots).skippedCandidates;
  const rootFileByPath = new Map(
    roots.map(({ file }) => [file.path, file] as const),
  );
  const requests = Array.from(
    new Map(
      skippedCandidates.map((candidate) => [
        `${candidate.filePath}:${candidate.groupPath}`,
        candidate,
      ]),
    ).values(),
  );

  const detailedMetadataResults = await Promise.allSettled(
    requests.map(async (candidate) => ({
      candidate,
      metadata: await hydrateEntityAttributeValues(
        fetchFn,
        candidate.filePath,
        await fetchHDF5Metadata(
          fetchFn,
          candidate.filePath,
          candidate.groupPath,
        ),
      ),
    })),
  );

  const groupsByFilePath = detailedMetadataResults.reduce<
    Record<string, HDF5Group[]>
  >((groups, result) => {
    if (
      result.status !== "fulfilled" ||
      result.value.metadata.kind !== "group"
    ) {
      return groups;
    }

    const { candidate, metadata } = result.value;
    groups[candidate.filePath] = groups[candidate.filePath] || [];
    groups[candidate.filePath].push(metadata);
    return groups;
  }, {});

  return Object.entries(groupsByFilePath).flatMap(([filePath, groups]) => {
    const file = rootFileByPath.get(filePath);
    if (!file) {
      return [];
    }

    return [
      {
        file,
        root: {
          name: "/",
          kind: "group" as const,
          path: "/",
          attributes: [],
          children: groups,
        },
      },
    ];
  });
}

async function hydrateEntityAttributeValues(
  fetchFn: ToolsFetch,
  filePath: string,
  entity: HDF5Entity,
): Promise<HDF5Entity> {
  if (entity.kind !== "group") {
    return hydrateEntityAttributes(
      entity,
      await fetchHDF5AttributeValues(fetchFn, filePath, entity.path),
    );
  }

  const [attributeValues, children] = await Promise.all([
    fetchHDF5AttributeValues(fetchFn, filePath, entity.path),
    Promise.all(
      entity.children.map((child) =>
        hydrateEntityAttributeValues(fetchFn, filePath, child),
      ),
    ),
  ]);

  return {
    ...entity,
    attributes: mergeAttributeValues(entity.attributes, attributeValues),
    children,
  };
}

function hydrateEntityAttributes(
  entity: HDF5Entity,
  attributeValues: Record<string, unknown>,
): HDF5Entity {
  return {
    ...entity,
    attributes: mergeAttributeValues(entity.attributes, attributeValues),
  };
}

function mergeAttributeValues(
  attributes: HDF5Attribute[],
  attributeValues: Record<string, unknown>,
): HDF5Attribute[] {
  const attributesByName = new Map(
    attributes.map((attribute) => [attribute.name, attribute] as const),
  );

  Object.entries(attributeValues).forEach(([name, value]) => {
    const attribute = attributesByName.get(name) || {
      name,
      shape: [],
      type: {
        class: 3,
        dtype: "|O",
        size: 8,
      },
    };
    attributesByName.set(name, {
      ...attribute,
      value,
    });
  });

  return Array.from(attributesByName.values());
}

function deduplicateFilesByPath(files: EuphrosyneFile[]): EuphrosyneFile[] {
  return Array.from(new Map(files.map((file) => [file.path, file])).values());
}
