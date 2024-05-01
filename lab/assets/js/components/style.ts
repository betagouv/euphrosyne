import { css } from "@emotion/react";

export const fileTableRowActionCellBtnStyle = css({
  marginBottom: "0 !important",
});

export const loadingDivStyle = css`
max-width: 150px;
  background-image: linear-gradient(
    90deg,
    var(--background-default-grey) 0px,
    var(--hairline-color) 40px,
    var(--background-default-grey) 80px
  );
  background-size: 600px;
  animation: 2s shine-lines infinite linear;
  border-radius: 4px;
  margin: 0 auto;
}
@keyframes shine-lines {
  0% {
    background-position: -100px;
  }
  40%,
  100% {
    background-position: 140px;
  }`;
