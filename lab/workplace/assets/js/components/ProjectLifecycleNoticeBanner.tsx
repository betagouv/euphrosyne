import { LifecycleState } from "../lifecycle-state";
import ProjectLifecycleNotice from "./ProjectLifecycleNotice";

interface ProjectLifecycleNoticeBannerProps {
  lifecycleState: LifecycleState;
}

export default function ProjectLifecycleNoticeBanner({
  lifecycleState,
}: ProjectLifecycleNoticeBannerProps) {
  return <ProjectLifecycleNotice lifecycleState={lifecycleState} />;
}
