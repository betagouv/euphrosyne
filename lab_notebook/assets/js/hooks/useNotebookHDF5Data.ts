import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { EuphrosyneFile } from "../../../../lab/assets/js/file-service";
import { RawDataFileService } from "../../../../lab/workplace/assets/js/raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../../../../lab/workplace/assets/js/processed-data/processed-data-file-service";
import type { IMeasuringPoint } from "../../../../shared/js/images/types";
import {
  createDatasetEntriesFromGroup,
  createHDF5FileSummaries,
  fetchHDF5Metadata,
  filterHDF5Files,
  findHDF5GroupMatches,
  HDF5DatasetEntry,
  HDF5Entity,
  HDF5FileRoot,
  HDF5FileSummary,
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
    ])
      .then(async ([rawDataFiles, processedDataFiles]) => {
        const runFiles = [...rawDataFiles, ...processedDataFiles];
        const hdf5Files = filterHDF5Files(runFiles);
        const rootMetadataResults = await Promise.allSettled(
          hdf5Files.map(async (file) => ({
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
        setRoots(loadedRoots);
        setError(
          failedMetadataCount > 0
            ? window.gettext("Some HDF5 file metadata could not be loaded.")
            : null,
        );
      })
      .catch((loadError: unknown) => {
        if (!isCurrent) {
          return;
        }
        console.error(loadError);
        setFiles([]);
        setRoots([]);
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

  const fileSummaries = useMemo(
    () => createHDF5FileSummaries(files, roots, pointKeys),
    [files, roots, pointKeys],
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
      Object.fromEntries(
        Object.entries(matchesByPointId).map(([pointId, matches]) => [
          pointId,
          matches.length > 0,
        ]),
      ),
    [matchesByPointId],
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
      if (matches.length === 0) {
        loadedPointIds.current.add(pointId);
        return;
      }

      setLoadingEntriesByPointId((previous) => ({
        ...previous,
        [pointId]: true,
      }));

      const promise = Promise.allSettled(
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
      )
        .then((entryResults) => {
          const entries = entryResults.flatMap((result) =>
            result.status === "fulfilled" ? result.value : [],
          );
          const failedGroupCount = entryResults.filter(
            (result) => result.status === "rejected",
          ).length;

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
    [fetchCachedMetadata, matchesByPointId],
  );

  if (!projectSlug || !runName) {
    return emptyNotebookHDF5Data;
  }

  return {
    files,
    fileSummaries,
    entriesByPointId,
    hasMatchesByPointId,
    loadingEntriesByPointId,
    isLoading,
    isLoadingEntries: Object.values(loadingEntriesByPointId).some(Boolean),
    error,
    loadEntriesForPoint,
  };
}
