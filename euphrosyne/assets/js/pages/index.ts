import { createElement } from "react";

import { renderComponent } from "../react";

import UpcomingProjects from "../components/UpcomingProjects";
import AdminCalendar from "../components/AdminCalendar";

document.addEventListener("DOMContentLoaded", async function () {
  renderComponent("admin-calendar", createElement(AdminCalendar));
  renderComponent("upcoming-projects", createElement(UpcomingProjects));
});
