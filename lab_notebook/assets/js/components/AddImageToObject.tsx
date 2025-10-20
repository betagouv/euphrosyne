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
import { constructImageStorageUrl } from "../utils";
import { getToken } from "../../../../shared/js/jwt";
import { EuphrosyneToolsClientContext } from "../../../../shared/js/EuphrosyneToolsClient.context";
import { css } from "@emotion/react";
import { getExternalImageService } from "../../../../lab/assets/js/external_image/registry";

const baseImageStyle = css({
  objectFit: "contain",
});

const selectedImageStyle = css({
  ...baseImageStyle,
  outline: "3px solid var(--border-active-blue-france)",
});

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
    providerImages: window.interpolate(window.gettext("Images from %s"), [
      objectGroup.externalReference
        ? objectGroup.externalReference.providerName.toUpperCase()
        : "",
    ]),
    noProviderImages: window.interpolate(
      window.gettext("No images found in %s for this object."),
      [objectGroup.externalReference?.providerName.toUpperCase() || ""],
    ),
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
  const [providerImages, setProviderImages] = useState<string[]>([]);

  const [fetchingRunObjectImages, setFetchingRunObjectImages] = useState(true);
  const [fetchingObjectImages, setFetchingObjectImages] = useState(true);
  const [fetchingProviderImages, setFetchingProviderImages] = useState(true);

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

  // FETCH PROVIDER IMAGES

  useEffect(() => {
    if (objectGroup.externalReference) {
      setFetchingProviderImages(true);
      getExternalImageService(objectGroup.externalReference.providerName)
        .getImagesURL(objectGroup.externalReference.providerObjectId)
        .then((images) => {
          if (images) setProviderImages(images);
          setFetchingProviderImages(false);
        });
    }
  }, [objectGroup.externalReference]);

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

      {objectGroup.externalReference && (
        <ObjectImageGallery
          title={t.providerImages}
          images={providerImages.map((url) => ({ url }))}
          selectedImage={selectedObjectImage}
          onImageSelect={onImageSelect}
          loading={fetchingProviderImages}
          noImageText={t.noProviderImages}
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
            css={selectedImage === i ? selectedImageStyle : baseImageStyle}
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
