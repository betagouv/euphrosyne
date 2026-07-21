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
  const t = {
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
    error: window.gettext(
      "Notebook generation stopped. You can retry after the issue is fixed.",
    ),
    noFiles: window.gettext("No HDF5 files detected yet."),
  };
  const modalId = "hdf5-notebook-generation-modal";
  const canGenerateNotebookFromHDF5 = isLabAdmin && canWriteNotebook;
  const workflow = useHDF5NotebookGenerationWorkflow({
    runId,
    projectSlug,
    runName,
    fetchFn,
    hasHDF5Files,
    errorMessage: t.error,
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
  const nextStepTitle = modalStep === 1 ? t.generationStep : null;

  if (!canGenerateNotebookFromHDF5) {
    return null;
  }

  return (
    <>
      <div
        className="hdf5-generation"
        title={!hasHDF5Files ? t.noFiles : undefined}
      >
        <button
          className="fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-magic-line"
          aria-controls={modalId}
          data-fr-opened={false}
          onClick={loadGenerationMetadata}
          disabled={isDisabled}
          title={!hasHDF5Files ? t.noFiles : undefined}
        >
          {t.button}
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
                    title={t.close}
                    aria-controls={modalId}
                    disabled={isRunning}
                  >
                    {t.close}
                  </button>
                </div>
                <div className="fr-modal__content">
                  <div className="fr-stepper" id={`${modalId}-title`}>
                    <h1 className="fr-stepper__title">
                      {modalStep === 1 ? t.metadataStep : t.generationStep}
                      <span className="fr-stepper__state">
                        {window.interpolate(t.stepCount, [
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
                        <span className="fr-text--bold">{t.nextStep}</span>{" "}
                        {nextStepTitle}
                      </p>
                    )}
                  </div>
                  {modalStep === 1 && (
                    <>
                      <p>{t.warning}</p>
                      <p className="fr-hint-text">{t.keepOpen}</p>
                      <HDF5NotebookGenerationPreparationPanel
                        candidateDiscoveryStatus={candidateDiscoveryStatus}
                        preflightStatus={preflightStatus}
                        preview={preview}
                        skippedGenerationCandidates={
                          skippedGenerationCandidates
                        }
                        fatalError={fatalError}
                      />
                    </>
                  )}
                  {modalStep === 2 && (
                    <>
                      <p className="fr-hint-text">{t.keepOpen}</p>
                      <HDF5NotebookGenerationProgressPanel
                        progress={progress}
                        status={status}
                        fatalError={fatalError}
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
                          {t.confirm}
                        </button>
                        <button
                          className="fr-btn fr-btn--secondary"
                          aria-controls={modalId}
                        >
                          {t.cancel}
                        </button>
                      </>
                    ) : (
                      <button
                        className="fr-btn"
                        aria-controls={modalId}
                        disabled={isRunning}
                      >
                        {t.close}
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
