import { useEffect, useState, useRef } from "react";

import { Run, RunObjectGroup, ObjectGroup } from "../types";

import ObjectGroupTable from "./ObjectGroupTable";
import RunObjectGroupProjectImportModal from "./RunObjectGroupProjectImportModal";
import {
  deleteRunObjectGroup,
  addObjectGroupToRun,
  fetchAvailableObjectGroups,
  fetchRunObjectGroups,
} from "../services";

interface RunObjectGroupFormProps {
  run: Run;
  popupObjectGroupEventTarget: EventTarget;
}

export default function RunObjectGroupForm({
  run,
  popupObjectGroupEventTarget,
}: RunObjectGroupFormProps) {
  const t = {
    "Add new object group or object": window.gettext(
      "Add new object group or object",
    ),
    "Import object from same project": window.gettext(
      "Import object from same project",
    ),
    "Import with EROS ID": window.gettext("Import with EROS ID"),
    "Import with POP Reference": window.gettext("Import with POP Reference"),
    "An error occurred.": window.gettext("An error occurred."),
    "POP is disabled but will be available soon.": window.gettext(
      "POP is disabled but will be available soon.",
    ),
  };

  const [runObjectGroups, setRunObjectGroups] = useState<RunObjectGroup[]>([]);
  const [availableObjectGroups, setAvailableObjectGroups] = useState<
    ObjectGroup[]
  >([]);
  const [addObjectGroupError, setAddObjectGroupError] = useState<string | null>(
    null,
  );
  const openModalBtnRef = useRef<HTMLButtonElement>(null);

  const importFromProjectModalId = "run-object-group-project-import";

  const onRunObjectGroupDelete = async (runObjectGroupId: string) => {
    const response = await deleteRunObjectGroup(runObjectGroupId);
    if (response && response.ok) {
      setRunObjectGroups(
        runObjectGroups.filter((ro) => ro.id !== runObjectGroupId),
      );
      fetchAvailableObjectGroups(run.id).then(setAvailableObjectGroups);
    }
  };

  const onAddObjectGroupToRun = (objectGroupId: string) => {
    addObjectGroupToRun(run.id, objectGroupId).then(async (response) => {
      if (response?.ok) {
        // Remove error message if any
        if (addObjectGroupError) setAddObjectGroupError(null);
        // Refetch run object groups
        fetchRunObjectGroups(run.id).then((runObjectGroups) => {
          setRunObjectGroups(runObjectGroups);
        });
        if (openModalBtnRef.current) {
          // Close the modal
          openModalBtnRef.current.dataset.frOpened = "false";
        }
        // Refetch available object groups
        setAvailableObjectGroups(
          availableObjectGroups.filter((og) => og.id !== objectGroupId),
        );
      } else {
        // Show error on select in modal
        setAddObjectGroupError(t["An error occurred."]);
      }
    });
  };

  popupObjectGroupEventTarget.addEventListener("objectGroupAdded", () => {
    fetchRunObjectGroups(run.id).then(setRunObjectGroups);
  });

  useEffect(() => {
    fetchRunObjectGroups(run.id).then(setRunObjectGroups);
    fetchAvailableObjectGroups(run.id).then(setAvailableObjectGroups);
  }, []);

  return (
    <div>
      <div>
        <ul className="fr-btns-group fr-btns-group--sm fr-btns-group--icon-left fr-btns-group--inline fr-ml-0">
          <li>
            <a
              href={`/lab/objectgroup/add/?_to_field=id&_popup=1&run=${run.id}`}
              className="related-widget-wrapper-link fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-add-circle-line"
              data-popup="yes"
            >
              {t["Add new object group or object"]}
            </a>
          </li>
          <li>
            <button
              className="fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-refresh-line"
              id={`${importFromProjectModalId}-btn`}
              data-fr-opened="false"
              aria-controls={importFromProjectModalId}
              type="button"
              ref={openModalBtnRef}
            >
              {t["Import object from same project"]}
            </button>
          </li>
          <li>
            <a
              href={`/lab/objectgroup/eros_import?_to_field=id&_popup=1&run=${run.id}`}
              className="related-widget-wrapper-link fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-download-line"
              data-popup="yes"
            >
              {t["Import with EROS ID"]}
            </a>
          </li>
          <li>
            <a
              className="related-widget-wrapper-link fr-btn fr-btn--secondary fr-btn--icon-left fr-icon-download-line"
              data-popup="yes"
              role="link"
              aria-disabled="true"
              aria-describedby="object-import-pop-tooltip"
            >
              {t["Import with POP Reference"]}
            </a>
            <span
              className="fr-tooltip fr-placement"
              id="object-import-pop-tooltip"
              role="tooltip"
            >
              {t["POP is disabled but will be available soon."]}
            </span>
          </li>
        </ul>
      </div>
      <ObjectGroupTable
        runObjectGroups={runObjectGroups}
        onRowDelete={onRunObjectGroupDelete}
        runId={run.id}
      />
      <RunObjectGroupProjectImportModal
        id={importFromProjectModalId}
        availableObjectGroups={availableObjectGroups}
        onAdd={onAddObjectGroupToRun}
        error={addObjectGroupError}
      />
    </div>
  );
}
