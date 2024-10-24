import {
  PropsWithChildren,
  useState,
  Children,
  cloneElement,
  isValidElement,
  ReactElement,
} from "react";
import { css } from "@emotion/react";

const selectedImageStyle = css({
  outline: "solid var(--background-action-high-blue-france) 3px",
});

interface IImageGridProps {
  hideFrom?: number;
  onImageSelect?: (index: number) => void;
}

export default function ImageGrid({
  hideFrom,
  onImageSelect,
  children,
}: PropsWithChildren<IImageGridProps>) {
  const t = {
    showMore: "Show more",
    showLess: "Show less",
  };
  const [showMore, setShowMore] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>();

  const visibleImages = Children.map(children, (child) =>
    isValidElement(child) ? (
      cloneElement(child as ReactElement, {
        className: "fr-responsive-img fr-ratio-1x1",
      })
    ) : (
      <></>
    ),
  )?.slice(0, showMore ? undefined : hideFrom);

  const isSelectedImage = (index: number) => {
    return selectedIndex && selectedIndex === index;
  };
  return (
    <div>
      <div className="fr-grid-row fr-grid-row--gutters">
        {Children.map(visibleImages, (node, index) => (
          <div
            className="fr-col-12 fr-col-sm-6 fr-col-md-4"
            key={node?.toString() + `_${index}`}
          >
            <figure className="fr-content-media fr-my-0" role="group">
              <div
                className="fr-content-media__img"
                css={{
                  ...(isSelectedImage(index) ? selectedImageStyle : {}),
                  position: "relative",
                }}
                onClick={() => {
                  if (onImageSelect) {
                    setSelectedIndex(index);
                    onImageSelect && onImageSelect(index);
                  }
                }}
              >
                {node}
              </div>
            </figure>
          </div>
        ))}
      </div>
      {hideFrom && Children.toArray(children).length > hideFrom && (
        <div className="fr-mt-1w" css={{ textAlign: "center" }}>
          <button
            className={`fr-btn fr-btn--tertiary-no-outline fr-btn--lg  ${showMore ? "fr-icon-arrow-up-s-line" : "fr-icon-arrow-down-s-line"}`}
            title={showMore ? t.showLess : t.showMore}
            onClick={() => setShowMore(!showMore)}
          >
            {showMore ? t.showLess : t.showMore}
          </button>
        </div>
      )}
    </div>
  );
}
