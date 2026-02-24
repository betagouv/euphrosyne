import { LifecycleState } from "../lifecycle-state";

interface ProjectLifecycleNoticeProps {
  lifecycleState: LifecycleState;
  message: string;
}

function shouldDisplayNotice(lifecycleState: LifecycleState): boolean {
  return (
    lifecycleState === "COOLING" ||
    lifecycleState === "RESTORING" ||
    lifecycleState === "ERROR"
  );
}

export default function ProjectLifecycleNotice({
  lifecycleState,
  message,
}: ProjectLifecycleNoticeProps) {
  if (!shouldDisplayNotice(lifecycleState)) {
    return null;
  }

  return (
    <div className="fr-notice fr-notice--info fr-mb-2w">
      <div className="fr-notice__body">
        <p>
          <span className="fr-notice__title">{message}</span>
        </p>
      </div>
    </div>
  );
}
