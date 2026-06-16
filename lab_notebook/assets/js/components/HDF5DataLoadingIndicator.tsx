import { css } from "@emotion/react";
import { useEffect, useState } from "react";

import {
  HDF5DataTransferProgressDetail,
  HDF5_DATA_TRANSFER_PROGRESS_EVENT,
} from "../hdf5";
import { formatBytes } from "../../../../lab/assets/js/utils.js";

const loadingStyle = css({
  display: "grid",
  gap: "0.75rem",
  width: "100%",
});

const progressStyle = css({
  width: "100%",
});

export default function HDF5DataLoadingIndicator({
  filePath,
  datasetPath,
  label,
}: {
  filePath: string;
  datasetPath: string;
  label: string;
}) {
  const [progress, setProgress] =
    useState<HDF5DataTransferProgressDetail | null>(null);

  useEffect(() => {
    function onProgress(event: Event) {
      const { detail } = event as CustomEvent<HDF5DataTransferProgressDetail>;
      if (detail.file !== filePath || detail.path !== datasetPath) {
        return;
      }
      setProgress(detail);
    }

    window.addEventListener(HDF5_DATA_TRANSFER_PROGRESS_EVENT, onProgress);
    return () => {
      window.removeEventListener(HDF5_DATA_TRANSFER_PROGRESS_EVENT, onProgress);
    };
  }, [datasetPath, filePath]);

  const loaded = progress?.loaded || 0;
  const total = progress?.total || null;
  const hasKnownTotal = total !== null && total > 0;
  const percentage = hasKnownTotal
    ? Math.min(100, Math.round((loaded / total) * 100))
    : null;

  return (
    <div css={loadingStyle}>
      <p className="fr-m-0">{label}</p>
      <progress
        aria-label={label}
        css={progressStyle}
        max={hasKnownTotal ? 100 : undefined}
        value={percentage ?? undefined}
      />
      {loaded > 0 && (
        <p className="fr-hint-text fr-m-0">
          {hasKnownTotal
            ? window.interpolate(window.gettext("%s of %s loaded"), [
                formatBytes(loaded),
                formatBytes(total),
              ])
            : window.interpolate(window.gettext("%s loaded"), [
                formatBytes(loaded),
              ])}
        </p>
      )}
    </div>
  );
}
