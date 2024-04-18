import { css } from "@emotion/react";

import ProjectLeftContent from "./ProjectLeftContent";
import { headerSection } from "./style";

import { BackLink } from "../../IHeader";
import { Project } from "../../IProject";

interface HeaderLeftContentProps {
  backLink: BackLink | null;
  project: Project | null;
}

const flexStyle = css({
  display: "flex",
});

export default function HeaderLeftContent({
  backLink,
  project,
}: HeaderLeftContentProps) {
  return (
    <div css={flexStyle}>
      {backLink && (
        <div css={headerSection} className="fr-mr-1w">
          <a href={backLink.href}>
            <i className="ri-arrow-left-line fr-mr-1w" aria-hidden="true"></i>
            <span className="fr-text--md">{backLink.title}</span>
          </a>
        </div>
      )}
      {project && <ProjectLeftContent project={project} />}{" "}
      {!project && !backLink && <h3>Euphrosyne</h3>}
    </div>
  );
}
