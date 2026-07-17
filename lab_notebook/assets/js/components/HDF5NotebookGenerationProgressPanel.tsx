import type { HDF5NotebookGenerationProgress } from "../hdf5";
import type { GenerationStatus } from "../hooks/useHDF5NotebookGenerationWorkflow";
import type { HDF5NotebookGenerationLabels } from "./HDF5NotebookGenerationModal";

export default function HDF5NotebookGenerationProgressPanel({
  progress,
  status,
  fatalError,
  labels,
}: {
  progress: HDF5NotebookGenerationProgress | null;
  status: GenerationStatus;
  fatalError: string | null;
  labels: HDF5NotebookGenerationLabels;
}) {
  if (!progress && !fatalError && status !== "running") {
    return null;
  }

  const alertClass =
    status === "error"
      ? "fr-alert fr-alert--error"
      : status === "success"
        ? "fr-alert fr-alert--success"
        : "fr-alert fr-alert--info";

  return (
    <div className={`${alertClass} fr-mt-2w`}>
      <p>
        {status === "idle"
          ? labels.skipped
          : status === "success"
            ? labels.success
            : status === "error"
              ? labels.error
              : labels.started}
      </p>
      {progress && (
        <dl className="hdf5-generation__progress">
          <div>
            <dt>{labels.detectedPoints}</dt>
            <dd>{progress.detectedPoints}</dd>
          </div>
          <div>
            <dt>{labels.currentPoint}</dt>
            <dd>{progress.currentPointName || "-"}</dd>
          </div>
          <div>
            <dt>{labels.pointsCreated}</dt>
            <dd>{progress.pointsCreated}</dd>
          </div>
          <div>
            <dt>{labels.pointsUpdated}</dt>
            <dd>{progress.pointsUpdated}</dd>
          </div>
          <div>
            <dt>{labels.objectsCreated}</dt>
            <dd>{progress.objectsCreated}</dd>
          </div>
          <div>
            <dt>{labels.objectsReused}</dt>
            <dd>{progress.objectsReused}</dd>
          </div>
          <div>
            <dt>{labels.standardsReused}</dt>
            <dd>{progress.standardsReused}</dd>
          </div>
        </dl>
      )}
      {progress && progress.errors.length > 0 && (
        <>
          <p className="fr-mt-2w">{labels.errors}</p>
          <ul>
            {progress.errors.map((error, index) => (
              <li key={`${index}-${error}`}>{error}</li>
            ))}
          </ul>
        </>
      )}
      {!progress && fatalError && (
        <>
          <p className="fr-mt-2w">{labels.errors}</p>
          <ul>
            <li>{fatalError}</li>
          </ul>
        </>
      )}
    </div>
  );
}
