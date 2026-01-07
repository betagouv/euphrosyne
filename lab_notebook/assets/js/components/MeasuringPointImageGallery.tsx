import { useCallback, useContext, useEffect, useState } from "react";
import { NotebookContext } from "../Notebook.context";
import { constructImageStorageUrl } from "../utils";
import { IRunObjectImage } from "../../../../shared/js/images/types";
import { css } from "@emotion/react";
import ImageGrid from "../../../../shared/js/images/ImageGrid";
import CroppedImageDisplay from "./CroppedImageDisplay";
import { getToken } from "../../../../shared/js/jwt";
import { IMeasuringPointImage } from "../../../../shared/js/images/types";
import { RunObjectGroup } from "../../../../lab/objects/assets/js/types";

const modalStyle = css({
  position: "fixed",
  zIndex: 999,
  top: 0,
  left: 0,
  padding: "10rem 13rem",
  backgroundColor: "rgba(0, 0, 0, 0.7)",
});

interface IRunObjectImageWithObjectRef extends IRunObjectImage {
  objectRef: string;
}

export default function MeasuringPointImageGallery({
  runObjectGroups,
}: {
  runObjectGroups: RunObjectGroup[];
}) {
  const t = {
    noImage: window.gettext(
      "There is no image for this run yet. You can add images to the measurement points below, and they will appear here with their corresponding point locations.",
    ),
    helpText: window.gettext("Click on an image to expand it."),
  };

  const { measuringPoints, imageStorage } = useContext(NotebookContext);

  const [euphrosyneToken, setEuphrosyneToken] = useState<string | null>(null);

  const pointImages = measuringPoints
    .map((point) => ({
      image: point.image,
      objectGroupId: point.objectGroupId,
    }))
    .filter((i) => !!i.image);

  const [usedRunObjectImages, setUsedRunObjectImages] = useState<
    IRunObjectImageWithObjectRef[]
  >([]);

  useEffect(() => {
    setUsedRunObjectImages([
      ...new Map(
        pointImages.map((i) => [
          `${(i.image as IMeasuringPointImage).runObjectGroupImage.id} : ${JSON.stringify((i.image as IMeasuringPointImage).runObjectGroupImage.transform)}`,
          {
            ...(i.image as IMeasuringPointImage).runObjectGroupImage,
            objectRef:
              runObjectGroups.find(
                (og) => og.objectGroup.id === i.objectGroupId,
              )?.objectGroup.label || "",
          },
        ]),
      ).values(),
    ]);
  }, [
    pointImages
      .map((i) => (i.image as IMeasuringPointImage).runObjectGroupImage.path)
      .join(","),
    runObjectGroups,
  ]);

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

  const getCroppedImageStyle = useCallback(
    (idx: number) => {
      return css({
        maxWidth: "100%",
        ...(idx === openedImageIndex
          ? {
              maxHeight: "80vh",
              margin: "0 auto",
              display: "block",
            }
          : {}),
      });
    },
    [openedImageIndex],
  );

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
              <p className="fr-text--sm">{image.objectRef}</p>
              <CroppedImageDisplay
                css={getCroppedImageStyle(idx)}
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
