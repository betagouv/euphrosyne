"use strict";
import { createElement } from "react";

import { getTemplateJSONData } from "../../../../../shared/js/utils";
import { renderComponent } from "../../../../../euphrosyne/assets/js/react";

import DocumentManager from "../components/DocumentManager";

interface ProjectDocumentsPageData {
  project: {
    name: string;
    slug: string;
  };
  table: {
    canDelete: boolean;
  };
  form: {
    hintText: string;
  };
}

window.addEventListener("DOMContentLoaded", () => {
  const projectDocumentsPageData =
    getTemplateJSONData<ProjectDocumentsPageData>("project-documents-data");

  if (!projectDocumentsPageData) {
    throw new Error(
      "Project data not found in project-documents-data script tag.",
    );
  }
  const { project, table, form } = projectDocumentsPageData;

  renderComponent(
    "document-manager",
    createElement(DocumentManager, { project, table, form }),
  );
});
