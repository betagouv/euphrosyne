import { JSX } from "react";
import { createRoot } from "react-dom/client";

export function renderComponent(elementId: string, component: JSX.Element) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(
      `Could not render ${component.type}. Element with id ${elementId} not found.`,
    );
    return;
  }
  const root = createRoot(element);
  root.render(component);
}
