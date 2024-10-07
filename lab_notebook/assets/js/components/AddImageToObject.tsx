import { useContext, useEffect, useState } from "react";
import type { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import {
  ObjectGroupImageServices,
  RunObjectGroupImageServices,
} from "../notebook-image.services";
import { NotebookContext } from "../Notebook.context";
import {
  IRunObjectImage,
  IImagewithUrl,
  IRunObjectImageWithUrl,
} from "../IImageTransform";
import ImageGrid from "./ImageGrid";
import UploadObjectImage from "./UploadObjectImage";

export default function AddImageToObject({
  runObjectGroup,
  onImageSelect,
  onRunObjectImageSelect,
}: {
  runObjectGroup: RunObjectGroup;
  onImageSelect: (image: IImagewithUrl) => void;
  onRunObjectImageSelect: (image: IRunObjectImageWithUrl) => void;
}) {
  const objectGroup = runObjectGroup.objectGroup;

  const t = {
    objectImagesUsedInRun: window.interpolate(
      "Images of object %s used in this run",
      [objectGroup.label],
    ),
    otherObjectImages: window.interpolate("Other images of object %s", [
      objectGroup.label,
    ]),
    noImage:
      "No image has been upload for this object group / object. You can upload one or import one from the project documents.",
  };

  const { projectSlug } = useContext(NotebookContext);

  const service = new ObjectGroupImageServices(projectSlug, objectGroup.id);

  // Run object images are object images selected previously. Have transform data. Are stored in DB.
  const [runObjectImages, setRunObjectImages] = useState<IRunObjectImage[]>([]);
  // Other images stored in S3-like storage.
  const [objectImages, setObjectImages] = useState<IImagewithUrl[]>([]);

  const [selectedImage, setSelectedImage] = useState<IImagewithUrl | null>();

  const runObjectImageSignedUrls = runObjectImages
    .map((i) => ({
      ...i,
      url: objectImages.find(({ url }) => url.includes(i.path))?.url,
    }))
    .filter((i) => !!i) as IRunObjectImageWithUrl[]; // shouldn't filter any value but just in case

  const _onImageSelect = (image: IImagewithUrl) => {
    setSelectedImage(image);
    onImageSelect(image);
  };

  const _onRunObjectImageSelect = (image: IImagewithUrl) => {
    const runObjectImage = runObjectImageSignedUrls.find((i) =>
      image.url.includes(i.path),
    );
    setSelectedImage(image);
    if (runObjectImage) onRunObjectImageSelect(runObjectImage);
  };

  const onUpload = (url: string) => {
    // Refetch images
    service.listObjectGroupImages().then((images) => {
      setObjectImages(images);
      // Select uploaded image
      setSelectedImage(
        images.find((i) => i.url.split("?")[0] === url.split("?")[0]),
      );
    });
  };

  useEffect(() => {
    service.listObjectGroupImages().then(setObjectImages);
    new RunObjectGroupImageServices(runObjectGroup.id)
      .listRunObjectGroupImages()
      .then(setRunObjectImages);
  }, []);

  return (
    <div>
      <h4 className="fr-mt-4w">{t.objectImagesUsedInRun}</h4>
      <ImageGrid
        images={runObjectImageSignedUrls}
        selectedImage={selectedImage}
        onImageSelect={_onRunObjectImageSelect}
        hideFrom={6}
      />

      <h4 className="fr-mt-4w">{t.otherObjectImages}</h4>
      {objectImages.length === 0 && <p>{t.noImage}</p>}
      <ImageGrid
        images={objectImages}
        selectedImage={selectedImage}
        onImageSelect={_onImageSelect}
        hideFrom={6}
      />

      <UploadObjectImage onUpload={onUpload} service={service} />
    </div>
  );
}
