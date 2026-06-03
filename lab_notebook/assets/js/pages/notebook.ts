import { createElement } from "react";
import { renderComponent } from "../../../../euphrosyne/assets/js/react";
import { NotebookRunComments } from "../web-components/notebook-run-comments";
import Notebook from "../components/Notebook";
import { getTemplateJSONData } from "../../../../shared/js/utils";

interface NotebookPageData {
  runId: string;
  projectId: string;
  projectSlug: string;
  runLabel: string;
  isDataAvailable: boolean;
}

NotebookRunComments.init();

document.addEventListener("DOMContentLoaded", () => {
  const notebookPageData =
    getTemplateJSONData<NotebookPageData>("notebook-data");

  if (!notebookPageData) {
    throw new Error("Workplace data not found in workplace-data script tag.");
  }

  const { runId, projectId, projectSlug, runLabel, isDataAvailable } =
    notebookPageData;

  renderComponent(
    "notebook",
    createElement(Notebook, {
      runId,
      projectId,
      projectSlug,
      runLabel,
      isDataAvailable,
    }),
  );
});
