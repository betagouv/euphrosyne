"use strict";
import { createElement } from "react";

import "@gouvfr/dsfr/dist/component/tab/tab.module.js";

import { renderComponent } from "../../../../../euphrosyne/assets/js/react";
import { getTemplateJSONData } from "../../../../../shared/js/utils";

import VirtualOfficeButton from "../components/virtual-office-button";
import VirtualOfficeDeleteButton from "../components/virtual-office-delete-button.js";
import VMSizeSelect from "../components/vm-size-select.js";
import ProjectImageDefinitionSelect from "../components/ProjectImageDefinitionSelect";
import downloadRunData from "../../../../assets/js/run-data-downloader.js";
import WorkplaceRunTabs, {
  WorkplaceRunTabsProps,
} from "../components/WorkplaceRunTabs";
import ProjectLifecycleRoot from "../components/ProjectLifecycleRoot";
import { RawDataFileService } from "../raw-data/raw-data-file-service";
import { ProcessedDataFileService } from "../processed-data/processed-data-file-service";
import toolsFetch from "../../../../../shared/js/euphrosyne-tools-client";
import { fetchProjectLifecycle } from "../project-lifecycle-service";
import ProjectLifecycleNoticeBanner from "../components/ProjectLifecycleNoticeBanner";

type WorkplaceRunData = Omit<
  WorkplaceRunTabsProps["runs"][number],
  "rawDataFileService" | "processedDataFileService"
>;

export interface WorkplacePageData {
  project: WorkplaceRunTabsProps["project"];
  runs: WorkplaceRunData[];
  isLabAdmin: boolean;
  isDataManagementEnabled: boolean;
  labels: {
    dataManagementTitle: string;
    loading: string;
  };
}

VirtualOfficeButton.init();
VirtualOfficeDeleteButton.init();
VMSizeSelect.init();

document.addEventListener("DOMContentLoaded", () => {
  const workplacePageData =
    getTemplateJSONData<WorkplacePageData>("workplace-data");

  if (!workplacePageData) {
    throw new Error("Workplace data not found in workplace-data script tag.");
  }

  const { project, runs, isLabAdmin, isDataManagementEnabled, labels } =
    workplacePageData;
  const fetchProjectLifecyclePromise = fetchProjectLifecycle(project.slug);

  renderComponent(
    "workplace-run-tabs",
    createElement(WorkplaceRunTabs, {
      project,
      fetchProjectLifecyclePromise,
      isDataManagementEnabled: isDataManagementEnabled && isLabAdmin,
      runs: runs.map((run) => ({
        ...run,
        rawDataFileService: new RawDataFileService(
          project.slug,
          run.label,
          toolsFetch,
        ),
        processedDataFileService: new ProcessedDataFileService(
          project.slug,
          run.label,
          toolsFetch,
        ),
      })),
    }),
  );

  fetchProjectLifecyclePromise.then((snapshot) => {
    renderComponent(
      "project-lifecycle-banner",
      createElement(ProjectLifecycleNoticeBanner, {
        lifecycleState: snapshot.lifecycleState,
      }),
    );
  });

  if (isLabAdmin && isDataManagementEnabled) {
    renderComponent(
      "project-lifecycle-root",
      createElement(ProjectLifecycleRoot, {
        projectId: String(project.id),
        projectSlug: project.slug,
        title: labels.dataManagementTitle,
        loadingLabel: labels.loading,
        fetchProjectLifecyclePromise,
      }),
    );
  }

  renderComponent(
    "project-config-image-definitions",
    createElement(ProjectImageDefinitionSelect, {
      projectSlug: project.slug,
      fetchFn: toolsFetch,
    }),
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
        toolsFetch,
      );
    });
  });
});
