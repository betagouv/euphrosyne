import { IImageTransform, IImagewithUrl } from "../IImageTransform";
import ImageCropper from "./ImageCropper";

export default function AddImageToObjectTransform({
  image,
  onTransform,
}: {
  image: IImagewithUrl;
  onTransform?: (data: IImageTransform) => void;
}) {
  return (
    <div>
      <ImageCropper
        src={image.url}
        onCrop={(e) => onTransform && onTransform(e.detail)}
      />
    </div>
  );
}
