import "./matomo.js";
if (
  window.matchMedia &&
  window.matchMedia("(prefers-color-scheme: dark)").matches
) {
  document.querySelector("html")?.setAttribute("data-fr-theme", "dark");
}
