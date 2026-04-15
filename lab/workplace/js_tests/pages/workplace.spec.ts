import { beforeEach, describe, expect, it, vi } from "vitest";

const { renderComponent, downloadRunData, fetchProjectLifecycle } = vi.hoisted(() => ({
  renderComponent: vi.fn(),
  downloadRunData: vi.fn(),
  fetchProjectLifecycle: vi.fn(),
}));

vi.mock("../../../../euphrosyne/assets/js/react", () => ({
  renderComponent,
}));

vi.mock("@gouvfr/dsfr/dist/component/tab/tab.module.js", () => ({}));

vi.mock("../../assets/js/components/virtual-office-button", () => ({
  default: class VirtualOfficeButton {
    static init() {}
  },
}));

vi.mock("../../assets/js/components/virtual-office-delete-button.js", () => ({
  default: class VirtualOfficeDeleteButton {
    static init() {}
  },
}));

vi.mock("../../assets/js/components/vm-size-select.js", () => ({
  default: class VMSizeSelect {
    static init() {}
  },
}));

vi.mock("../../assets/js/components/ProjectImageDefinitionSelect", () => ({
  default: function ProjectImageDefinitionSelect() {
    return null;
  },
}));

vi.mock("../../assets/js/components/WorkplaceRunTabs", () => ({
  default: function WorkplaceRunTabs() {
    return null;
  },
}));

vi.mock("../../assets/js/components/ProjectLifecycleRoot", () => ({
  default: function ProjectLifecycleRoot() {
    return null;
  },
}));

vi.mock("../../assets/js/components/ProjectLifecycleNoticeBanner", () => ({
  default: function ProjectLifecycleNoticeBanner() {
    return null;
  },
}));

vi.mock("../../assets/js/project-lifecycle-service", async () => {
  const actual = await vi.importActual<
    typeof import("../../assets/js/project-lifecycle-service")
  >("../../assets/js/project-lifecycle-service");
  return {
    ...actual,
    fetchProjectLifecycle,
  };
});

vi.mock("../../../../assets/js/run-data-downloader.js", () => ({
  default: downloadRunData,
}));

import "../../assets/js/pages/workplace";

function renderIds(): string[] {
  return renderComponent.mock.calls.map(([elementId]) => elementId);
}

function renderPropsFor(elementId: string): Record<string, unknown> {
  const call = renderComponent.mock.calls.find(([id]) => id === elementId);
  if (!call) {
    throw new Error(`Missing render call for ${elementId}`);
  }
  return call[1].props as Record<string, unknown>;
}

function setupWorkplaceDom(data: unknown): void {
  document.body.innerHTML = `
    <div id="project-lifecycle-banner"></div>
    <div id="project-lifecycle-root"></div>
    <div id="workplace-run-tabs"></div>
    <div id="project-config-image-definitions"></div>
    <script id="workplace-data" type="application/json">${JSON.stringify(
      data,
    )}</script>
  `;
}

describe("workplace page", () => {
  beforeEach(() => {
    renderComponent.mockReset();
    downloadRunData.mockReset();
    fetchProjectLifecycle.mockReset();
    document.body.innerHTML = "";
  });

  async function flushAsyncWork(): Promise<void> {
    await Promise.resolve();
    await Promise.resolve();
  }

  it("renders the member banner from the lifecycle API", async () => {
    fetchProjectLifecycle.mockResolvedValue({
      lifecycleState: "COOL",
      lastOperationId: null,
      lastOperationType: null,
    });
    setupWorkplaceDom({
      project: {
        id: 42,
        name: "Project",
        slug: "project-slug",
      },
      runs: [],
      isLabAdmin: false,
      isDataManagementEnabled: true,
      labels: {
        dataManagementTitle: "Data management",
        loading: "Loading",
      },
    });

    document.dispatchEvent(new Event("DOMContentLoaded"));
    await flushAsyncWork();

    expect(fetchProjectLifecycle).toHaveBeenCalledWith("project-slug");
    expect(renderIds()).toContain("project-lifecycle-banner");
    expect(renderIds()).not.toContain("project-lifecycle-root");
    expect(renderPropsFor("project-lifecycle-banner")).toMatchObject({
      lifecycleState: "COOL",
    });
    const runTabsProps = renderPropsFor("workplace-run-tabs");
    expect(runTabsProps.isDataManagementEnabled).toBe(false);
    expect(runTabsProps.fetchProjectLifecyclePromise).toBeInstanceOf(Promise);
  });

  it("shares the lifecycle fetch promise with admin components", async () => {
    fetchProjectLifecycle.mockResolvedValue({
      lifecycleState: "ERROR",
      lastOperationId: "op-1",
      lastOperationType: "RESTORE",
    });
    setupWorkplaceDom({
      project: {
        id: 42,
        name: "Project",
        slug: "project-slug",
      },
      runs: [],
      isLabAdmin: true,
      isDataManagementEnabled: true,
      labels: {
        dataManagementTitle: "Data management",
        loading: "Loading",
      },
    });

    document.dispatchEvent(new Event("DOMContentLoaded"));
    const runTabsPromise = renderPropsFor("workplace-run-tabs")
      .fetchProjectLifecyclePromise as Promise<unknown>;
    const rootPromise = renderPropsFor("project-lifecycle-root")
      .fetchProjectLifecyclePromise as Promise<unknown>;

    expect(fetchProjectLifecycle).toHaveBeenCalledWith("project-slug");
    expect(runTabsPromise).toBe(rootPromise);
  });

  it("uses the hot fallback when the lifecycle endpoint is unavailable", async () => {
    fetchProjectLifecycle.mockResolvedValue({
      lifecycleState: "HOT",
      lastOperationId: null,
      lastOperationType: null,
    });
    setupWorkplaceDom({
      project: {
        id: 42,
        name: "Project",
        slug: "project-slug",
      },
      runs: [],
      isLabAdmin: true,
      isDataManagementEnabled: false,
      labels: {
        dataManagementTitle: "Data management",
        loading: "Loading",
      },
    });

    document.dispatchEvent(new Event("DOMContentLoaded"));
    await flushAsyncWork();

    expect(renderPropsFor("project-lifecycle-banner")).toMatchObject({
      lifecycleState: "HOT",
    });
  });
});
