import { createElement } from "react";
import ProjectParticipationsSection from "../participation/components/ProjectParticipationsSection";
import {
  tabClickHandler,
  handleModalClose,
  handleModalConfirm,
} from "../project/tabs.js";
import { renderComponent } from "../../../../euphrosyne/assets/js/react";
import { getTemplateJSONData } from "../../../../shared/js/utils";
import { getUserData } from "../../../../euphrosyne/assets/js/main";

interface ProjectPageData {
  projectId: number | null;
  participationEmployerFormExemptRorIds: string[];
}

interface TypeAheadResultClickEvent extends Event {
  detail: {
    result: {
      id: string;
    };
  };
}

function initProjectCreationEmployerExemption(projectPageData: ProjectPageData) {
  const exemptRorIds = projectPageData.participationEmployerFormExemptRorIds || [];
  if (!exemptRorIds.length) {
    return;
  }

  const rorInput = document.getElementById(
    "id_institution__ror_id",
  ) as HTMLInputElement | null;
  const employerInputs = [
    "id_employer_first_name",
    "id_employer_last_name",
    "id_employer_email",
    "id_employer_function",
  ]
    .map((id) => document.getElementById(id) as HTMLInputElement | null)
    .filter((input): input is HTMLInputElement => input !== null);

  if (!rorInput || employerInputs.length === 0) {
    return;
  }

  const institutionField = rorInput.closest(".field-institution");
  const firstEmployerRow = employerInputs[0].closest(".form-row");
  const infoMessage = document.createElement("p");
  infoMessage.className = "fr-message fr-message--info";
  infoMessage.textContent = window.gettext(
    "Employer information is not required for the selected institution.",
  );
  infoMessage.hidden = true;
  infoMessage.style.display = "none";
  firstEmployerRow?.parentNode?.insertBefore(infoMessage, firstEmployerRow);

  const updateEmployerFields = (rorId = rorInput.value) => {
    const isExempt = !!rorId && exemptRorIds.includes(rorId);
    infoMessage.hidden = !isExempt;
    infoMessage.style.display = isExempt ? "" : "none";
    employerInputs.forEach((input) => {
      input.disabled = isExempt;
      input.required = !isExempt;
      if (isExempt) {
        input.value = "";
      }
    });
  };

  institutionField
    ?.querySelector("div[is='institution-type-ahead']")
    ?.addEventListener("result-click", (event) => {
      updateEmployerFields((event as TypeAheadResultClickEvent).detail.result.id);
    });
  const onInstitutionManualInput = () => {
    rorInput.value = "";
    updateEmployerFields();
  };
  document
    .getElementById("id_institution__name")
    ?.addEventListener("input", onInstitutionManualInput);
  document
    .getElementById("id_institution__country")
    ?.addEventListener("input", onInstitutionManualInput);

  updateEmployerFields();
}

document.addEventListener("DOMContentLoaded", () => {
  const projectPageData = getTemplateJSONData<ProjectPageData>(
    "project-changeform-data",
  );
  const featureFlags =
    getTemplateJSONData<Record<string, boolean>>("feature-flags") || {};

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

  if (projectPageData && !projectPageData.projectId) {
    initProjectCreationEmployerExemption(projectPageData);
  }

  if (projectPageData && projectPageData.projectId) {
    const userData = getUserData();
    const employerFormExemptRorIds =
      projectPageData.participationEmployerFormExemptRorIds || [];
    renderComponent(
      "project-participations-form",
      createElement(ProjectParticipationsSection, {
        projectId: projectPageData.projectId,
        userData,
        isRadiationProtectionEnabled:
          featureFlags.radiation_protection ?? false,
        employerFormExemptRorIds,
      }),
    );
  }
});
