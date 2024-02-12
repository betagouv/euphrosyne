import { css } from "@emotion/react";

import { BackLink } from "../../IHeader";
import { Project } from "../../IProject";
import Translate from "./Translate";
import HeaderLeftContent from "./HeaderLeftContent";
import { getCSRFToken } from "../../../../../lab/assets/js/utils";

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
    <div className="fr-header__body">
      <div className="fr-container">
        <div className="fr-header__body-row">
          <div className="fr-header__brand">
            <div className="fr-header__brand-top">
              <HeaderLeftContent backLink={backLink} project={project} />
              <div className="fr-header__navbar">
                <button
                  className="fr-btn--menu fr-btn"
                  data-fr-opened="false"
                  aria-controls="header-modal"
                  aria-haspopup="menu"
                  id="header-modal-btn"
                  title={window.gettext("Menu")}
                >
                  {window.gettext("Menu")}
                </button>
              </div>
            </div>
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
                  className="fr-displayed-lg"
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
                  <form method="post" action="/logout/?next=/login">
                    <button
                      className="fr-btn"
                      css={errorTextStyle}
                      type="submit"
                    >
                      <span>{window.gettext("Log out")}</span>
                      <input
                        type="hidden"
                        name="csrfmiddlewaretoken"
                        value={getCSRFToken() || ""}
                      />
                    </button>
                  </form>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
