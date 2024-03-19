import { css } from "@emotion/react";

import { headerSection } from "./style";

import { Project } from "../../IProject";

interface ProjectLeftContentProps {
  project: Project;
}

const leaderContainerStyle = css({
  display: "flex",
  flexDirection: "column",
  marginLeft: "22px",
});

const statusContainerStyle = css({
  margin: "0 1rem",
});

export default function ProjectLeftContent({
  project,
}: ProjectLeftContentProps) {
  const t = {
    Leader: window.gettext("Leader"),
  };
  return (
    <div css={headerSection}>
      <i className="ri-arrow-right-s-line" aria-hidden="true"></i>
      <h3>{project.name}</h3>
      <div css={statusContainerStyle}>
        <span className={`fr-tag ${project.status.className}`}>
          {project.status.label}
        </span>
      </div>
      <div css={leaderContainerStyle}>
        <span className="fr-text--xs">{t["Leader"]}</span>
        <span className="fr-text--sm">{project.leader}</span>
      </div>
    </div>
  );
}
