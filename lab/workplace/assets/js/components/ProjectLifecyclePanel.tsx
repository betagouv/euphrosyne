import { formatBytes } from "../../../../assets/js/utils";
import {
  LifecycleOperationType,
  LifecycleState,
} from "../lifecycle-state";
import useProjectLifecycle from "../useProjectLifecycle";
import ProjectLifecycleErrorAlert from "./ProjectLifecycleErrorAlert";
import ProjectLifecycleStatus from "./ProjectLifecycleStatus";

interface ProjectLifecyclePanelProps {
  projectId: string;
  projectSlug: string;
  lifecycleState: LifecycleState | null;
  lastLifecycleOperationId: string | null;
  lastLifecycleOperationType: LifecycleOperationType | null;
  onLifecycleStateChange: (state: LifecycleState) => void;
  loadingLabel: string;
}

const PANEL_TEXT = {
  dataAvailability: window.gettext("Data availability"),
  archiveProjectData: window.gettext("Archive project data"),
  restoreProjectData: window.gettext("Restore project data"),
  couldNotUpdateLifecycleState: window.gettext(
    "Could not update lifecycle state.",
  ),
};

function formatDateTime(value: string | null): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.valueOf())) {
    return value;
  }
  return date.toLocaleString();
}

function formatNumber(value: number | null): string {
  if (value === null) {
    return "-";
  }
  return new Intl.NumberFormat().format(value);
}

function formatByteValue(value: number | null): string {
  if (value === null) {
    return "-";
  }
  return formatBytes(value);
}

function formatProgress(
  copied: number | null,
  total: number | null,
  formatter: (value: number | null) => string,
): string {
  if (copied === null && total === null) {
    return "-";
  }
  return `${formatter(copied)} / ${formatter(total)}`;
}

export default function ProjectLifecyclePanel({
  projectId,
  projectSlug,
  lifecycleState,
  lastLifecycleOperationId,
  lastLifecycleOperationType,
  onLifecycleStateChange,
  loadingLabel,
}: ProjectLifecyclePanelProps) {
  const {
    operationDetails,
    operationTypeLabel,
    retryTarget,
    actionError,
    isSubmittingAction,
    performLifecycleAction,
  } = useProjectLifecycle({
    projectId,
    projectSlug,
    lifecycleState,
    lastLifecycleOperationId,
    lastLifecycleOperationType,
    onLifecycleStateChange,
    actionErrorMessage: PANEL_TEXT.couldNotUpdateLifecycleState,
  });

  const retryAction = retryTarget
    ? () =>
        performLifecycleAction(retryTarget.actionType, retryTarget.targetState)
    : null;

  return (
    <section className="fr-mb-3w">
      <h2 className="fr-h5 fr-mb-1w">{PANEL_TEXT.dataAvailability}</h2>
      <ProjectLifecycleStatus
        lifecycleState={lifecycleState}
        loadingLabel={loadingLabel}
      />

      {lifecycleState === "HOT" && (
        <div className="fr-px-1w">
          <button
            type="button"
            className="fr-btn fr-btn--secondary fr-mb-2w"
            disabled={isSubmittingAction}
            onClick={() => performLifecycleAction("COOL", "COOLING")}
          >
            {PANEL_TEXT.archiveProjectData}
          </button>
        </div>
      )}

      {lifecycleState === "COOL" && (
        <div className="fr-px-1w">
          <button
            type="button"
            className="fr-btn fr-btn--secondary fr-mb-2w"
            disabled={isSubmittingAction}
            onClick={() => performLifecycleAction("RESTORE", "RESTORING")}
          >
            {PANEL_TEXT.restoreProjectData}
          </button>
        </div>
      )}

      {lifecycleState === "ERROR" && (
        <ProjectLifecycleErrorAlert
          operationTypeLabel={operationTypeLabel}
          errorTitle={
            operationDetails?.errorTitle || operationDetails?.errorMessage || "-"
          }
          finishedAt={formatDateTime(operationDetails?.finishedAt || null)}
          filesProgress={formatProgress(
            operationDetails?.filesCopied ?? null,
            operationDetails?.filesTotal ?? null,
            formatNumber,
          )}
          bytesProgress={formatProgress(
            operationDetails?.bytesCopied ?? null,
            operationDetails?.bytesTotal ?? null,
            formatByteValue,
          )}
          isSubmittingAction={isSubmittingAction}
          onRetry={retryAction}
        />
      )}

      {actionError && (
        <div className="fr-alert fr-alert--error fr-alert--sm fr-mb-2w">
          <p>{actionError}</p>
        </div>
      )}
    </section>
  );
}
