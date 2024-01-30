import "./matomo.js";
import { createElement } from "react";

import { renderComponent } from "./react";
import HeaderNav from "./components/header/HeaderNav";
import Header from "./components/header/Header";

import { NavItem } from "./INav";
import { Project } from "./IProject";
import { BackLink } from "./IHeader";

interface NavItemsData {
  currentPath: string;
  items: NavItem[];
}

interface HeaderData {
  project: Project | null;
  backLink: BackLink | null;
}

interface UserData {
  fullName: string;
  isLabAdmin: boolean;
}

function getTemplateJSONData<Type>(elementId: string): Type | null {
  const element = document.querySelector<HTMLScriptElement>(`#${elementId}`);
  if (!element || !element.text) {
    return null;
  }
  try {
    return JSON.parse(element.text);
  } catch (e) {
    return null;
  }
}

function getUserData(): UserData {
  const data = getTemplateJSONData<UserData>("user-data");
  if (!data) {
    return { fullName: window.gettext("User"), isLabAdmin: false };
  }
  return data;
}

function getHeaderData(): HeaderData {
  const data = getTemplateJSONData<HeaderData>("top-header-data");
  if (!data) {
    return { project: null, backLink: null };
  }
  return data;
}

function getNavItemsData(): NavItemsData {
  const data = getTemplateJSONData<NavItemsData>("nav-items-data");
  if (!data) {
    return { currentPath: "", items: [] };
  }
  return data;
}

if (
  window.matchMedia &&
  window.matchMedia("(prefers-color-scheme: dark)").matches
) {
  document.querySelector("html")?.setAttribute("data-fr-theme", "dark");
}

window.addEventListener("DOMContentLoaded", () => {
  const { currentPath, items } = getNavItemsData();
  renderComponent(
    "header-nav",
    createElement(HeaderNav, { currentPath, items })
  );

  const { project, backLink } = getHeaderData();
  const currentUser = getUserData();
  renderComponent(
    "header-main",
    createElement(Header, { project, backLink, currentUser })
  );
});
