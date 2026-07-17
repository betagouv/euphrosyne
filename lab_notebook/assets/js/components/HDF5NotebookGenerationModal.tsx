import type { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import { useHDF5NotebookGenerationWorkflow } from "../hooks/useHDF5NotebookGenerationWorkflow";
import HDF5NotebookGenerationPreparationPanel from "./HDF5NotebookGenerationPreparationPanel";
import HDF5NotebookGenerationProgressPanel from "./HDF5NotebookGenerationProgressPanel";

interface HDF5NotebookGenerationModalProps {
  runId: string;
  projectSlug: string;
  runName: string;
  fetchFn: ToolsFetch;
  isLabAdmin: boolean;
  canWriteNotebook: boolean;
  hasHDF5Files: boolean;
  onGenerationComplete: () => Promise<void>;
}

export type HDF5NotebookGenerationLabels = ReturnType<
  typeof createHDF5NotebookGenerationLabels
>;

export default function HDF5NotebookGenerationModal({
  runId,
  projectSlug,
  runName,
  fetchFn,
  isLabAdmin,
  canWriteNotebook,
  hasHDF5Files,
  onGenerationComplete,
}: HDF5NotebookGenerationModalProps) {
  const labels = createHDF5NotebookGenerationLabels();
  const modalId = "hdf5-notebook-generation-modal";
  const canGenerateNotebookFromHDF5 = isLabAdmin && canWriteNotebook;
  const workflow = useHDF5NotebookGenerationWorkflow({
    runId,
    projectSlug,
    runName,
    fetchFn,
    hasHDF5Files,
    errorMessage: labels.error,
    onGenerationComplete,
  });
  const {
    modalStep,
    status,
    candidateDiscoveryStatus,
    preflightStatus,
    preview,
    skippedGenerationCandidates,
    progress,
    fatalError,
    canConfirmGeneration,
    isRunning,
    isDisabled,
    loadGenerationMetadata,
    startGeneration,
  } = workflow;
  const nextStepTitle = modalStep === 1 ? labels.generationStep : null;

  if (!canGenerateNotebookFromHDF5) {
    return null;
  }

  return (
    <>
      <div
        className="hdf5-generation"
        title={!hasHDF5Files ? labels.noFiles : undefined}
      >
        <button
          className="fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-magic-line"
          aria-controls={modalId}
          data-fr-opened={false}
          onClick={loadGenerationMetadata}
          disabled={isDisabled}
          title={!hasHDF5Files ? labels.noFiles : undefined}
        >
          {labels.button}
        </button>
      </div>
      <dialog
        aria-labelledby={`${modalId}-title`}
        role="dialog"
        id={modalId}
        className="fr-modal"
      >
        <div className="fr-container fr-container--fluid fr-container-md">
          <div className="fr-grid-row fr-grid-row--center">
            <div className="fr-col-12 fr-col-md-8">
              <div className="fr-modal__body">
                <div className="fr-modal__header">
                  <button
                    className="fr-btn--close fr-btn"
                    title={labels.close}
                    aria-controls={modalId}
                    disabled={isRunning}
                  >
                    {labels.close}
                  </button>
                </div>
                <div className="fr-modal__content">
                  <div className="fr-stepper" id={`${modalId}-title`}>
                    <h1 className="fr-stepper__title">
                      {modalStep === 1
                        ? labels.metadataStep
                        : labels.generationStep}
                      <span className="fr-stepper__state">
                        {window.interpolate(labels.stepCount, [
                          modalStep.toString(),
                          "2",
                        ])}
                      </span>
                    </h1>
                    <div
                      className="fr-stepper__steps"
                      data-fr-current-step={modalStep}
                      data-fr-steps={2}
                    ></div>
                    {nextStepTitle && (
                      <p className="fr-stepper__details">
                        <span className="fr-text--bold">{labels.nextStep}</span>{" "}
                        {nextStepTitle}
                      </p>
                    )}
                  </div>
                  {modalStep === 1 && (
                    <>
                      <p>{labels.warning}</p>
                      <p className="fr-hint-text">{labels.keepOpen}</p>
                      <HDF5NotebookGenerationPreparationPanel
                        candidateDiscoveryStatus={candidateDiscoveryStatus}
                        preflightStatus={preflightStatus}
                        preview={preview}
                        skippedGenerationCandidates={
                          skippedGenerationCandidates
                        }
                        fatalError={fatalError}
                        labels={labels}
                      />
                    </>
                  )}
                  {modalStep === 2 && (
                    <>
                      <p className="fr-hint-text">{labels.keepOpen}</p>
                      <HDF5NotebookGenerationProgressPanel
                        progress={progress}
                        status={status}
                        fatalError={fatalError}
                        labels={labels}
                      />
                    </>
                  )}
                </div>
                <div className="fr-modal__footer">
                  <div className="fr-btns-group fr-btns-group--right fr-btns-group--inline-reverse fr-btns-group--inline-lg">
                    {modalStep === 1 ? (
                      <>
                        <button
                          className="fr-btn"
                          onClick={startGeneration}
                          disabled={!canConfirmGeneration}
                        >
                          {labels.confirm}
                        </button>
                        <button
                          className="fr-btn fr-btn--secondary"
                          aria-controls={modalId}
                        >
                          {labels.cancel}
                        </button>
                      </>
                    ) : (
                      <button
                        className="fr-btn"
                        aria-controls={modalId}
                        disabled={isRunning}
                      >
                        {labels.close}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </dialog>
    </>
  );
}

function createHDF5NotebookGenerationLabels() {
  return {
    button: window.gettext("Generate notebook"),
    cancel: window.gettext("Cancel"),
    close: window.gettext("Close"),
    confirm: window.gettext("Confirm generation"),
    title: window.gettext("Generate notebook from HDF5"),
    stepCount: window.gettext("Step %s of %s"),
    nextStep: window.gettext("Next step:"),
    metadataStep: window.gettext("Prepare generation"),
    generationStep: window.gettext("Generate notebook"),
    warning: window.gettext(
      "The measurement points in this notebook can be created or completed using the HDF5 data available for this run. Existing measurement points may be updated, but duplicate points and objects will not be created. Please review the notebook after generation.",
    ),
    keepOpen: window.gettext(
      "Keep this browser tab open while generation is running.",
    ),
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
    noData: window.gettext("No usable HDF5 metadata detected yet."),
    noFiles: window.gettext("No HDF5 files detected yet."),
    loadingMetadata: window.gettext("Loading HDF5 metadata for generation..."),
    loadingPreflight: window.gettext("Loading current notebook state..."),
    detectedMetadata: window.gettext("Detected HDF5 metadata"),
    expectedChanges: window.gettext("Expected changes"),
    rulesApplied: window.gettext("Rules applied"),
    warnings: window.gettext("Warnings"),
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
    noPreviewWarnings: window.gettext("No blocking issue detected."),
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
    warningMissingObjectReference: window.gettext(
      "Point %s has no object reference in HDF5 metadata.",
    ),
    warningPointLinkedToStandard: window.gettext(
      "Point %s is already linked to a standard; it will not be changed to an object analysis.",
    ),
    warningDifferentObject: window.gettext(
      "Point %s is already linked to a different object; it will not be overwritten.",
    ),
    warningDifferentComment: window.gettext(
      "Point %s already has a different comment; it will be preserved.",
    ),
    warningMissingStandardReference: window.gettext(
      "Point %s has no standard reference in HDF5 metadata.",
    ),
    warningPointLinkedToObject: window.gettext(
      "Point %s is already linked to an object; it will not be changed to a standard analysis.",
    ),
    warningDifferentStandard: window.gettext(
      "Point %s is already linked to a different standard; it will not be overwritten.",
    ),
    warningMissingStandard: window.gettext(
      "Standard %s does not exist yet; create it and retry generation to attach it.",
    ),
  };
}
