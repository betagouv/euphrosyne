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
import ImageLoading from "./ImageLoading";
import ImageWithPlaceholder from "../ImageWithPlaceholder";
import { ProjectImageServices } from "../../../../lab/documents/assets/js/project-image-service";

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
  };

  const { projectSlug } = useContext(NotebookContext);

  const objectGroupImageService = new ObjectGroupImageServices(
    projectSlug,
    objectGroup.id,
  );
  const projectImageService = new ProjectImageServices(projectSlug);
  const runObjectGroupImageService = new RunObjectGroupImageServices(
    runObjectGroup.id,
  );

  const [objectImages, setObjectImages] = useState<IImagewithUrl[] | null>();
  const [runObjectImages, setRunObjectImages] = useState<
    IRunObjectImageWithUrl[] | null
  >();

  const [fetchingRunObjectImages, setFetchingRunObjectImages] = useState(true);
  const [fetchingObjectImages, setFetchingObjectImages] = useState(true);

  const fetchImagesFn = async () => {
    const promises = [
      projectImageService.listProjectImages(),
      runObjectGroupImageService.listRunObjectGroupImages(),
    ];

    const [_projectImagesPromise, _runObjectImagesPromise] =
      await Promise.allSettled(promises);

    let _objectImages: IImagewithUrl[] = [];
    if (_projectImagesPromise.status === "fulfilled") {
      _objectImages = _projectImagesPromise.value as IImagewithUrl[];
    }

    setFetchingObjectImages(false);
    setObjectImages(_objectImages);

    if (_runObjectImagesPromise.status === "fulfilled") {
      const runObjectImagesWithURL = (
        _runObjectImagesPromise.value as IRunObjectImage[]
      )
        .map((i) => {
          return {
            ...i,
            url: _objectImages?.find(({ url }) => url.includes(i.path))?.url,
          };
        })
        .filter((i) => !!i) as IRunObjectImageWithUrl[]; // shouldn't filter any value but just in case;
      setRunObjectImages(runObjectImagesWithURL);
    } else {
      setRunObjectImages([]);
    }
    setFetchingRunObjectImages(false);
  };

  const onUpload = (url: string) => {
    // Refetch images
    projectImageService.listProjectImages().then((images) => {
      setObjectImages(images);
      // Select uploaded image
      const _image = images.find(
        (i) => i.url.split("?")[0] === url.split("?")[0],
      );
      if (_image) onImageSelect(_image);
    });
  };

  useEffect(() => {
    fetchImagesFn();
  }, []);

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
