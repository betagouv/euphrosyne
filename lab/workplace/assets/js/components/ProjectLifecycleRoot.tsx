import { useEffect, useState } from "react";

import { dispatchLifecycleStateChanged, LifecycleState } from "../lifecycle-state";
import {
  fetchProjectLifecycle,
  ProjectLifecycleSnapshot,
} from "../project-lifecycle-service";
import ProjectLifecycleNoticeBanner from "./ProjectLifecycleNoticeBanner";
import ProjectLifecyclePanel from "./ProjectLifecyclePanel";

interface ProjectLifecycleRootProps {
  projectId: string;
  projectSlug: string;
  title: string;
  loadingLabel: string;
}

export default function ProjectLifecycleRoot({
  projectId,
  projectSlug,
  title,
  loadingLabel,
}: ProjectLifecycleRootProps) {
  const [snapshot, setSnapshot] = useState<ProjectLifecycleSnapshot | null>(null);

  useEffect(() => {
    let cancelled = false;

    void fetchProjectLifecycle(projectSlug)
      .then((nextSnapshot) => {
        if (cancelled) {
          return;
        }
        setSnapshot(nextSnapshot);
        dispatchLifecycleStateChanged(nextSnapshot.lifecycleState);
      })
      .catch((error) => {
        if (!cancelled) {
          console.error(error);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [projectSlug]);

  function handleLifecycleStateChange(nextState: LifecycleState): void {
    setSnapshot((currentSnapshot) => {
      if (!currentSnapshot || currentSnapshot.lifecycleState === nextState) {
        return currentSnapshot;
      }
      return {
        ...currentSnapshot,
        lifecycleState: nextState,
      };
    });
    dispatchLifecycleStateChanged(nextState);
  }

  return (
    <div>
      {snapshot && (
        <ProjectLifecycleNoticeBanner lifecycleState={snapshot.lifecycleState} />
      )}
      <h3>{title}</h3>
      <ProjectLifecyclePanel
        projectId={projectId}
        projectSlug={projectSlug}
        lifecycleState={snapshot?.lifecycleState ?? null}
        lastLifecycleOperationId={snapshot?.lastOperationId ?? null}
        lastLifecycleOperationType={snapshot?.lastOperationType ?? null}
        onLifecycleStateChange={handleLifecycleStateChange}
        loadingLabel={loadingLabel}
      />
    </div>
  );
}
