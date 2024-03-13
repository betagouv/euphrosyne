import { createElement } from "react";

import { renderComponent } from "../react";

import UpcomingProjects from "../components/UpcomingProjects";
import AdminCalendar from "../components/AdminCalendar";
import RunningVMTable from "../components/RunningVMTable";

document.addEventListener("DOMContentLoaded", async function () {
  renderComponent("admin-calendar", createElement(AdminCalendar));
  renderComponent("upcoming-projects", createElement(UpcomingProjects));
  renderComponent("running-vms", createElement(RunningVMTable));
});
