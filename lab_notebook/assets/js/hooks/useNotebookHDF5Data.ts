import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { EuphrosyneFile } from "../../../../lab/assets/js/file-service";
import { RawDataFileService } from "../../../../lab/workplace/assets/js/raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../../../../lab/workplace/assets/js/processed-data/processed-data-file-service";
import type { IMeasuringPoint } from "../../../../shared/js/images/types";
import {
  createDatasetEntriesFromGroup,
  createHDF5FileSummaries,
  createMapDatasetEntryFromDetectorDataset,
  createMapDatasetEntriesFromRoot,
  fetchHDF5Metadata,
  filterHDF5Files,
  filterHDF5MapFiles,
  findHDF5GroupMatches,
  HDF5DatasetEntry,
  HDF5Entity,
  HDF5FileRoot,
  HDF5FileSummary,
  HDF5Group,
  HDF5GroupMatch,
  normalizeMeasuringPointName,
  ToolsFetch,
} from "../hdf5";

interface NotebookHDF5Data {
  files: EuphrosyneFile[];
  fileSummaries: HDF5FileSummary[];
  entriesByPointId: Record<string, HDF5DatasetEntry[]>;
  hasMatchesByPointId: Record<string, boolean>;
  loadingEntriesByPointId: Record<string, boolean>;
  isLoading: boolean;
  isLoadingEntries: boolean;
  error: string | null;
  loadEntriesForPoint: (pointId: string) => Promise<void>;
}

const emptyNotebookHDF5Data: NotebookHDF5Data = {
  files: [],
  fileSummaries: [],
  entriesByPointId: {},
  hasMatchesByPointId: {},
  loadingEntriesByPointId: {},
  isLoading: false,
  isLoadingEntries: false,
  error: null,
  loadEntriesForPoint: async () => {},
};

