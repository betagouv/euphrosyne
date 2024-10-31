"use strict";
import { createElement } from "react";

import "@gouvfr/dsfr/dist/component/tab/tab.module.js";

import { renderComponent } from "../../../../../euphrosyne/assets/js/react";
import { getTemplateJSONData } from "../../../../../shared/js/utils";

import VirtualOfficeButton from "../components/virtual-office-button.js";
import VirtualOfficeDeleteButton from "../components/virtual-office-delete-button.js";
import VMSizeSelect from "../components/vm-size-select.js";
import ProjectImageDefinitionSelect from "../components/ProjectImageDefinitionSelect";
import downloadRunData from "../../../../assets/js/run-data-downloader.js";
import WorkplaceRunTabs, {
  WorkplaceRunTabsProps,
} from "../components/WorkplaceRunTabs";
import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";

export type WorkplacePageData = Omit<
  WorkplaceRunTabsProps,
  "rawDataFileService" | "processedDataFileService"
>;

VirtualOfficeButton.init();
VirtualOfficeDeleteButton.init();
VMSizeSelect.init();

document.addEventListener("DOMContentLoaded", () => {
  const workplacePageData =
    getTemplateJSONData<WorkplacePageData>("workplace-data");

  if (!workplacePageData) {
    throw new Error("Workplace data not found in workplace-data script tag.");
  }

  const { project, runs } = workplacePageData;

  renderComponent(
    "workplace-run-tabs",
    createElement(WorkplaceRunTabs, {
      project,
      runs: runs.map((run) => ({
        ...run,
        rawDataFileService: new RawDataFileService(project.slug, run.label),
        processedDataFileService: new ProcessedDataFileService(
          project.slug,
          run.label,
        ),
      })),
    }),
  );

  renderComponent(
    "project-config-image-definitions",
    createElement(ProjectImageDefinitionSelect, { projectSlug: project.slug }),
  );

  document.querySelectorAll(".run-data-download-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      const target = e.target as HTMLElement;
      if (!target?.dataset) {
        console.warn("No dataset property found on run data download button.");
        return;
      }
      downloadRunData(
        project.slug,
        target.dataset.runName,
        target.dataset.runDataType,
      );
    });
  });
});
