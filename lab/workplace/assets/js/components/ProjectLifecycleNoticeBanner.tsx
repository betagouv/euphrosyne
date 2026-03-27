import { useEffect, useState } from "react";
import { LifecycleState, onLifecycleStateChanged } from "../lifecycle-state";

interface ProjectLifecycleNoticeBannerProps {
  lifecycleState: LifecycleState;
}

type NoticeClass = "info" | "alert" | "warning";
type NoticeClassMapping = {
  [key in LifecycleState]: NoticeClass;
};

const noticeClasses: NoticeClassMapping = {
  HOT: "info",
  COOLING: "warning",
  COOL: "info",
  RESTORING: "warning",
  ERROR: "alert",
};

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
    return window.gettext(
      "Project is currently archived. Contact an administrator to restore it.",
    );
  }
  if (lifecycleState === "COOLING") {
    return window.gettext("Project data is currently being archived.");
  }
  if (lifecycleState === "RESTORING") {
    return window.gettext("Project data is currently being restored.");
  }
  if (lifecycleState === "ERROR") {
    return window.gettext(
      "An error occurred while processing project data. Contact an administrator to fix the issue.",
    );
  }
  return "";
}

export default function ProjectLifecycleNoticeBanner({
  lifecycleState,
}: ProjectLifecycleNoticeBannerProps) {
  const [_lifecycleState, _setLifecycleState] = useState(lifecycleState);

  useEffect(() => {
    return onLifecycleStateChanged(_setLifecycleState);
  }, []);

  if (!shouldDisplayNotice(_lifecycleState)) {
    return null;
  }

  return (
    <div
      className={`fr-notice fr-notice--${noticeClasses[_lifecycleState]} fr-mb-2w`}
    >
      <div className="fr-notice__body">
        <p>
          <span className="fr-notice__title">
            {getNoticeMessage(_lifecycleState)}
          </span>
        </p>
      </div>
    </div>
  );
}