export default function useNotebookHDF5Data({
  projectSlug,
  runName,
  measuringPoints,
  fetchFn,
}: {
  projectSlug: string;
  runName: string;
  measuringPoints: IMeasuringPoint[];
  fetchFn: ToolsFetch;
}): NotebookHDF5Data {
  const [files, setFiles] = useState<EuphrosyneFile[]>([]);
  const [mapFiles, setMapFiles] = useState<EuphrosyneFile[]>([]);
  const [discoveredMapEntries, setDiscoveredMapEntries] = useState<
    HDF5DatasetEntry[]
  >([]);
  const [roots, setRoots] = useState<HDF5FileRoot[]>([]);
  const [entriesByPointId, setEntriesByPointId] = useState<
    Record<string, HDF5DatasetEntry[]>
  >({});
  const [isLoading, setIsLoading] = useState(false);
  const [loadingEntriesByPointId, setLoadingEntriesByPointId] = useState<
    Record<string, boolean>
  >({});
  const [error, setError] = useState<string | null>(null);
  const groupMetadataCache = useRef<Map<string, Promise<HDF5Entity>>>(
    new Map(),
  );
  const loadedPointIds = useRef<Set<string>>(new Set());
  const loadingPointPromises = useRef<Map<string, Promise<void>>>(new Map());

  useEffect(() => {
    let isCurrent = true;
    if (!projectSlug || !runName) {
      setFiles([]);
      setMapFiles([]);
      setDiscoveredMapEntries([]);
      setRoots([]);
      setEntriesByPointId({});
      setLoadingEntriesByPointId({});
      setError(null);
      setIsLoading(false);
      loadedPointIds.current.clear();
      loadingPointPromises.current.clear();
      return () => {
        isCurrent = false;
      };
    }

    setIsLoading(true);
    setError(null);
    setDiscoveredMapEntries([]);
    setEntriesByPointId({});
    setLoadingEntriesByPointId({});
    groupMetadataCache.current.clear();
    loadedPointIds.current.clear();
    loadingPointPromises.current.clear();

    const rawDataFileService = new RawDataFileService(
      projectSlug,
      runName,
      fetchFn as typeof fetch,
    );
    const processedDataFileService = new ProcessedDataFileService(
      projectSlug,
      runName,
      fetchFn as typeof fetch,
    );

    Promise.all([
      rawDataFileService.listData(),
      processedDataFileService.listData(),
      rawDataFileService.listData("HDF5_maps_files"),
      processedDataFileService.listData("HDF5_maps_files"),
    ])
      .then(
        async ([
          rawDataFiles,
          processedDataFiles,
          rawMapFiles,
          processedMapFiles,
        ]) => {
          const runFiles = [...rawDataFiles, ...processedDataFiles];
          const hdf5Files = filterHDF5Files(runFiles);
          const hdf5MapFiles = filterHDF5MapFiles([
            ...rawMapFiles,
            ...processedMapFiles,
          ]);
          const metadataFiles = deduplicateFilesByPath(hdf5Files);
          const rootMetadataResults = await Promise.allSettled(
            metadataFiles.map(async (file) => ({
              file,
              root: await fetchHDF5Metadata(fetchFn, file.path, "/"),
            })),
          );

          if (!isCurrent) {
            return;
          }

          const loadedRoots = rootMetadataResults.flatMap((result) =>
            result.status === "fulfilled" ? [result.value] : [],
          );
          const failedMetadataCount = rootMetadataResults.filter(
            (result) => result.status === "rejected",
          ).length;

          setFiles(hdf5Files);
          setMapFiles(hdf5MapFiles);
          setRoots(loadedRoots);
          setError(
            failedMetadataCount > 0
              ? window.gettext("Some HDF5 file metadata could not be loaded.")
              : null,
          );
        },
      )
      .catch((loadError: unknown) => {
        if (!isCurrent) {
          return;
        }
        console.error(loadError);
        setFiles([]);
        setRoots([]);
        setMapFiles([]);
        setDiscoveredMapEntries([]);
        setError(window.gettext("HDF5 data could not be loaded."));
      })
      .finally(() => {
        if (isCurrent) {
          setIsLoading(false);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [projectSlug, runName, fetchFn]);

  const pointKeys = useMemo(
    () =>
      measuringPoints.flatMap((point) => {
        const pointKey = normalizeMeasuringPointName(point.name);
        return pointKey ? [pointKey] : [];
      }),
    [measuringPoints],
  );

  const pointIdByPointKey = useMemo(
    () =>
      new Map(
        measuringPoints.flatMap((point) => {
          const pointKey = normalizeMeasuringPointName(point.name);
          return pointKey ? [[pointKey, point.id] as const] : [];
        }),
      ),
    [measuringPoints],
  );

  const mapEntries = useMemo(
    () =>
      discoveredMapEntries.map((entry) => {
        const pointKey = getPointKeyFromHDF5FileName(entry.fileName);
        const pointId = pointKey ? pointIdByPointKey.get(pointKey) || "" : "";
        return {
          ...entry,
          pointId,
          pointKey: pointKey || "",
        };
      }),
    [discoveredMapEntries, pointIdByPointKey],
  );

  const mapFilesByPointId = useMemo(
    () =>
      mapFiles.reduce<Record<string, EuphrosyneFile[]>>((accumulator, file) => {
        const pointKey = getPointKeyFromHDF5FileName(file.name);
        const pointId = pointKey ? pointIdByPointKey.get(pointKey) || "" : "";
        if (!pointId) {
          return accumulator;
        }
        accumulator[pointId] = accumulator[pointId] || [];
        accumulator[pointId].push(file);
        return accumulator;
      }, {}),
    [mapFiles, pointIdByPointKey],
  );

  const fileSummaries = useMemo(
    () => [
      ...createHDF5FileSummaries(files, roots, pointKeys),
      ...createMapFileSummaries(mapFiles, mapEntries),
    ],
    [files, mapEntries, mapFiles, roots, pointKeys],
  );

  const mapEntriesByPointId = useMemo(
    () =>
      mapEntries.reduce<Record<string, HDF5DatasetEntry[]>>(
        (accumulator, entry) => {
          if (!entry.pointId) {
            return accumulator;
          }
          accumulator[entry.pointId] = accumulator[entry.pointId] || [];
          accumulator[entry.pointId].push(entry);
          return accumulator;
        },
        {},
      ),
    [mapEntries],
  );

  const matchesByPointId = useMemo(
    () =>
      findHDF5GroupMatches(roots, measuringPoints).reduce<
        Record<string, HDF5GroupMatch[]>
      >((accumulator, match) => {
        accumulator[match.pointId] = accumulator[match.pointId] || [];
        accumulator[match.pointId].push(match);
        return accumulator;
      }, {}),
    [roots, measuringPoints],
  );

  const hasMatchesByPointId = useMemo(
    () =>
      Array.from(
        new Set([
          ...Object.keys(matchesByPointId),
          ...Object.keys(mapFilesByPointId),
          ...Object.keys(mapEntriesByPointId),
        ]),
      ).reduce<Record<string, boolean>>((accumulator, pointId) => {
        accumulator[pointId] =
          (matchesByPointId[pointId] || []).length > 0 ||
          (mapFilesByPointId[pointId] || []).length > 0 ||
          (mapEntriesByPointId[pointId] || []).length > 0;
        return accumulator;
      }, {}),
    [mapEntriesByPointId, mapFilesByPointId, matchesByPointId],
  );

  const fetchCachedMetadata = useCallback(
    (filePath: string, path: string) => {
      const cacheKey = `${filePath}:${path}`;
      if (!groupMetadataCache.current.has(cacheKey)) {
        groupMetadataCache.current.set(
          cacheKey,
          fetchHDF5Metadata(fetchFn, filePath, path),
        );
      }
      return groupMetadataCache.current.get(cacheKey);
    },
    [fetchFn],
  );

  const loadEntriesForPoint = useCallback(
    async (pointId: string) => {
      if (loadedPointIds.current.has(pointId)) {
        return;
      }

      const inFlightPromise = loadingPointPromises.current.get(pointId);
      if (inFlightPromise) {
        return inFlightPromise;
      }

      const matches = matchesByPointId[pointId] || [];
      const pointMapFiles = mapFilesByPointId[pointId] || [];
      if (matches.length === 0 && pointMapFiles.length === 0) {
        loadedPointIds.current.add(pointId);
        return;
      }

      setLoadingEntriesByPointId((previous) => ({
        ...previous,
        [pointId]: true,
      }));

      const spectraEntriesPromise = Promise.allSettled(
        matches.map(async (match) => {
          const groupMetadata = await fetchCachedMetadata(
            match.file.path,
            match.groupPath,
          );
          if (!groupMetadata) {
            return [];
          }

          const directEntries = createDatasetEntriesFromGroup(
            match,
            groupMetadata,
          );

          return directEntries;
        }),
      );
      const mapEntriesPromise = Promise.allSettled(
        pointMapFiles.map(async (file) => {
          const rootMetadata = await fetchCachedMetadata(file.path, "/");
          if (!rootMetadata) {
            return [];
          }
          return discoverMapEntriesForFile(fetchFn, file, rootMetadata);
        }),
      );

      const promise = Promise.all([spectraEntriesPromise, mapEntriesPromise])
        .then(([entryResults, mapEntryResults]) => {
          const entries = entryResults.flatMap((result) =>
            result.status === "fulfilled" ? result.value : [],
          );
          const discoveredEntries = mapEntryResults.flatMap((result) =>
            result.status === "fulfilled" ? result.value : [],
          );
          const failedGroupCount =
            entryResults.filter((result) => result.status === "rejected")
              .length +
            mapEntryResults.filter((result) => result.status === "rejected")
              .length;

          if (discoveredEntries.length > 0) {
            setDiscoveredMapEntries((previous) =>
              deduplicateEntriesById([...previous, ...discoveredEntries]),
            );
          }

          setEntriesByPointId((previous) => ({
            ...previous,
            [pointId]: entries,
          }));
          loadedPointIds.current.add(pointId);

          if (failedGroupCount > 0) {
            setError(
              window.gettext(
                "Some HDF5 measurement point metadata could not be loaded.",
              ),
            );
          }
        })
        .finally(() => {
          loadingPointPromises.current.delete(pointId);
          setLoadingEntriesByPointId((previous) => ({
            ...previous,
            [pointId]: false,
          }));
        });

      loadingPointPromises.current.set(pointId, promise);
      return promise;
    },
    [fetchCachedMetadata, fetchFn, mapFilesByPointId, matchesByPointId],
  );

  if (!projectSlug || !runName) {
    return emptyNotebookHDF5Data;
  }

  const combinedEntriesByPointId = {
    ...entriesByPointId,
    ...Object.fromEntries(
      Object.entries(mapEntriesByPointId).map(([pointId, entries]) => [
        pointId,
        [...(entriesByPointId[pointId] || []), ...entries],
      ]),
    ),
  };

  return {
    files,
    fileSummaries,
    entriesByPointId: combinedEntriesByPointId,
    hasMatchesByPointId,
    loadingEntriesByPointId,
    isLoading,
    isLoadingEntries: Object.values(loadingEntriesByPointId).some(Boolean),
    error,
    loadEntriesForPoint,
  };
}

function createMapFileSummaries(
  mapFiles: EuphrosyneFile[],
  mapEntries: HDF5DatasetEntry[],
): HDF5FileSummary[] {
  return mapFiles.map((file) => {
    const fileMapEntries = mapEntries.filter(
      (entry) => entry.filePath === file.path,
    );
    return {
      file,
      entryCount: fileMapEntries.length > 0 ? fileMapEntries.length : null,
      coveredPointRange: getPointKeyFromHDF5FileName(file.name),
    };
  });
}

function getPointKeyFromHDF5FileName(fileName: string): string | null {
  const match = fileName.match(/^\d{8}_(\d{4})(?:_|\.|$)/);
  return match ? match[1] : null;
}

function deduplicateFilesByPath(files: EuphrosyneFile[]): EuphrosyneFile[] {
  return Array.from(new Map(files.map((file) => [file.path, file])).values());
}

function deduplicateEntriesById(
  entries: HDF5DatasetEntry[],
): HDF5DatasetEntry[] {
  return Array.from(
    new Map(entries.map((entry) => [entry.id, entry])).values(),
  );
}

async function discoverMapEntriesForFile(
  fetchFn: ToolsFetch,
  file: EuphrosyneFile,
  root: HDF5Entity | null | undefined,
): Promise<HDF5DatasetEntry[]> {
  if (!root || root.kind !== "group") {
    return [];
  }

  const entriesById = new Map<string, HDF5DatasetEntry>();
  const visitedPaths = new Set<string>();

  async function visitGroup(group: HDF5Group, depth: number): Promise<void> {
    if (visitedPaths.has(group.path)) {
      return;
    }
    visitedPaths.add(group.path);

    createMapDatasetEntriesFromRoot(file, group).forEach((entry) => {
      entriesById.set(entry.id, entry);
    });

    if (depth >= 2) {
      return;
    }

    const childGroups = group.children.filter(
      (child): child is HDF5Group => child.kind === "group",
    );
    const detectorGroups = childGroups.filter(({ name }) =>
      isMapDetectorGroupName(name),
    );
    const childMetadataResults = await Promise.allSettled(
      childGroups.map((child) =>
        fetchHDF5Metadata(fetchFn, file.path, child.path),
      ),
    );
    const directMapDatasetResults = await Promise.allSettled(
      detectorGroups.map(async (detector) => ({
        detector,
        dataset: await fetchHDF5Metadata(
          fetchFn,
          file.path,
          `${detector.path}/maps`,
        ),
      })),
    );

    directMapDatasetResults.forEach((result) => {
      if (result.status !== "fulfilled") {
        return;
      }
      createMapDatasetEntryFromDetectorDataset(
        file,
        group,
        result.value.detector,
        result.value.dataset,
      ).forEach((entry) => {
        entriesById.set(entry.id, entry);
      });
    });

    await Promise.all(
      childMetadataResults.map((result) =>
        result.status === "fulfilled" && result.value.kind === "group"
          ? visitGroup(result.value, depth + 1)
          : Promise.resolve(),
      ),
    );
  }

  await visitGroup(root, 0);
  return Array.from(entriesById.values());
}

function isMapDetectorGroupName(name: string): boolean {
  return /^(?:X\d+|RBS\d+|GAMMA\d+)$/i.test(name);
}
