import { useEffect, useMemo, useState } from "react";
import { EuphrosyneFile } from "../../../lab/assets/js/file-service";
import { RawDataFileService } from "../../../lab/workplace/assets/js/raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../../../lab/workplace/assets/js/processed-data/processed-data-file-service";

export interface GroupedRunDataFiles {
  global: EuphrosyneFile[];
  byMeasuringPoint: Record<string, EuphrosyneFile[]>;
}

export interface RunDataFiles {
  raw: GroupedRunDataFiles;
  processed: GroupedRunDataFiles;
}

const FILE_POINT_PATTERN = /^\d{8}_(\d{4})_/;
const EXCEL_LIKE_EXTENSIONS = new Set(["csv", "xls", "xlsx"]);
const HDF5_EXTENSIONS = new Set(["h5", "hdf5"]);

function getFileExtension(fileName: string): string {
  return fileName.split(".").pop()?.toLowerCase() || "";
}

function getSortPriority(file: EuphrosyneFile): number {
  if (file.isDir) return 0;

  const extension = getFileExtension(file.name);
  if (EXCEL_LIKE_EXTENSIONS.has(extension)) return 1;
  if (HDF5_EXTENSIONS.has(extension)) return 2;
  return 3;
}

export function normalizeMeasuringPointName(name: string): string | null {
  const match = name.trim().match(/^\d+$/);
  if (!match) return null;
  return match[0].padStart(4, "0");
}

export function parseMeasuringPointSegment(fileName: string): string | null {
  return fileName.match(FILE_POINT_PATTERN)?.[1] || null;
}

export function sortRunDataFiles(files: EuphrosyneFile[]): EuphrosyneFile[] {
  return [...files].sort((left, right) => {
    const priorityDiff = getSortPriority(left) - getSortPriority(right);
    if (priorityDiff !== 0) return priorityDiff;
    return left.name.localeCompare(right.name);
  });
}

export function groupRunDataFiles(
  files: EuphrosyneFile[],
  measuringPointNames: string[],
): GroupedRunDataFiles {
  const knownPointSegments = new Set(
    measuringPointNames
      .map(normalizeMeasuringPointName)
      .filter((name): name is string => name !== null),
  );
  const global: EuphrosyneFile[] = [];
  const byMeasuringPoint: Record<string, EuphrosyneFile[]> = {};

  files.forEach((file) => {
    const segment = parseMeasuringPointSegment(file.name);
    if (segment && knownPointSegments.has(segment)) {
      byMeasuringPoint[segment] = byMeasuringPoint[segment] || [];
      byMeasuringPoint[segment].push(file);
    } else {
      global.push(file);
    }
  });

  Object.entries(byMeasuringPoint).forEach(([point, pointFiles]) => {
    byMeasuringPoint[point] = sortRunDataFiles(pointFiles);
  });

  return {
    global: sortRunDataFiles(global),
    byMeasuringPoint,
  };
}

export function useRunDataFiles({
  projectSlug,
  runLabel,
  isDataAvailable,
  measuringPointNames,
  fetchFn,
}: {
  projectSlug: string;
  runLabel: string;
  isDataAvailable: boolean;
  measuringPointNames: string[];
  fetchFn?: typeof fetch;
}) {
  const [rawFiles, setRawFiles] = useState<EuphrosyneFile[]>([]);
  const [processedFiles, setProcessedFiles] = useState<EuphrosyneFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isDataAvailable) {
      setRawFiles([]);
      setProcessedFiles([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    let ignore = false;
    setIsLoading(true);
    setError(null);

    const rawDataFileService = new RawDataFileService(
      projectSlug,
      runLabel,
      fetchFn,
    );
    const processedDataFileService = new ProcessedDataFileService(
      projectSlug,
      runLabel,
      fetchFn,
    );

    Promise.all([
      rawDataFileService.listData(),
      processedDataFileService.listData(),
    ])
      .then(([raw, processed]) => {
        if (ignore) return;
        setRawFiles(raw);
        setProcessedFiles(processed);
      })
      .catch((fetchError) => {
        if (ignore) return;
        console.error(`Failed to fetch notebook data files: ${fetchError}`);
        setRawFiles([]);
        setProcessedFiles([]);
        setError(window.gettext("Data files could not be loaded."));
      })
      .finally(() => {
        if (!ignore) setIsLoading(false);
      });

    return () => {
      ignore = true;
    };
  }, [projectSlug, runLabel, isDataAvailable, fetchFn]);

  const dataFiles = useMemo(
    () => ({
      raw: groupRunDataFiles(rawFiles, measuringPointNames),
      processed: groupRunDataFiles(processedFiles, measuringPointNames),
    }),
    [rawFiles, processedFiles, measuringPointNames],
  );

  return {
    dataFiles,
    isLoading,
    error,
  };
}
