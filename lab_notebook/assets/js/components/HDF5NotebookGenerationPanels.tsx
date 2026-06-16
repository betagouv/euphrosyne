import type {
  HDF5NotebookGenerationPreview,
  HDF5NotebookGenerationPreviewWarning,
  HDF5NotebookGenerationProgress,
  HDF5NotebookGenerationSkippedCandidate,
} from "../hdf5";
import type { HDF5NotebookGenerationLabels } from "./HDF5NotebookGenerationLabels";

export type GenerationStatus = "idle" | "running" | "success" | "error";
export type CandidateDiscoveryStatus = "idle" | "loading" | "loaded" | "error";
export type PreflightStatus = "idle" | "loading" | "loaded" | "error";

export function HDF5NotebookGenerationProgressPanel({
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

export function HDF5NotebookGenerationPreparationPanel({
  candidateDiscoveryStatus,
  preflightStatus,
  preview,
  skippedGenerationCandidates,
  fatalError,
  labels,
}: {
  candidateDiscoveryStatus: CandidateDiscoveryStatus;
  preflightStatus: PreflightStatus;
  preview: HDF5NotebookGenerationPreview | null;
  skippedGenerationCandidates: HDF5NotebookGenerationSkippedCandidate[];
  fatalError: string | null;
  labels: HDF5NotebookGenerationLabels;
}) {
  if (candidateDiscoveryStatus === "idle") {
    return null;
  }

  if (candidateDiscoveryStatus === "loading") {
    return <p className="fr-info-text fr-mt-2w">{labels.loadingMetadata}</p>;
  }

  if (candidateDiscoveryStatus === "error") {
    return (
      <p className="fr-error-text fr-mt-2w">{fatalError || labels.error}</p>
    );
  }

  if (preflightStatus === "loading") {
    return (
      <>
        <p className="fr-info-text fr-mt-2w">{labels.loadingPreflight}</p>
        <SkippedCandidatesPanel
          skippedGenerationCandidates={skippedGenerationCandidates}
          labels={labels}
        />
      </>
    );
  }

  if (preflightStatus === "error") {
    return (
      <p className="fr-error-text fr-mt-2w">{fatalError || labels.error}</p>
    );
  }

  if (!preview) {
    return (
      <>
        <p className="fr-warning-text fr-mt-2w">{labels.noData}</p>
        <SkippedCandidatesPanel
          skippedGenerationCandidates={skippedGenerationCandidates}
          labels={labels}
        />
      </>
    );
  }

  const metadataStats: [string, number][] = [
    [labels.hdf5Points, preview.metadata.detectedPoints],
    [labels.objectPoints, preview.metadata.objectAnalysisPoints],
    [labels.standardPoints, preview.metadata.standardAnalysisPoints],
    [labels.skippedEntries, preview.metadata.skippedEntries],
  ];
  const changeStats: [string, number][] = [
    [labels.pointsToCreate, preview.changes.pointsToCreate],
    [labels.existingPointsToReuse, preview.changes.existingPointsToReuse],
    [labels.commentsToFill, preview.changes.commentsToFill],
    [labels.commentsPreserved, preview.changes.commentsPreserved],
    [labels.objectsToCreate, preview.changes.objectsToCreate],
    [labels.objectsReusedOrLinked, preview.changes.objectsReusedOrLinked],
    [labels.standardsToAttachOrReuse, preview.changes.standardsToAttachOrReuse],
    [labels.missingStandards, preview.changes.missingStandards],
  ];

  return (
    <div className="hdf5-generation__preview fr-mt-3w">
      <section className="hdf5-generation__preview-section">
        <p className="fr-text--bold fr-mb-1w">{labels.detectedMetadata}</p>
        <StatGrid items={metadataStats} />
      </section>
      {preview.metadata.detectedPoints === 0 ? (
        <p className="fr-warning-text fr-mt-2w">{labels.noData}</p>
      ) : (
        <section className="hdf5-generation__preview-section">
          <p className="fr-text--bold fr-mb-1w">{labels.expectedChanges}</p>
          <StatGrid items={changeStats} />
        </section>
      )}
      <PreviewWarningsPanel warnings={preview.warnings} labels={labels} />
      <SkippedCandidatesPanel
        skippedGenerationCandidates={skippedGenerationCandidates}
        labels={labels}
      />
      <section className="hdf5-generation__preview-section">
        <p className="fr-text--bold fr-mb-1w">{labels.rulesApplied}</p>
        <ul className="fr-mb-0">
          <li>{labels.ruleComments}</li>
          <li>{labels.ruleAssignments}</li>
          <li>{labels.ruleObjects}</li>
          <li>{labels.ruleStandards}</li>
          <li>{labels.ruleMissingStandards}</li>
          <li>{labels.ruleRetry}</li>
        </ul>
      </section>
    </div>
  );
}

function StatGrid({ items }: { items: [string, number][] }) {
  return (
    <dl className="hdf5-generation__preview-grid">
      {items.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function PreviewWarningsPanel({
  warnings,
  labels,
}: {
  warnings: HDF5NotebookGenerationPreviewWarning[];
  labels: HDF5NotebookGenerationLabels;
}) {
  if (warnings.length === 0) {
    return (
      <div className="fr-alert fr-alert--success fr-alert--sm fr-mt-2w">
        <p>{labels.noPreviewWarnings}</p>
      </div>
    );
  }

  return (
    <div className="fr-alert fr-alert--warning fr-alert--sm fr-mt-2w">
      <p>{labels.warnings}</p>
      <ul className="hdf5-generation__details-list">
        {warnings.map((warning, index) => (
          <li key={`${warning.code}-${warning.pointName}-${index}`}>
            {formatPreviewWarning(warning, labels)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function SkippedCandidatesPanel({
  skippedGenerationCandidates,
  labels,
}: {
  skippedGenerationCandidates: HDF5NotebookGenerationSkippedCandidate[];
  labels: HDF5NotebookGenerationLabels;
}) {
  if (skippedGenerationCandidates.length === 0) {
    return null;
  }

  return (
    <div className="fr-alert fr-alert--info fr-alert--sm fr-mt-2w">
      <p>{labels.skipped}</p>
      <ul className="hdf5-generation__details-list">
        {skippedGenerationCandidates.map((candidate) => (
          <li key={candidate.id}>
            {candidate.groupName}: {candidate.reason}
          </li>
        ))}
      </ul>
    </div>
  );
}

function formatPreviewWarning(
  warning: HDF5NotebookGenerationPreviewWarning,
  labels: HDF5NotebookGenerationLabels,
) {
  if (warning.code === "missing-standard") {
    return window.interpolate(labels.warningMissingStandard, [
      warning.label || warning.pointName,
    ]);
  }

  const labelByCode: Record<string, string> = {
    "missing-object-reference": labels.warningMissingObjectReference,
    "point-linked-to-standard": labels.warningPointLinkedToStandard,
    "different-object": labels.warningDifferentObject,
    "different-comment": labels.warningDifferentComment,
    "missing-standard-reference": labels.warningMissingStandardReference,
    "point-linked-to-object": labels.warningPointLinkedToObject,
    "different-standard": labels.warningDifferentStandard,
  };

  return window.interpolate(labelByCode[warning.code], [warning.pointName]);
}
