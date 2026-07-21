import type {
  HDF5NotebookGenerationPreview,
  HDF5NotebookGenerationPreviewWarning,
  HDF5NotebookGenerationSkippedCandidate,
} from "../hdf5";
import type {
  CandidateDiscoveryStatus,
  PreflightStatus,
} from "../hooks/useHDF5NotebookGenerationWorkflow";

function formatPreviewWarning(warning: HDF5NotebookGenerationPreviewWarning) {
  const t = {
    missingObjectReference: window.gettext(
      "Point %s has no object reference in HDF5 metadata.",
    ),
    pointLinkedToStandard: window.gettext(
      "Point %s is already linked to a standard; it will not be changed to an object analysis.",
    ),
    differentObject: window.gettext(
      "Point %s is already linked to a different object; it will not be overwritten.",
    ),
    differentComment: window.gettext(
      "Point %s already has a different comment; it will be preserved.",
    ),
    missingStandardReference: window.gettext(
      "Point %s has no standard reference in HDF5 metadata.",
    ),
    pointLinkedToObject: window.gettext(
      "Point %s is already linked to an object; it will not be changed to a standard analysis.",
    ),
    differentStandard: window.gettext(
      "Point %s is already linked to a different standard; it will not be overwritten.",
    ),
    missingStandard: window.gettext(
      "Standard %s does not exist yet; create it and retry generation to attach it.",
    ),
  };

  if (warning.code === "missing-standard") {
    return window.interpolate(t.missingStandard, [
      warning.label || warning.pointName,
    ]);
  }

  const labelByCode: Record<string, string> = {
    "missing-object-reference": t.missingObjectReference,
    "point-linked-to-standard": t.pointLinkedToStandard,
    "different-object": t.differentObject,
    "different-comment": t.differentComment,
    "missing-standard-reference": t.missingStandardReference,
    "point-linked-to-object": t.pointLinkedToObject,
    "different-standard": t.differentStandard,
  };

  return window.interpolate(labelByCode[warning.code], [warning.pointName]);
}

