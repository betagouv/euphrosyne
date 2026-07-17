import type { HDF5NotebookGenerationLabels } from "../hooks/useHDF5NotebookGenerationWorkflow";

interface HDF5NotebookGenerationActionProps {
  modalId: string;
  labels: HDF5NotebookGenerationLabels;
  canGenerateNotebookFromHDF5: boolean;
  hasHDF5Files: boolean;
  isDisabled: boolean;
  onLoadGenerationMetadata: () => void;
}

export default function HDF5NotebookGenerationAction({
  modalId,
  labels,
  canGenerateNotebookFromHDF5,
  hasHDF5Files,
  isDisabled,
  onLoadGenerationMetadata,
}: HDF5NotebookGenerationActionProps) {
  if (!canGenerateNotebookFromHDF5) {
    return null;
  }

  return (
    <div
      className="hdf5-generation"
      title={!hasHDF5Files ? labels.noFiles : undefined}
    >
      <button
        className="fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-magic-line"
        aria-controls={modalId}
        data-fr-opened={false}
        onClick={onLoadGenerationMetadata}
        disabled={isDisabled}
        title={!hasHDF5Files ? labels.noFiles : undefined}
      >
        {labels.button}
      </button>
    </div>
  );
}
