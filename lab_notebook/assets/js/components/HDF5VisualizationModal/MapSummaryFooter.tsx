import { ScientificMetadataRow } from "../../hdf5";
import { summaryFooterStyle, summaryItemStyle } from "./styles";

export function MapSummaryFooter({
  channels,
  columns,
  metadataRows,
  rows,
}: {
  channels: number;
  columns: number;
  metadataRows: ScientificMetadataRow[];
  rows: number;
}) {
  const metadataByKey = new Map(
    metadataRows.map((row) => [row.key, row.value]),
  );
  const mapSizeX = metadataByKey.get("mapSizeX");
  const mapSizeY = metadataByKey.get("mapSizeY");
  const pixelSizeX = metadataByKey.get("pixelSizeX");
  const pixelSizeY = metadataByKey.get("pixelSizeY");

  return (
    <div css={summaryFooterStyle}>
      <span css={summaryItemStyle}>
        {window.gettext("Map size")} : {rows} × {columns}{" "}
        {window.gettext("pixels")}
      </span>
      {mapSizeX && mapSizeY && (
        <span css={summaryItemStyle}>
          {window.gettext("Physical size")} : {mapSizeX} × {mapSizeY}
        </span>
      )}
      {pixelSizeX && pixelSizeY && (
        <span css={summaryItemStyle}>
          {window.gettext("Pixel")} : {pixelSizeX} × {pixelSizeY}
        </span>
      )}
      <span css={summaryItemStyle}>
        {window.gettext("Channels")} : {channels}
      </span>
    </div>
  );
}
