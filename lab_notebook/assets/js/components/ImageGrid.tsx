import { useState } from "react";
import { IImagewithUrl } from "../IImageTransform";
import ImageWithPlaceholder from "../ImageWithPlaceholder";
import { css } from "@emotion/react";

const selectedImageStyle = css({
  outline: "solid var(--background-action-high-blue-france) 3px",
});

interface IImageGridProps<T extends IImagewithUrl> {
  images: T[];
  selectedImage?: T | null;
  hideFrom?: number;
  onImageSelect?: (image: T) => void;
}

export default function ImageGrid<T extends IImagewithUrl>({
  images,
  selectedImage,
  hideFrom,
  onImageSelect,
}: IImageGridProps<T>) {
  const t = {
    showMore: "Show more",
    showLess: "Show less",
  };
  const [showMore, setShowMore] = useState(false);

  const visibleImages = showMore ? images : images.slice(0, hideFrom);

  const isSelectedImage = (image: T) => {
    return (
      selectedImage &&
      image.url === selectedImage.url &&
      JSON.stringify(image.transform) ===
        JSON.stringify(selectedImage.transform)
    );
  };
  return (
    <div>
      <div className="fr-grid-row fr-grid-row--gutters">
        {visibleImages.map((i) => (
          <div
            className="fr-col-6 fr-col-md-4"
            key={i.url + "-" + JSON.stringify(i.transform)}
          >
            <figure className="fr-content-media fr-my-0" role="group">
              <div
                className="fr-content-media__img"
                css={{
                  ...(isSelectedImage(i) ? selectedImageStyle : {}),
                  position: "relative",
                }}
                onClick={() => onImageSelect && onImageSelect(i)}
              >
                <ImageWithPlaceholder
                  className={`fr-responsive-img fr-ratio-1x1`}
                  src={i.url}
                  transform={i.transform}
                  alt=""
                />
              </div>
            </figure>
          </div>
        ))}
      </div>
      {hideFrom && images.length > hideFrom && (
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
