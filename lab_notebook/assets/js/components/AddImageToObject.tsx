import { useContext, useEffect, useState } from "react";
import type { RunObjectGroup } from "../../../../lab/objects/assets/js/types";
import {
  ObjectGroupImageServices,
  RunObjectGroupImageServices,
} from "../notebook-image.services";
import { NotebookContext } from "../Notebook.context";
import { IImagewithUrl, IRunObjectImageWithUrl } from "../IImageTransform";
import ImageGrid from "./ImageGrid";
import UploadObjectImage from "./UploadObjectImage";
import ImageLoading from "./ImageLoading";
import ImageWithPlaceholder from "../ImageWithPlaceholder";
import { ProjectImageServices } from "../../../../lab/documents/assets/js/project-image-service";
import { getImagesURLForObject } from "../../../../lab/assets/js/eros-service";
import { constructImageStorageUrl } from "../utils";
import { getToken } from "../../../../shared/js/jwt";
import { EuphrosyneToolsClientContext } from "../../../../shared/js/EuphrosyneToolsClient.context";

const selectedImageStyle = {
  outline: "3px solid var(--border-active-blue-france)",
};

export default function AddImageToObject({
  runObjectGroup,
  selectedObjectImage,
  selectedRunObjectImage,
  onImageSelect,
  onRunObjectImageSelect,
}: {
  runObjectGroup: RunObjectGroup;
  selectedObjectImage: IImagewithUrl | null;
  selectedRunObjectImage: IRunObjectImageWithUrl | null;
  onImageSelect: (image: IImagewithUrl) => void;
  onRunObjectImageSelect: (image: IRunObjectImageWithUrl) => void;
}) {
  const objectGroup = runObjectGroup.objectGroup;

  const t = {
    objectImagesUsedInRun: window.interpolate(
      window.gettext("Images of object %s used in this run"),
      [objectGroup.label],
    ),
    otherObjectImages: window.gettext("Other images of this project"),
    noObjectImage: window.gettext(
      "No image has been upload for this object group / object. You can upload one or import one from the project documents.",
    ),
    noRunObjectImage: window.gettext(
      "No image has been linked to this object yet. Select an image below or upload one to add one.",
    ),
    erosImages: window.gettext("Images from EROS"),
    noErosImages: window.gettext("No images found in EROS for this object."),
  };

  const { projectSlug, imageStorage } = useContext(NotebookContext);

  const { fetchFn } = useContext(EuphrosyneToolsClientContext);

  const objectGroupImageService = new ObjectGroupImageServices(
    projectSlug,
    objectGroup.id,
    fetchFn,
  );
  const projectImageService = new ProjectImageServices(projectSlug, fetchFn);
  const runObjectGroupImageService = new RunObjectGroupImageServices(
    runObjectGroup.id,
  );

  const [objectImages, setObjectImages] = useState<IImagewithUrl[] | null>();
  const [runObjectImages, setRunObjectImages] = useState<
    IRunObjectImageWithUrl[] | null
  >();
  const [erosImages, setErosImages] = useState<string[]>([]);

  const [fetchingRunObjectImages, setFetchingRunObjectImages] = useState(true);
  const [fetchingObjectImages, setFetchingObjectImages] = useState(true);
  const [fetchingErosImages, setFetchingErosImages] = useState(true);

  const onUpload = (url: string) => {
    // Refetch images
    projectImageService
      .listProjectImages(imageStorage?.token)
      .then((images) => {
        setObjectImages(images);
        // Select uploaded image
        const _image = images.find(
          (i) => i.url.split("?")[0] === url.split("?")[0],
        );
        if (_image) onImageSelect(_image);
      });
  };

  // FETCH PROJECT IMAGES
  useEffect(() => {
    if (!imageStorage) return;
    setFetchingObjectImages(true);
    projectImageService
      .listProjectImages(imageStorage.token)
      .then((images) => {
        setObjectImages(images);
      })
      .finally(() => {
        setFetchingObjectImages(false);
      });
  }, [objectGroup.id, imageStorage]);

  // FETCH RUN OBJECT IMAGES
  useEffect(() => {
    if (imageStorage) {
      const { baseUrl, token } = imageStorage;
      setFetchingRunObjectImages(true);
      runObjectGroupImageService
        .listRunObjectGroupImages()
        .then(async (images) => {
          const euphrosyneToken = await getToken(true);
          setRunObjectImages(
            images.map((i) => ({
              ...i,
              url: constructImageStorageUrl(
                i.path,
                baseUrl,
                token,
                euphrosyneToken,
              ),
            })),
          );
        })
        .finally(() => {
          setFetchingRunObjectImages(false);
        });
    }
  }, [imageStorage, runObjectGroup.id]);

  // FETCH EROS IMAGES
  useEffect(() => {
    if (!objectGroup.c2rmfId && erosImages?.length > 0) setErosImages([]);
    if (objectGroup.c2rmfId) {
      setFetchingErosImages(true);
      getImagesURLForObject(objectGroup.c2rmfId).then((images) => {
        if (images) setErosImages(images);
        setFetchingErosImages(false);
      });
    }
  }, [objectGroup.c2rmfId]);

  return (
    <div>
      <ObjectImageGallery
        title={t.objectImagesUsedInRun}
        images={runObjectImages || []}
        selectedImage={selectedRunObjectImage}
        onImageSelect={onRunObjectImageSelect}
        loading={fetchingRunObjectImages}
        noImageText={t.noRunObjectImage}
      />

      <ObjectImageGallery
        title={t.otherObjectImages}
        images={objectImages || []}
        selectedImage={selectedObjectImage}
        onImageSelect={onImageSelect}
        loading={fetchingObjectImages}
        noImageText={t.noObjectImage}
      />

      {objectGroup.c2rmfId && (
        <ObjectImageGallery
          title={t.erosImages}
          images={erosImages.map((url) => ({ url }))}
          selectedImage={selectedObjectImage}
          onImageSelect={onImageSelect}
          loading={fetchingErosImages}
          noImageText={t.noErosImages}
        />
      )}

      <UploadObjectImage
        onUpload={onUpload}
        service={objectGroupImageService}
      />
    </div>
  );
}

interface IObjectImageGalleryProps<T extends IImagewithUrl> {
  title: string;
  noImageText?: string;
  images: T[];
  selectedImage?: T | null;
  loading?: boolean;
  onImageSelect: (image: T) => void;
}

function ObjectImageGallery<T extends IImagewithUrl>({
  title,
  images,
  loading = false,
  noImageText,
  selectedImage,
  onImageSelect,
}: IObjectImageGalleryProps<T>) {
  return (
    <div>
      <h4 className="fr-mt-4w">{title}</h4>
      {loading && <LoadingIndicator />}
      {!loading && images.length === 0 && noImageText && <p>{noImageText}</p>}
      <ImageGrid
        onImageSelect={(index) => onImageSelect(images[index])}
        hideFrom={6}
      >
        {images.map((i) => (
          <ImageWithPlaceholder
            src={i.url}
            transform={i.transform}
            alt=""
            key={i.url + "-" + JSON.stringify(i.transform)}
            css={selectedImage === i ? selectedImageStyle : undefined}
          />
        ))}
      </ImageGrid>
    </div>
  );
}

function LoadingIndicator() {
  const t = {
    imagesLoading: "Fetching images...",
  };
  return (
    <div css={{ display: "flex", alignItems: "center" }}>
      <ImageLoading css={{ width: "40px" }} /> {t.imagesLoading}
    </div>
  );
}
