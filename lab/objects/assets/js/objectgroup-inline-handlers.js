import { loadFormsetRow } from "../../../assets/js/snippet.js";

export function dismissAddRelatedObjectGroupPopup(
  win,
  newId,
  newRepr,
  objectGroupRunRunIds
) {
  const pageRunId = parseInt(
    document.getElementById("id_Run_run_object_groups-__prefix__-run").value
  );
  const [relatedObjectGroupRunRunIds] = objectGroupRunRunIds.filter(
    ([, runId]) => pageRunId === runId
  );
  if (!relatedObjectGroupRunRunIds) {
    window.dismissAddRelatedObjectPopup(win, newId, newRepr);
    return;
  }

  const name = win.name.replace(new RegExp("__[0-9]$"), ""),
    elem = document.getElementById(name),
    [formIndex] = elem.id.split("-").slice("-2");

  const newRow = loadFormsetRow(
    "Run_run_object_groups",
    formIndex,
    relatedObjectGroupRunRunIds[0],
    "objectgroup",
    `/admin/lab/objectgroup/${newId}/change/?next=/admin/lab/run/${pageRunId}/change/&_popup=1`,
    newRepr,
    "run",
    pageRunId
  );

  elem.closest("tr").replaceWith(newRow);

  const intialFormsInput = document.querySelector(
    "input[name='Run_run_object_groups-INITIAL_FORMS']"
  );
  intialFormsInput.value = parseInt(intialFormsInput.value) + 1;

  win.close();
}
