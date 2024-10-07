import { IImageTransform, IImagewithUrl, IRunObjectImage } from "../IImageTransform";
import ImageCropper from "./ImageCropper";

export default function AddMeasuringPointToImage({
  storedImage,
  runObjectImage,
  onTransform,
}: {
  storedImage: IImagewithUrl;
  runObjectImage: IRunObjectImage,
  onTransform?: (data: IImageTransform) => void;
}) {
  return (
    <div>
      <ImageCropper
        src={storedImage.url}
        onCrop={(e) => onTransform && onTransform(e.detail)}
      />
    </div>
  );
}
