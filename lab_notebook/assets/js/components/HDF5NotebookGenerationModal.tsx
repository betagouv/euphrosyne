import type { ToolsFetch } from "../../../../shared/js/euphrosyne-tools-client";
import { useHDF5NotebookGenerationWorkflow } from "../hooks/useHDF5NotebookGenerationWorkflow";
import HDF5NotebookGenerationAction from "./HDF5NotebookGenerationAction";
import {
  HDF5NotebookGenerationPreparationPanel,
  HDF5NotebookGenerationProgressPanel,
} from "./HDF5NotebookGenerationPanels";

interface HDF5NotebookGenerationModalProps {
  runId: string;
  projectSlug: string;
  runName: string;
  fetchFn: ToolsFetch;
  canGenerateNotebookFromHDF5: boolean;
  hasHDF5Files: boolean;
  onGenerationComplete: () => Promise<void>;
}

export default function HDF5NotebookGenerationModal({
  runId,
  projectSlug,
  runName,
  fetchFn,
  canGenerateNotebookFromHDF5,
  hasHDF5Files,
  onGenerationComplete,
}: HDF5NotebookGenerationModalProps) {
  const modalId = "hdf5-notebook-generation-modal";
  const workflow = useHDF5NotebookGenerationWorkflow({
    runId,
    projectSlug,
    runName,
    fetchFn,
    hasHDF5Files,
    onGenerationComplete,
  });
  const {
    labels,
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
      <HDF5NotebookGenerationAction
        modalId={modalId}
        labels={labels}
        canGenerateNotebookFromHDF5={canGenerateNotebookFromHDF5}
        hasHDF5Files={hasHDF5Files}
        isDisabled={isDisabled}
        onLoadGenerationMetadata={loadGenerationMetadata}
      />
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
                        <span className="fr-text--bold">
                          {labels.nextStep}
                        </span>{" "}
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
                        skippedGenerationCandidates={skippedGenerationCandidates}
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
