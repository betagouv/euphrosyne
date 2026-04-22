import { LifecycleState } from "../lifecycle-state";

interface ProjectLifecycleStatusProps {
  lifecycleState: LifecycleState | null;
  loadingLabel: string;
}

const BADGE_CLASS_BY_STATE: Record<LifecycleState, string> = {
  HOT: "fr-badge fr-badge--success fr-badge--no-icon",
  COOLING: "fr-badge fr-badge--info fr-badge--no-icon",
  COOL: "fr-badge fr-badge--no-icon",
  RESTORING: "fr-badge fr-badge--info fr-badge--no-icon",
  ERROR: "fr-badge fr-badge--error fr-badge--no-icon",
};

const BADGE_LABEL_BY_STATE: Record<LifecycleState, string> = {
  HOT: window.gettext("available"),
  COOL: window.gettext("archived"),
  COOLING: window.gettext("archiving"),
  RESTORING: window.gettext("restoring"),
  ERROR: window.gettext("error"),
};

const AVAILABILITY_DESCRIPTION_BY_STATE: Record<LifecycleState, string> = {
  HOT: window.gettext(
    "Project data is available and can be accessed from the virtual workstation.",
  ),
  COOL: window.gettext(
    "Project data is archived in cold storage and is not currently accessible. Restore the data to make it available again.",
  ),
  COOLING: window.gettext(
    "Project data is currently being archived to cold storage. Some operations may be temporarily unavailable during this process.",
  ),
  RESTORING: window.gettext(
    "Archived project data is currently being restored. The data will become available once the restoration is complete.",
  ),
  ERROR: window.gettext(
    "An error occurred while processing the project data. You can retry the operation.",
  ),
};

export default function ProjectLifecycleStatus({
  lifecycleState,
  loadingLabel,
}: ProjectLifecycleStatusProps) {
  return (
    <div className="fr-mb-2w">
      {lifecycleState ? (
        <>
          <p>
            <span className={BADGE_CLASS_BY_STATE[lifecycleState]}>
              {BADGE_LABEL_BY_STATE[lifecycleState]}
            </span>
          </p>
          <p>{AVAILABILITY_DESCRIPTION_BY_STATE[lifecycleState]}</p>
        </>
      ) : (
        <p>
          <span className="fr-badge fr-badge--info fr-badge--no-icon">
            {loadingLabel}
          </span>
        </p>
      )}
    </div>
  );
}
