import { useCallback, useContext, useEffect, useState } from "react";
import { NotebookContext } from "../Notebook.context";
import { constructImageStorageUrl } from "../utils";
import { IRunObjectImage } from "../IImageTransform";
import { css } from "@emotion/react";
import ImageGrid from "./ImageGrid";
import CroppedImageDisplay from "./CroppedImageDisplay";
import { getToken } from "../../../../shared/js/jwt";

const modalStyle = css({
  position: "fixed",
  zIndex: 999,
  top: 0,
  left: 0,
  padding: "10rem 13rem",
  backgroundColor: "rgba(0, 0, 0, 0.7)",
});

export default function MeasuringPointImageGallery() {
  const t = {
    noImage: window.gettext(
      "There is no image for this run yet. You can add images to the measurement points below, and they will appear here with their corresponding point locations.",
    ),
    helpText: window.gettext("Click on an image to expand it."),
  };

  const { measuringPoints, imageStorage } = useContext(NotebookContext);

  const [euphrosyneToken, setEuphrosyneToken] = useState<string | null>(null);

  const pointImages = measuringPoints
    .map((point) => point.image)
    .filter((i) => !!i);

  const [usedRunObjectImages, setUsedRunObjectImages] = useState<
    IRunObjectImage[]
  >([]);

  useEffect(() => {
    setUsedRunObjectImages([
      ...new Map(
        pointImages.map((i) => [
          `${i.runObjectGroupImage.id} : ${JSON.stringify(i.runObjectGroupImage.transform)}`,
          i.runObjectGroupImage,
        ]),
      ).values(),
    ]);
  }, [pointImages.map((i) => i.runObjectGroupImage.path).join(",")]);

  useEffect(() => {
    getToken().then(setEuphrosyneToken);
  });

  const getPointsForImage = useCallback(
    (image: IRunObjectImage) => {
      return measuringPoints.filter(
        (p) => p.image?.runObjectGroupImage.id === image.id,
      );
    },
    [measuringPoints],
  );

  const [openedImageIndex, setOpenedImageIndex] = useState<number | null>(null);

  const showImage = (idx: number) => {
    document.querySelector(":root")?.setAttribute("data-fr-scrolling", "false");
    setOpenedImageIndex(idx);
  };

  const closeImage = () => {
    document.querySelector(":root")?.removeAttribute("data-fr-scrolling");
    setOpenedImageIndex(null);
  };

  return (
    <div>
      {usedRunObjectImages.length === 0 ? (
        <p>{t.noImage}</p>
      ) : (
        <p>{t.helpText}</p>
      )}
      {imageStorage && euphrosyneToken && (
        <ImageGrid>
          {usedRunObjectImages.map((image, idx) => (
            <div
              key={`${image.path}-${image.id}`}
              onClick={() =>
                openedImageIndex !== null ? closeImage() : showImage(idx)
              }
              css={openedImageIndex === idx && modalStyle}
            >
              <CroppedImageDisplay
                css={{ maxWidth: "100%" }}
                src={constructImageStorageUrl(
                  image.path,
                  imageStorage.baseUrl,
                  imageStorage.token,
                  euphrosyneToken,
                )}
                transform={image.transform}
                measuringPoints={getPointsForImage(image)}
              />
            </div>
          ))}
        </ImageGrid>
      )}
    </div>
  );
}
