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
  const t = {
    mapSize: window.gettext("Map size"),
    pixels: window.gettext("pixels"),
    physicalSize: window.gettext("Physical size"),
    pixel: window.gettext("Pixel"),
    channels: window.gettext("Channels"),
  };

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
        {t.mapSize} : {rows} × {columns} {t.pixels}
      </span>
      {mapSizeX && mapSizeY && (
        <span css={summaryItemStyle}>
          {t.physicalSize} : {mapSizeX} × {mapSizeY}
        </span>
      )}
      {pixelSizeX && pixelSizeY && (
        <span css={summaryItemStyle}>
          {t.pixel} : {pixelSizeX} × {pixelSizeY}
        </span>
      )}
      <span css={summaryItemStyle}>
        {t.channels} : {channels}
      </span>
    </div>
  );
}
