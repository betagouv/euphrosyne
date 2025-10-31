import { createElement } from "react";
import ProjectParticipationsSection from "../participation/components/ProjectParticipationsSection";
import {
  tabClickHandler,
  handleModalClose,
  handleModalConfirm,
} from "../project/tabs.js";
import { renderComponent } from "../../../../euphrosyne/assets/js/react";
import { getTemplateJSONData } from "../../../../shared/js/utils";

interface ProjectPageData {
  projectId: number;
}

document.addEventListener("DOMContentLoaded", () => {
  const projectPageData = getTemplateJSONData<ProjectPageData>(
    "project-changeform-data",
  );

  const form = Array.from(document.forms).filter(
    (f) => f.id == "project_form",
  )[0];
  const otherTabsAnchors = document.querySelectorAll(
    "#runs-tab > a,#documents-tab > a",
  );
  const onCloseModal = document.getElementById("fr-modal-prdformclose");

  const initialFormData = Array.from(new FormData(form));

  otherTabsAnchors.forEach((a) => {
    a.addEventListener("click", (e) =>
      tabClickHandler(
        initialFormData,
        Array.from(new FormData(form)),
        onCloseModal,
        e,
      ),
    );
  });

  onCloseModal
    ?.querySelector('[aria-controls="fr-modal-prdformclose-cancel"]')
    ?.addEventListener("click", () => handleModalClose(onCloseModal));
  onCloseModal
    ?.querySelector('[aria-controls="fr-modal-prdformclose-confirm"]')
    ?.addEventListener("click", () => handleModalConfirm(onCloseModal));

  if (projectPageData && projectPageData.projectId) {
    renderComponent(
      "project-participations-form",
      createElement(ProjectParticipationsSection, {
        projectId: projectPageData.projectId,
      }),
    );
  }
});
