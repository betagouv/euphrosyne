import { css } from "@emotion/react";

const loadingPlaceholderStyle = css`
  max-width: 150px;
  width: 100%;
  height: 1.25rem;
  background-image: linear-gradient(
    90deg,
    var(--background-default-grey) 0px,
    var(--hairline-color) 40px,
    var(--background-default-grey) 80px
  );
  background-size: 600px;
  animation: 2s shine-lines infinite linear;
  margin: 0 auto;

  @keyframes shine-lines {
    0% {
      background-position: -100px;
    }
    40%,
    100% {
      background-position: 140px;
    }
  }
`;

export default function PlaceholderCard() {
  return (
    <div className="fr-card fr-card--shadow fr-card--horizontal fr-card--sm">
      <div className="fr-card__body">
        <div className="fr-card__content">
          <h3 className="fr-card__title" css={loadingPlaceholderStyle}></h3>
          <p className="fr-card__desc" css={loadingPlaceholderStyle}></p>
          <div className="fr-card__start">
            <ul className="fr-tags-group">
              <li>
                <p className="fr-tag" css={loadingPlaceholderStyle}></p>
              </li>
            </ul>
          </div>
          <div className="fr-card__end">
            <p className="fr-card__detail" css={loadingPlaceholderStyle}></p>
          </div>
        </div>
      </div>
    </div>
  );
}