export default function HDF5NotebookGenerationPreparationPanel({
  candidateDiscoveryStatus,
  preflightStatus,
  preview,
  skippedGenerationCandidates,
  fatalError,
}: {
  candidateDiscoveryStatus: CandidateDiscoveryStatus;
  preflightStatus: PreflightStatus;
  preview: HDF5NotebookGenerationPreview | null;
  skippedGenerationCandidates: HDF5NotebookGenerationSkippedCandidate[];
  fatalError: string | null;
}) {
  const t = {
    loadingMetadata: window.gettext("Loading HDF5 metadata for generation..."),
    loadingPreflight: window.gettext("Loading current notebook state..."),
    error: window.gettext(
      "Notebook generation stopped. You can retry after the issue is fixed.",
    ),
    noData: window.gettext("No usable HDF5 metadata detected yet."),
    detectedMetadata: window.gettext("Detected HDF5 metadata"),
    expectedChanges: window.gettext("Expected changes"),
    rulesApplied: window.gettext("Rules applied"),
    hdf5Points: window.gettext("HDF5 points"),
    objectPoints: window.gettext("Object analyses"),
    standardPoints: window.gettext("Standard analyses"),
    skippedEntries: window.gettext("Skipped entries"),
    pointsToCreate: window.gettext("Points to create"),
    existingPointsToReuse: window.gettext("Existing points reused"),
    commentsToFill: window.gettext("Comments to fill"),
    commentsPreserved: window.gettext("Comments preserved"),
    objectsToCreate: window.gettext("Objects to create"),
    objectsReusedOrLinked: window.gettext("Objects reused/linked"),
    standardsToAttachOrReuse: window.gettext("Standards attached/reused"),
    missingStandards: window.gettext("Missing standards"),
    ruleComments: window.gettext("Existing comments are not overwritten."),
    ruleAssignments: window.gettext(
      "Existing object or standard assignments are not replaced if different.",
    ),
    ruleObjects: window.gettext("Existing objects are reused by label."),
    ruleStandards: window.gettext(
      "Standards are matched without case, spaces, hyphens, underscores, or other special characters.",
    ),
    ruleMissingStandards: window.gettext(
      "Missing standards are reported, not created.",
    ),
    ruleRetry: window.gettext("The operation can be retried safely."),
  };

  if (candidateDiscoveryStatus === "idle") {
    return null;
  }

  if (candidateDiscoveryStatus === "loading") {
    return <p className="fr-info-text fr-mt-2w">{t.loadingMetadata}</p>;
  }

  if (candidateDiscoveryStatus === "error") {
    return <p className="fr-error-text fr-mt-2w">{fatalError || t.error}</p>;
  }

  if (preflightStatus === "loading") {
    return (
      <>
        <p className="fr-info-text fr-mt-2w">{t.loadingPreflight}</p>
        <SkippedCandidatesPanel
          skippedGenerationCandidates={skippedGenerationCandidates}
        />
      </>
    );
  }

  if (preflightStatus === "error") {
    return <p className="fr-error-text fr-mt-2w">{fatalError || t.error}</p>;
  }

  if (!preview) {
    return (
      <>
        <p className="fr-warning-text fr-mt-2w">{t.noData}</p>
        <SkippedCandidatesPanel
          skippedGenerationCandidates={skippedGenerationCandidates}
        />
      </>
    );
  }

  const metadataStats: [string, number][] = [
    [t.hdf5Points, preview.metadata.detectedPoints],
    [t.objectPoints, preview.metadata.objectAnalysisPoints],
    [t.standardPoints, preview.metadata.standardAnalysisPoints],
    [t.skippedEntries, preview.metadata.skippedEntries],
  ];
  const changeStats: [string, number][] = [
    [t.pointsToCreate, preview.changes.pointsToCreate],
    [t.existingPointsToReuse, preview.changes.existingPointsToReuse],
    [t.commentsToFill, preview.changes.commentsToFill],
    [t.commentsPreserved, preview.changes.commentsPreserved],
    [t.objectsToCreate, preview.changes.objectsToCreate],
    [t.objectsReusedOrLinked, preview.changes.objectsReusedOrLinked],
    [t.standardsToAttachOrReuse, preview.changes.standardsToAttachOrReuse],
    [t.missingStandards, preview.changes.missingStandards],
  ];

  return (
    <div className="hdf5-generation__preview fr-mt-3w">
      <section className="hdf5-generation__preview-section">
        <p className="fr-text--bold fr-mb-1w">{t.detectedMetadata}</p>
        <StatGrid items={metadataStats} />
      </section>
      {preview.metadata.detectedPoints === 0 ? (
        <p className="fr-warning-text fr-mt-2w">{t.noData}</p>
      ) : (
        <section className="hdf5-generation__preview-section">
          <p className="fr-text--bold fr-mb-1w">{t.expectedChanges}</p>
          <StatGrid items={changeStats} />
        </section>
      )}
      <PreviewWarningsPanel warnings={preview.warnings} />
      <SkippedCandidatesPanel
        skippedGenerationCandidates={skippedGenerationCandidates}
      />
      <section className="hdf5-generation__preview-section">
        <p className="fr-text--bold fr-mb-1w">{t.rulesApplied}</p>
        <ul className="fr-mb-0">
          <li>{t.ruleComments}</li>
          <li>{t.ruleAssignments}</li>
          <li>{t.ruleObjects}</li>
          <li>{t.ruleStandards}</li>
          <li>{t.ruleMissingStandards}</li>
          <li>{t.ruleRetry}</li>
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
}: {
  warnings: HDF5NotebookGenerationPreviewWarning[];
}) {
  const t = {
    noWarnings: window.gettext("No blocking issue detected."),
    warnings: window.gettext("Warnings"),
  };

  if (warnings.length === 0) {
    return (
      <div className="fr-alert fr-alert--success fr-alert--sm fr-mt-2w">
        <p>{t.noWarnings}</p>
      </div>
    );
  }

  return (
    <div className="fr-alert fr-alert--warning fr-alert--sm fr-mt-2w">
      <p>{t.warnings}</p>
      <ul className="hdf5-generation__details-list">
        {warnings.map((warning, index) => (
          <li key={`${warning.code}-${warning.pointName}-${index}`}>
            {formatPreviewWarning(warning)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function SkippedCandidatesPanel({
  skippedGenerationCandidates,
}: {
  skippedGenerationCandidates: HDF5NotebookGenerationSkippedCandidate[];
}) {
  const t = {
    skipped: window.gettext("Skipped HDF5 entries"),
  };

  if (skippedGenerationCandidates.length === 0) {
    return null;
  }

  return (
    <div className="fr-alert fr-alert--info fr-alert--sm fr-mt-2w">
      <p>{t.skipped}</p>
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
