import { useEffect, useState } from "react";

import {
  LIFECYCLE_STATE_CHANGED_EVENT,
  LifecycleState,
  isLifecycleState,
} from "../lifecycle-state";
import ProjectLifecycleNotice from "./ProjectLifecycleNotice";

interface ProjectLifecycleNoticeBannerProps {
  lifecycleState: LifecycleState;
}

export default function ProjectLifecycleNoticeBanner({
  lifecycleState: initialLifecycleState,
}: ProjectLifecycleNoticeBannerProps) {
  const [lifecycleState, setLifecycleState] = useState<LifecycleState>(
    initialLifecycleState,
  );

  useEffect(() => {
    const handler = (event: Event) => {
      const customEvent = event as CustomEvent<unknown>;
      if (isLifecycleState(customEvent.detail)) {
        setLifecycleState(customEvent.detail);
      }
    };

    window.addEventListener(LIFECYCLE_STATE_CHANGED_EVENT, handler);
    return () => {
      window.removeEventListener(LIFECYCLE_STATE_CHANGED_EVENT, handler);
    };
  }, []);

  return (
    <ProjectLifecycleNotice
      lifecycleState={lifecycleState}
      message={window.gettext(
        "Project is currently in Cool storage. Restore to modify.",
      )}
    />
  );
}
