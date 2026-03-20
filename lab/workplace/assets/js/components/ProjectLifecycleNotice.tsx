import { LifecycleState } from "../lifecycle-state";

interface ProjectLifecycleNoticeProps {
  lifecycleState: LifecycleState;
}

function shouldDisplayNotice(lifecycleState: LifecycleState): boolean {
  return (
    lifecycleState === "COOL" ||
    lifecycleState === "COOLING" ||
    lifecycleState === "RESTORING" ||
    lifecycleState === "ERROR"
  );
}

function getNoticeMessage(lifecycleState: LifecycleState): string {
  if (lifecycleState === "COOL") {
    return window.gettext("Project is currently archived. Restore to modify.");
  }
  if (lifecycleState === "COOLING") {
    return window.gettext("Project data is currently being archived.");
  }
  if (lifecycleState === "RESTORING") {
    return window.gettext("Project data is currently being restored.");
  }
  if (lifecycleState === "ERROR") {
    return window.gettext(
      "An error occurred while processing project data. You can retry the operation.",
    );
  }
  return "";
}

export default function ProjectLifecycleNotice({
  lifecycleState,
}: ProjectLifecycleNoticeProps) {
  if (!shouldDisplayNotice(lifecycleState)) {
    return null;
  }

  if (lifecycleState === "ERROR") {
    return (
      <div className="fr-notice fr-notice--error fr-mb-2w">
        <div className="fr-notice__body">
          <p>
            <span className="fr-notice__title">
              {getNoticeMessage(lifecycleState)}
            </span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="fr-notice fr-notice--info fr-mb-2w">
      <div className="fr-notice__body">
        <p>
          <span className="fr-notice__title">
            {getNoticeMessage(lifecycleState)}
          </span>
        </p>
      </div>
    </div>
  );
}
