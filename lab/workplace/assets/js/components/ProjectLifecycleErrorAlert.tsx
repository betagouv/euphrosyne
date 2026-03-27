interface ProjectLifecycleErrorAlertProps {
  operationTypeLabel: string;
  errorTitle: string;
  finishedAt: string;
  filesProgress: string;
  bytesProgress: string;
  isSubmittingAction: boolean;
  onRetry: (() => void) | null;
}

export default function ProjectLifecycleErrorAlert({
  operationTypeLabel,
  errorTitle,
  finishedAt,
  filesProgress,
  bytesProgress,
  isSubmittingAction,
  onRetry,
}: ProjectLifecycleErrorAlertProps) {
  const t = {
    "Lifecycle operation failed": window.gettext("Lifecycle operation failed"),
    "Operation type": window.gettext("Operation type"),
    "Error title": window.gettext("Error title"),
    "Finished at": window.gettext("Finished at"),
    "Files copied / total": window.gettext("Files copied / total"),
    "Bytes copied / total": window.gettext("Bytes copied / total"),
    "Retry operation": window.gettext("Retry operation"),
  };

  return (
    <div className="fr-alert fr-alert--error fr-mb-2w">
      <h3 className="fr-alert__title">{t["Lifecycle operation failed"]}</h3>
      <p>
        <strong>{t["Operation type"]}:</strong> {operationTypeLabel}
      </p>
      <p>
        <strong>{t["Error title"]}:</strong> {errorTitle}
      </p>
      <p>
        <strong>{t["Finished at"]}:</strong> {finishedAt}
      </p>
      <p>
        <strong>{t["Files copied / total"]}:</strong> {filesProgress}
      </p>
      <p>
        <strong>{t["Bytes copied / total"]}:</strong> {bytesProgress}
      </p>
      {onRetry && (
        <button
          type="button"
          className="fr-btn fr-btn--secondary"
          disabled={isSubmittingAction}
          onClick={onRetry}
        >
          {t["Retry operation"]}
        </button>
      )}
    </div>
  );
}
