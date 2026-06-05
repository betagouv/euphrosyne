import { css } from "@emotion/react";

import { ScientificMetadataRow } from "../hdf5";

const metadataTitleStyle = css({
  marginBottom: "0.75rem",
});

const metadataGroupStyle = css({
  borderTop: "1px solid var(--border-default-grey)",
  paddingTop: "0.75rem",
  marginTop: "0.75rem",
});

const metadataListStyle = css({
  display: "grid",
  gap: "0.5rem",
  margin: 0,
});

const metadataRowStyle = css({
  display: "grid",
  gridTemplateColumns: "minmax(5.5rem, 1fr) minmax(0, 1.35fr)",
  gap: "0.5rem",
  fontSize: "0.8125rem",
});

const metadataLabelStyle = css({
  color: "var(--text-mention-grey)",
});

const metadataValueStyle = css({
  margin: 0,
  overflowWrap: "anywhere",
});

export default function HDF5MetadataPanel({
  rows,
}: {
  rows: ScientificMetadataRow[];
}) {
  const groups = getMetadataGroups(rows);
  return (
    <>
      <h2 className="fr-h5" css={metadataTitleStyle}>
        {window.gettext("Metadata")}
      </h2>
      {groups.map((group) => (
        <section key={group.title} css={metadataGroupStyle}>
          <h3 className="fr-h6">{group.title}</h3>
          <dl css={metadataListStyle}>
            {group.rows.map((row) => (
              <div css={metadataRowStyle} key={row.key}>
                <dt css={metadataLabelStyle}>{row.label}</dt>
                <dd css={metadataValueStyle}>{row.value}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </>
  );
}

function getMetadataGroups(rows: ScientificMetadataRow[]): Array<{
  title: string;
  rows: ScientificMetadataRow[];
}> {
  const rowByKey = new Map(rows.map((row) => [row.key, row]));
  const getRows = (keys: string[]) =>
    keys.flatMap((key) => {
      const row = rowByKey.get(key);
      return row ? [row] : [];
    });
  const groups = [
    {
      title: window.gettext("Acquisition"),
      rows: getRows([
        "particle",
        "beamEnergy",
        "targetType",
        "dose",
        "dosePerColumn",
        "timestamp",
        "institution",
        "username",
        "analysisReference",
        "objectReference",
      ]),
    },
    {
      title: window.gettext("Detector"),
      rows: getRows([
        "detector",
        "adcName",
        "detectorType",
        "detectorSerialNumber",
        "calibration",
      ]),
    },
    {
      title: window.gettext("Geometry"),
      rows: getRows([
        "detectorAngle",
        "detectorEntranceWindow",
        "detectorFilter",
        "detectorThickness",
        "detectorActiveArea",
        "shape",
      ]),
    },
    {
      title: window.gettext("File"),
      rows: getRows(["file", "entry", "group"]),
    },
  ];
  return groups.filter((group) => group.rows.length > 0);
}
