import { createElement } from "react";
import { renderComponent } from "../../../../../euphrosyne/assets/js/react";
import HDF5Viewer from "../components/HDF5Viewer";

document.addEventListener("DOMContentLoaded", async function () {
  renderComponent("root", createElement(HDF5Viewer));
});
