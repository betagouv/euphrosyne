import { useMemo } from "react";
import FileTable, { Col } from "../../../../lab/assets/js/components/FileTable";
import { EuphrosyneFile } from "../../../../lab/assets/js/file-service";
import { formatBytes } from "../../../../lab/assets/js/utils";
import { RawDataFileService } from "../../../../lab/workplace/assets/js/raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../../../../lab/workplace/assets/js/processed-data/processed-data-file-service";
import NotebookDataFilesActionCell from "./NotebookDataFilesActionCell";

const tableCols: Col<EuphrosyneFile>[] = [
  { label: window.gettext("File"), key: "name" },
  {
    label: window.gettext("Last modified"),
    key: "lastModified",
    formatter: (value: string | null) =>
      value ? new Date(value).toLocaleDateString() : "",
  },
  {
    label: window.gettext("Size"),
    key: "size",
    formatter: (value: string | null) =>
      value ? formatBytes(parseInt(value)) : "",
  },
];

export default function NotebookDataFilesSection({
  title,
  rawFiles,
  processedFiles,
  projectId,
  projectSlug,
  runLabel,
  fetchFn,
  isLoading = false,
  error = null,
}: {
  title: string;
  rawFiles: EuphrosyneFile[];
  processedFiles: EuphrosyneFile[];
  projectId: string;
  projectSlug: string;
  runLabel: string;
  fetchFn?: typeof fetch;
  isLoading?: boolean;
  error?: string | null;
}) {
  const t = {
    "Raw data": window.gettext("Raw data"),
    "Processed data": window.gettext("Processed data"),
    "Data files are loading.": window.gettext("Data files are loading."),
  };

  const rawDataFileService = useMemo(
    () => new RawDataFileService(projectSlug, runLabel, fetchFn),
    [projectSlug, runLabel, fetchFn],
  );
  const processedDataFileService = useMemo(
    () => new ProcessedDataFileService(projectSlug, runLabel, fetchFn),
    [projectSlug, runLabel, fetchFn],
  );

  if (
    !isLoading &&
    !error &&
    rawFiles.length === 0 &&
    processedFiles.length === 0
  ) {
    return null;
  }

  return (
    <section className="fr-mt-4w">
      <h4>{title}</h4>
      {isLoading && (
        <div className="fr-alert fr-alert--info fr-alert--sm fr-mb-2w">
          <p>{t["Data files are loading."]}</p>
        </div>
      )}
      {error && (
        <div className="fr-alert fr-alert--error fr-alert--sm fr-mb-2w">
          <p>{error}</p>
        </div>
      )}
      {rawFiles.length > 0 && (
        <>
          <h5>{t["Raw data"]}</h5>
          <FileTable
            rows={rawFiles}
            cols={tableCols}
            actionCell={
              <NotebookDataFilesActionCell
                projectId={projectId}
                fileService={rawDataFileService}
              />
            }
          />
        </>
      )}
      {processedFiles.length > 0 && (
        <>
          <h5>{t["Processed data"]}</h5>
          <FileTable
            rows={processedFiles}
            cols={tableCols}
            actionCell={
              <NotebookDataFilesActionCell
                projectId={projectId}
                fileService={processedDataFileService}
              />
            }
          />
        </>
      )}
    </section>
  );
}
