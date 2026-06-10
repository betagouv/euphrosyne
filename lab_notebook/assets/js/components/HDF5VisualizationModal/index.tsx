import { Suspense, useEffect, useMemo } from "react";
import { H5GroveProvider } from "@witoldw/h5web-app";

import { createToolsH5GroveFetcher, HDF5DatasetEntry } from "../../hdf5";
import { ToolsFetch } from "../../../../../shared/js/euphrosyne-tools-client";
import { HDF5VisualizationContent } from "./HDF5VisualizationContent";
import { HDF5VisualizationErrorBoundary } from "./HDF5VisualizationErrorBoundary";
import { getVisualizationModalTitle } from "./metadata";
import { modalContainerStyle, modalContentStyle } from "./styles";

export default function HDF5VisualizationModal({
  modalId,
  entry,
  fetchFn,
  onClose,
}: {
  modalId: string;
  entry: HDF5DatasetEntry | null;
  fetchFn: ToolsFetch;
  onClose: () => void;
}) {
  const t = {
    close: window.gettext("Close"),
    loading: window.gettext("Loading visualization..."),
  };

  const fetcher = useMemo(() => createToolsH5GroveFetcher(fetchFn), [fetchFn]);

  useEffect(() => {
    if (!entry) {
      return;
    }
    const modalElement = document.getElementById(modalId);
    if (modalElement && window.dsfr) {
      window.dsfr(modalElement).modal.disclose();
    }
  }, [entry, modalId]);

  return (
    <dialog
      aria-labelledby={`${modalId}-title`}
      role="dialog"
      id={modalId}
      className="fr-modal"
    >
      <div
        className="fr-container fr-container--fluid fr-container-md"
        css={modalContainerStyle}
      >
        <div className="fr-modal__body">
          <div className="fr-modal__header">
            <button
              className="fr-btn--close fr-btn"
              aria-controls={modalId}
              type="button"
              onClick={onClose}
            >
              {t.close}
            </button>
          </div>
          <div className="fr-modal__content" css={modalContentStyle}>
            <h1 id={`${modalId}-title`} className="fr-modal__title">
              {entry ? getVisualizationModalTitle(entry) : t.loading}
            </h1>
            {entry && (
              <H5GroveProvider
                url="/hdf5"
                filepath={entry.filePath}
                fetcher={fetcher}
                getExportURL={() => undefined}
              >
                <HDF5VisualizationErrorBoundary key={entry.id}>
                  <Suspense fallback={<p>{t.loading}</p>}>
                    <HDF5VisualizationContent entry={entry} />
                  </Suspense>
                </HDF5VisualizationErrorBoundary>
              </H5GroveProvider>
            )}
          </div>
        </div>
      </div>
    </dialog>
  );
}
