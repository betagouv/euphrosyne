import { css } from "@emotion/react";

export const visualizationLayoutStyle = css({
  display: "grid",
  gridTemplateColumns: "minmax(15rem, 18rem) minmax(0, 1fr)",
  border: "1px solid var(--border-default-grey)",
  borderRadius: "0.5rem",
  overflow: "hidden",
  "@media (max-width: 62rem)": {
    gridTemplateColumns: "1fr",
  },
});

export const metadataPanelStyle = css({
  borderRight: "1px solid var(--border-default-grey)",
  padding: "1rem 1.25rem",
  background: "var(--background-alt-grey)",
  "@media (max-width: 62rem)": {
    borderRight: "none",
    borderBottom: "1px solid var(--border-default-grey)",
  },
});

export const rangeControlsStyle = css({
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gap: "0.5rem",
  marginTop: "0.75rem",
  "@media (max-width: 36rem)": {
    gridTemplateColumns: "1fr",
  },
});

export const mapPanelStyle = css({
  display: "flex",
  flexDirection: "column",
  gap: "1rem",
  minWidth: 0,
  padding: "1rem 1.25rem",
});

export const spectrumPanelStyle = css({
  minWidth: 0,
  padding: "1rem 1.25rem",
});

export const visualizationLoadingStyle = css({
  alignItems: "center",
  display: "flex",
  minHeight: "24rem",
});

export const spectrumLoadingStyle = css({
  alignItems: "center",
  display: "flex",
  minHeight: "28rem",
});

export const spectrumAreaStyle = css({
  display: "grid",
  gridTemplateColumns: "minmax(34rem, 1fr) minmax(14rem, 17rem)",
  gap: "1rem",
  alignItems: "stretch",
  "@media (max-width: 78rem)": {
    gridTemplateColumns: "1fr",
  },
});

export const sectionStyle = css({
  minWidth: 0,
});

export const sectionTitleStyle = css({
  alignItems: "center",
  display: "flex",
  gap: "0.5rem",
  marginBottom: "0.5rem",
});

export const rangeCardStyle = css({
  alignSelf: "start",
  border: "1px solid var(--border-default-grey)",
  borderRadius: "0.5rem",
  padding: "1rem",
});

export const rangeFieldsetStyle = css({
  display: "grid",
  gap: "0.5rem",
  margin: 0,
  minWidth: 0,
});

export const rangeHintStyle = css({
  gridColumn: "1 / -1",
  margin: 0,
});

export const rangeActionRowStyle = css({
  display: "flex",
  gridColumn: "1 / -1",
  marginTop: "0.25rem",
  width: "100%",
});

export const rangeButtonStyle = css({
  justifyContent: "center",
  width: "100%",
});

export const helpCardStyle = css({
  background: "var(--background-alt-blue-france)",
  border: "1px solid var(--border-default-blue-france)",
  borderRadius: "0.5rem",
  color: "var(--text-default-grey)",
  fontSize: "0.875rem",
  lineHeight: 1.5,
  marginTop: "0.5rem",
  padding: "0.75rem",
});

export const mapSectionStyle = css({
  borderTop: "1px solid var(--border-default-grey)",
  paddingTop: "1rem",
});

export const globalSpectrumPlotStyle = css({
  height: "clamp(18rem, 32vh, 25rem)",
  minHeight: "18rem",
  width: "100%",
});

export const spectrumPlotStyle = css({
  minHeight: "28rem",
  height: "62vh",
});

export const mapStyle = css({
  height: "clamp(30rem, 52vh, 44rem)",
  minHeight: "30rem",
  width: "100%",
});

export const summaryFooterStyle = css({
  alignItems: "center",
  border: "1px solid var(--border-default-grey)",
  borderRadius: "0.25rem",
  display: "flex",
  flexWrap: "wrap",
  gap: "0.5rem 1rem",
  padding: "0.5rem 0.75rem",
});

export const summaryItemStyle = css({
  color: "var(--text-mention-grey)",
  fontSize: "0.875rem",
  whiteSpace: "nowrap",
});
