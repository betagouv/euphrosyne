import { css } from "@emotion/react";

import { BackLink } from "../../IHeader";
import { Project } from "../../IProject";
import Translate from "./Translate";
import HeaderLeftContent from "./HeaderLeftContent";

interface User {
  fullName: string;
  isLabAdmin: boolean;
}

interface HeaderProps {
  backLink: BackLink | null;
  project: Project | null;
  currentUser: User;
}

const errorTextStyle = css`
  color: var(--text-default-error) !important;
`;

export default function Header({
  backLink,
  project,
  currentUser,
}: HeaderProps) {
  return (
    <>
      <div className="fr-header__body">
        <div className="fr-container">
          <div className="fr-header__body-row">
            <div>
              <HeaderLeftContent backLink={backLink} project={project} />
            </div>
            <div className="fr-header__tools">
              <div className="fr-header__tools-links">
                <ul className="fr-btns-group">
                  <li>
                    <Translate />
                  </li>
                  <li
                    css={css`
                      flex-direction: column;
                      margin-left: 8px;
                    `}
                  >
                    <p>{currentUser.fullName}</p>
                    {currentUser.isLabAdmin && (
                      <>
                        <br />
                        <p className="fr-text--sm">{window.gettext("Admin")}</p>
                      </>
                    )}
                  </li>
                  <li>
                    <a className="fr-btn" href="/logout" css={errorTextStyle}>
                      <span>{window.gettext("Log out")}</span>
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="fr-header__menu fr-modal" id="header-modal">
        <div className="fr-container">
          <button
            className="fr-btn--close fr-btn"
            aria-controls="header-modal"
            title={window.gettext("Close")}
          >
            {window.gettext("Close")}
          </button>
          <div className="fr-header__menu-links"></div>
        </div>
      </div>
    </>
  );
}
