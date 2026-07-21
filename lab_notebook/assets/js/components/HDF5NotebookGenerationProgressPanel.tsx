import type { HDF5NotebookGenerationProgress } from "../hdf5";
import type { GenerationStatus } from "../hooks/useHDF5NotebookGenerationWorkflow";

export default function HDF5NotebookGenerationProgressPanel({
  progress,
  status,
  fatalError,
}: {
  progress: HDF5NotebookGenerationProgress | null;
  status: GenerationStatus;
  fatalError: string | null;
}) {
  const t = {
    started: window.gettext("Generation started."),
    success: window.gettext("Notebook generation completed."),
    error: window.gettext(
      "Notebook generation stopped. You can retry after the issue is fixed.",
    ),
    detectedPoints: window.gettext("Detected points"),
    currentPoint: window.gettext("Current point"),
    pointsCreated: window.gettext("Points created"),
    pointsUpdated: window.gettext("Points updated/completed"),
    objectsCreated: window.gettext("Objects created"),
    objectsReused: window.gettext("Objects reused"),
    standardsReused: window.gettext("Standards reused"),
    errors: window.gettext("Errors"),
    skipped: window.gettext("Skipped HDF5 entries"),
  };

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
          ? t.skipped
          : status === "success"
            ? t.success
            : status === "error"
              ? t.error
              : t.started}
      </p>
      {progress && (
        <dl className="hdf5-generation__progress">
          <div>
            <dt>{t.detectedPoints}</dt>
            <dd>{progress.detectedPoints}</dd>
          </div>
          <div>
            <dt>{t.currentPoint}</dt>
            <dd>{progress.currentPointName || "-"}</dd>
          </div>
          <div>
            <dt>{t.pointsCreated}</dt>
            <dd>{progress.pointsCreated}</dd>
          </div>
          <div>
            <dt>{t.pointsUpdated}</dt>
            <dd>{progress.pointsUpdated}</dd>
          </div>
          <div>
            <dt>{t.objectsCreated}</dt>
            <dd>{progress.objectsCreated}</dd>
          </div>
          <div>
            <dt>{t.objectsReused}</dt>
            <dd>{progress.objectsReused}</dd>
          </div>
          <div>
            <dt>{t.standardsReused}</dt>
            <dd>{progress.standardsReused}</dd>
          </div>
        </dl>
      )}
      {progress && progress.errors.length > 0 && (
        <>
          <p className="fr-mt-2w">{t.errors}</p>
          <ul>
            {progress.errors.map((error, index) => (
              <li key={`${index}-${error}`}>{error}</li>
            ))}
          </ul>
        </>
      )}
      {!progress && fatalError && (
        <>
          <p className="fr-mt-2w">{t.errors}</p>
          <ul>
            <li>{fatalError}</li>
          </ul>
        </>
      )}
    </div>
  );
}
