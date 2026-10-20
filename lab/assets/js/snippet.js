import { snippet as formsetRowSnippet } from "./snippets/tabular_formset_row.ts";

export function loadFormsetRow(
  formsetPrefix,
  formIndex,
  objectId,
  objectName,
  objectChangeUrl,
  objectRepr,
  parentObjectName,
  parentObjectId,
) {
  let template = formsetRowSnippet;
  const variablesMapping = {
    formsetPrefix,
    formIndex,
    objectId,
    objectName,
    objectChangeUrl,
    objectRepr,
    parentObjectName,
    parentObjectId,
  };
  Object.entries(variablesMapping).forEach(
    ([key, value]) => (template = template.replaceAll(`{{ ${key} }}`, value)),
  );
  const parentTempEl = document.createElement("table");
  parentTempEl.innerHTML = template;
  return parentTempEl.querySelector("tr");
}
